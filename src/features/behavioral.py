"""Past-only behavioral features. One card/timestamp batch commits atomically."""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.data.split import stable_split_hash

ROOT = Path(__file__).resolve().parents[2]
FEATURES = ['txn_count_1h','txn_count_24h','txn_count_7d','hist_amt_mean','hist_amt_std','amt_ratio','txn_recency','is_new_merchant','is_new_category','hour_deviation']
EXPECTED_HASH = 'aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8'
WINDOWS = (3600_000_000_000, 86400_000_000_000, 604800_000_000_000)


def build_behavioral_features(transactions, split_manifest, config=None):
    config = config or {}
    cols = ['trans_num', 'cc_num', 'timestamp', 'amt', 'merchant', 'category']
    df = transactions.loc[:, cols].copy()
    if df[['trans_num','cc_num','timestamp','amt']].isna().any().any() or df.trans_num.duplicated().any():
        raise ValueError('null required field or duplicate transaction ID')
    if not config.get('allow_null_categories', False) and df[['merchant','category']].isna().any().any():
        raise ValueError('null merchant/category violates production schema')
    if not all(df[c].dropna().map(lambda x: isinstance(x, str)).all() for c in ['trans_num','cc_num','merchant','category']):
        raise ValueError('identifier and category fields must be strings')
    if not pd.api.types.is_datetime64_ns_dtype(df.timestamp.dtype) or df.timestamp.dt.tz is not None:
        raise ValueError('timestamp must be timezone-naive datetime64[ns]')
    if not np.isfinite(df.amt.to_numpy(dtype=float)).all():
        raise ValueError('amount must be finite')
    m = split_manifest[['trans_num','split']].copy()
    if m.isna().any().any() or m.trans_num.duplicated().any() or not set(m.split).issubset({'train','validation','test'}):
        raise ValueError('invalid manifest')
    if len(m) != len(df) or set(m.trans_num) != set(df.trans_num):
        raise ValueError('manifest does not cover transactions one-to-one')
    if config.get('split_hash') and stable_split_hash(m) != config['split_hash']:
        raise ValueError('split hash mismatch')
    df = df.sort_values(['cc_num','timestamp','trans_num'], kind='mergesort').reset_index(drop=True)
    ts = df.timestamp.astype('int64').to_numpy()
    amt = df.amt.to_numpy(dtype=float)
    cards = df.cc_num.to_numpy(); merchants = df.merchant.to_numpy(); categories = df.category.to_numpy()
    nrows = len(df); counts = np.zeros((nrows,3), dtype=np.int32); values = np.full((nrows,7), np.nan)
    i = 0
    while i < nrows:
        card = cards[i]; queues = [deque(),deque(),deque()]; n=0; mean=0.; m2=0.; last=None; seen_m=set(); seen_c=set(); cs=0.; sn=0.
        while i < nrows and cards[i] == card:
            t = int(ts[i]); end=i+1
            while end < nrows and cards[end] == card and ts[end] == t: end += 1
            for k,w in enumerate(WINDOWS):
                while queues[k] and queues[k][0] < t-w: queues[k].popleft()
                counts[i:end,k] = len(queues[k])
            angle = 2*math.pi*((t % 86400_000_000_000)/86400_000_000_000)
            for j in range(i,end):
                if n:
                    values[j,0] = mean; values[j,1] = math.sqrt(max(0.,m2/n))
                    if mean != 0 and math.isfinite(mean): values[j,2] = amt[j]/mean
                    values[j,3] = (t-last)/1e9
                    if math.hypot(cs,sn) > 1e-12*n:
                        a = math.atan2(sn,cs) % (2*math.pi); delta = abs(angle-a); values[j,6] = min(delta,2*math.pi-delta)*12/math.pi
                if pd.notna(merchants[j]): values[j,4] = float(merchants[j] not in seen_m)
                if pd.notna(categories[j]): values[j,5] = float(categories[j] not in seen_c)
            for j in range(i,end):
                for q in queues: q.append(t)
                n += 1; d=amt[j]-mean; mean += d/n; m2 += d*(amt[j]-mean)
                if pd.notna(merchants[j]): seen_m.add(merchants[j])
                if pd.notna(categories[j]): seen_c.add(categories[j])
                cs += math.cos(angle); sn += math.sin(angle)
            last=t; i=end
    out = pd.DataFrame(counts,columns=FEATURES[:3]); out[FEATURES[3:]] = values; out.insert(0,'trans_num',df.trans_num.astype('string'))
    return out


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(4*1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=ROOT/'data/features/behavioral_v1'); args=parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()): raise FileExistsError('output exists; preserve it before running')
    start=time.perf_counter(); proc=ROOT/'data/processed/transactions.parquet'; manifest=ROOT/'data/splits/split_manifest.parquet'; meta=json.loads((ROOT/'data/splits/split_metadata.json').read_text())
    if meta['split_hash'] != EXPECTED_HASH: raise ValueError('metadata split hash mismatch')
    data=pd.read_parquet(proc,columns=['trans_num','cc_num','timestamp','amt','merchant','category']); m=pd.read_parquet(manifest)
    out=build_behavioral_features(data,m,{'split_hash':EXPECTED_HASH}); joined=out.merge(m,on='trans_num',validate='one_to_one')
    if joined['split'].value_counts().to_dict() != meta['rows']: raise ValueError('split row counts mismatch')
    args.output.mkdir(parents=True,exist_ok=True); outputs={}; stats={}
    for split in ('train','validation','test'):
        frame=joined.loc[joined['split']==split,['trans_num']+FEATURES]; path=args.output/f'{split}.parquet'
        table=pa.Table.from_pandas(frame,preserve_index=False); idx=table.schema.get_field_index('trans_num'); table=table.set_column(idx,'trans_num',table.column(idx).cast(pa.string())); pq.write_table(table,path,compression='zstd')
        outputs[split]={'rows':len(frame),'sha256':sha(path)}
        stats[split]={c:{'null':int(frame[c].isna().sum()),'min':None if frame[c].dropna().empty else float(frame[c].min()),'max':None if frame[c].dropna().empty else float(frame[c].max()),'q50':None if frame[c].dropna().empty else float(frame[c].quantile(.5)),'q95':None if frame[c].dropna().empty else float(frame[c].quantile(.95))} for c in FEATURES}
        assert not np.isinf(frame[FEATURES].to_numpy()).any()
        assert (frame.txn_count_1h <= frame.txn_count_24h).all() and (frame.txn_count_24h <= frame.txn_count_7d).all()
        assert pq.read_schema(path).names == ['trans_num']+FEATURES
    git=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True)
    result={'feature_version':'behavioral_v1','null_policy':{'production_merchant_category':'reject','historical_statistics':'undefined as NaN','novelty_missing':'NaN in robustness fixtures'},'feature_order':FEATURES,'dtypes':{'trans_num':'string',**{c:('int32' if c in FEATURES[:3] else 'float64') for c in FEATURES}},'inputs':{'processed_sha256':sha(proc),'manifest_sha256':sha(manifest)},'outputs':outputs,'split_hash':EXPECTED_HASH,'git_head':subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True).stdout.strip(),'git_status':git.stdout if git.returncode == 0 else None,'git_status_error':git.stderr.strip() if git.returncode else None,'python':platform.python_version(),'pandas':pd.__version__,'pyarrow':pa.__version__,'decisions':'D01-D06 approved 2026-11-24; circular epsilon 1e-12','generated_utc':datetime.now(timezone.utc).isoformat(),'runtime_seconds':round(time.perf_counter()-start,2),'statistics':stats}
    (args.output/'metadata.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); print(json.dumps({'outputs':outputs,'runtime_seconds':result['runtime_seconds']}))

if __name__ == '__main__': main()
