"""Validate saved behavioral features independently; exits nonzero on mismatch."""
import argparse
import json
from pathlib import Path
import ctypes
from ctypes import wintypes
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from src.data.split import stable_split_hash
from src.features.behavioral import FEATURES, EXPECTED_HASH, ROOT, sha


def validate(directory, metadata_path=None):
    directory=Path(directory); metadata_path=Path(metadata_path or directory/'metadata.json')
    meta=json.loads(metadata_path.read_text(encoding='utf-8-sig'))
    def require(condition, message):
        if not condition: raise ValueError(message)
    require(meta.get('feature_version') == 'behavioral_v1','invalid feature version')
    require(meta.get('feature_order') == FEATURES,'feature order mismatch')
    require(meta.get('split_hash') == EXPECTED_HASH,'metadata split hash mismatch')
    require(meta.get('null_policy',{}).get('production_merchant_category') == 'reject','null policy missing or invalid')
    manifest_path=ROOT/'data/splits/split_manifest.parquet'; processed_path=ROOT/'data/processed/transactions.parquet'
    require(meta['inputs']['manifest_sha256']==sha(manifest_path) and meta['inputs']['processed_sha256']==sha(processed_path),'input checksum mismatch')
    manifest=pd.read_parquet(manifest_path)
    require(manifest.trans_num.notna().all() and manifest.trans_num.is_unique,'manifest IDs invalid')
    require(stable_split_hash(manifest)==EXPECTED_HASH,'manifest split hash mismatch')
    counts={'train':1037340,'validation':259335,'test':555719}
    require(manifest['split'].value_counts().to_dict()==counts,'manifest split counts mismatch')
    for split, expected in counts.items():
        path=directory/f'{split}.parquet'; require(sha(path)==meta['outputs'][split]['sha256'],'output checksum mismatch: '+split)
        schema=pq.read_schema(path); require(schema.names==['trans_num']+FEATURES,'output columns mismatch')
        require(schema.field('trans_num').type==pa.string(),'invalid trans_num dtype')
        require(all(schema.field(c).type==pa.int32() for c in FEATURES[:3]),'invalid count dtype')
        require(all(schema.field(c).type==pa.float64() for c in FEATURES[3:]),'invalid feature dtype')
        frame=pd.read_parquet(path); require(len(frame)==expected==meta['outputs'][split]['rows'],'row count mismatch')
        require(frame.trans_num.notna().all() and frame.trans_num.is_unique,'duplicate or null IDs')
        require(set(frame.trans_num)==set(manifest.loc[manifest.split==split,'trans_num']),'manifest join mismatch')
        require(not np.isinf(frame[FEATURES].to_numpy()).any(),'infinite value')
        require((frame.txn_count_1h<=frame.txn_count_24h).all() and (frame.txn_count_24h<=frame.txn_count_7d).all(),'count ordering mismatch')
        for feature in FEATURES:
            require(int(frame[feature].isna().sum())==meta['statistics'][split][feature]['null'],'null count mismatch')
    return counts


def peak_memory():
    if __import__('os').name != 'nt': return None
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD),('PeakWorkingSetSize',ctypes.c_size_t),('WorkingSetSize',ctypes.c_size_t),('QuotaPeakPagedPoolUsage',ctypes.c_size_t),('QuotaPagedPoolUsage',ctypes.c_size_t),('QuotaPeakNonPagedPoolUsage',ctypes.c_size_t),('QuotaNonPagedPoolUsage',ctypes.c_size_t),('PagefileUsage',ctypes.c_size_t),('PeakPagefileUsage',ctypes.c_size_t)]
    counters=Counters(); counters.cb=ctypes.sizeof(counters)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True); kernel.GetCurrentProcess.restype=wintypes.HANDLE
    get_info=ctypes.WinDLL('psapi',use_last_error=True).GetProcessMemoryInfo; get_info.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]; get_info.restype=wintypes.BOOL
    ok=get_info(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb)
    return counters.PeakWorkingSetSize if ok else None


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--directory',type=Path,default=ROOT/'data/features/behavioral_v1'); parser.add_argument('--metadata',type=Path); args=parser.parse_args()
    result=validate(args.directory,args.metadata); print(json.dumps({'status':'PASS','rows':result,'peak_working_set_bytes':peak_memory()}))

if __name__=='__main__': main()
