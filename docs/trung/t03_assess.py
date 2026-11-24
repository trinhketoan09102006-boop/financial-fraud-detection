import argparse
import json, hashlib, time, sys, platform
from pathlib import Path
R=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description='Recompute T03 aggregate statistics and plots from existing artifacts; outputs are protected unless --overwrite is provided.')
parser.add_argument('--output-dir',type=Path,default=R/'results/features/behavioral_v1')
parser.add_argument('--overwrite',action='store_true',help='Allow replacement of existing T03 outputs in the chosen output directory')
args=parser.parse_args()
O=args.output_dir.resolve()
if O == R or O == R/'data' or (R/'data') in O.parents:
 raise ValueError('Output directory must not be repository root or within data/')
output_names=['feature_statistics.csv','novelty_rates.csv','train_pearson.csv','train_spearman.csv','train_fraud_comparison.csv','missing_rate.png','velocity_median.png','novelty_rate.png','train_pearson_heatmap.png','distribution_comparison.png','assessment_summary.json']
if not args.overwrite and any((O/name).exists() for name in output_names):
 raise FileExistsError('Output already exists; choose an empty --output-dir or explicitly use --overwrite')
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yaml
sys.path.insert(0,str(R))
from src.data.split import stable_split_hash
from src.features.validate_behavioral import peak_memory
O.mkdir(parents=True,exist_ok=True)
D=R/'data/features/behavioral_v1'; start=time.perf_counter()
F=['txn_count_1h','txn_count_24h','txn_count_7d','hist_amt_mean','hist_amt_std','amt_ratio','txn_recency','is_new_merchant','is_new_category','hour_deviation']
H='aabb7d14153b48bc353dc84d25b624cce1b74f321edb74edfc6138ba08faf5b8'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
meta=json.loads((D/'metadata.json').read_text(encoding='utf-8-sig')); m=pd.read_parquet(R/'data/splits/split_manifest.parquet'); cfg=yaml.safe_load((R/'configs/split.yaml').read_text()); sm=json.loads((R/'data/splits/split_metadata.json').read_text()); counts={'train':1037340,'validation':259335,'test':555719}; checks={}
checks['feature_version']=meta['feature_version']=='behavioral_v1'; checks['feature_order']=meta['feature_order']==F; checks['split_hash']=stable_split_hash(m)==H==meta['split_hash']==cfg['split_hash']==sm['split_hash']; checks['manifest_unique']=m.trans_num.notna().all() and m.trans_num.is_unique; checks['input_hash']=sha(R/'data/processed/transactions.parquet')==meta['inputs']['processed_sha256'] and sha(R/'data/splits/split_manifest.parquet')==meta['inputs']['manifest_sha256']; hashes={'processed':sha(R/'data/processed/transactions.parquet'),'manifest':sha(R/'data/splits/split_manifest.parquet'),'metadata':sha(D/'metadata.json')}
frames={}; rows=[]; nov=[]; inv={}; fraud=[]
for sp in counts:
 p=D/(sp+'.parquet'); h=sha(p); hashes[sp]=h; sch=pq.read_schema(p); x=pd.read_parquet(p); frames[sp]=x
 checks[sp+'_checksum']=h==meta['outputs'][sp]['sha256']; checks[sp+'_schema']=sch.names==['trans_num']+F and sch.field('trans_num').type==pa.string() and all(sch.field(c).type==pa.int32() for c in F[:3]) and all(sch.field(c).type==pa.float64() for c in F[3:]); checks[sp+'_ids']=len(x)==counts[sp]==meta['outputs'][sp]['rows'] and x.trans_num.notna().all() and x.trans_num.is_unique and set(x.trans_num)==set(m.loc[m.split==sp,'trans_num'])
 inv[sp]={'count_order':int((~((x.txn_count_1h<=x.txn_count_24h)&(x.txn_count_24h<=x.txn_count_7d))).sum()),'negative_counts':int((x[F[:3]]<0).any(axis=1).sum()),'negative_mean':int((x.hist_amt_mean.dropna()<0).sum()),'negative_std':int((x.hist_amt_std.dropna()<0).sum()),'negative_ratio':int((x.amt_ratio.dropna()<0).sum()),'nonpositive_recency':int((x.txn_recency.dropna()<=0).sum()),'invalid_hour':int((~x.hour_deviation.dropna().between(0,12)).sum()),'invalid_novelty':int((~x.is_new_merchant.isin([0.,1.]) | ~x.is_new_category.isin([0.,1.])).sum())}
 for c in F:
  a=x[c]; q=a.quantile([.01,.05,.25,.5,.75,.95,.99]); rows.append({'split':sp,'feature':c,'rows':len(a),'valid':int(a.notna().sum()),'missing':int(a.isna().sum()),'missing_rate':float(a.isna().mean()),'inf_count':int(np.isinf(a.to_numpy()).sum()),'min':a.min(),'max':a.max(),'mean':a.mean(),'median':q.loc[.5],'std_sample_ddof1':a.std(),'p01':q.loc[.01],'p05':q.loc[.05],'p25':q.loc[.25],'p75':q.loc[.75],'p95':q.loc[.95],'p99':q.loc[.99],'zero_rate_all_rows':float(a.eq(0).mean()),'unique_nonnull':int(a.nunique())})
 for c in F[7:9]:
  nov.append({'split':sp,'feature':c,'rate_0':float(x[c].eq(0).mean()),'rate_1':float(x[c].eq(1).mean()),'rate_nan':float(x[c].isna().mean())})
stats=pd.DataFrame(rows);stats.to_csv(O/'feature_statistics.csv',index=False);pd.DataFrame(nov).to_csv(O/'novelty_rates.csv',index=False)
train=frames['train']; pear=train[F].corr(method='pearson'); spear=train[F].corr(method='spearman'); pear.to_csv(O/'train_pearson.csv');spear.to_csv(O/'train_spearman.csv')
source=pd.read_parquet(R/'data/processed/transactions.parquet',columns=['trans_num','cc_num','timestamp','amt','merchant','category']); checks['source_amount_positive']=bool((source.amt>0).all()); checks['source_categories_nonnull']=bool(source[['merchant','category']].notna().all().all());
allfeatures=pd.concat([frames[s] for s in counts],ignore_index=True); joined=source.merge(allfeatures,on='trans_num',validate='one_to_one'); first=joined.groupby('cc_num',sort=False).timestamp.transform('min'); cold=joined.timestamp.eq(first); coldx=joined.loc[cold]; cold_bad=((coldx[F[:3]]!=0).any(axis=1)|coldx[['hist_amt_mean','hist_amt_std','amt_ratio','txn_recency','hour_deviation']].notna().any(axis=1)|(coldx.is_new_merchant!=1)|(coldx.is_new_category!=1));
missing_evidence={c:{'missing':int(joined[c].isna().sum()),'cold_missing':int((joined[c].isna() & cold).sum()),'noncold_missing':int((joined[c].isna() & ~cold).sum()),'cold_nonmissing':int((joined[c].notna() & cold).sum())} for c in ['hist_amt_mean','hist_amt_std','amt_ratio','txn_recency','hour_deviation']}
tie=joined.groupby(['cc_num','timestamp'],sort=False).trans_num.transform('size')>1; t=joined.loc[tie]; shared=['txn_count_1h','txn_count_24h','txn_count_7d','hist_amt_mean','hist_amt_std','txn_recency','hour_deviation']; groups=t.groupby(['cc_num','timestamp'],sort=False,dropna=False); tie_groups=groups.ngroups; tie_bad={c:int((groups[c].nunique(dropna=False)>1).sum()) for c in shared};
inv['cold']={'cards':int(source.cc_num.nunique()),'rows':int(cold.sum()),'violations':int(cold_bad.sum()),'missing_evidence':missing_evidence}; inv['ties']={'groups':tie_groups,'rows':len(t),'violations_by_feature':tie_bad}
# Only train labels are read, via the pre-existing train split.
y=pd.read_parquet(R/'data/splits/train.parquet',columns=['trans_num','is_fraud']); z=train.merge(y,on='trans_num',validate='one_to_one');
for label,g in z.groupby('is_fraud'):
 for c in F:
  a=g[c]; fraud.append({'label':int(label),'feature':c,'rows':len(a),'valid':int(a.notna().sum()),'mean':a.mean(),'median':a.median(),'p95':a.quantile(.95),'zero_rate':float(a.eq(0).mean()),'one_rate':float(a.eq(1).mean()),'missing_rate':float(a.isna().mean())})
pd.DataFrame(fraud).to_csv(O/'train_fraud_comparison.csv',index=False)
# Each figure is descriptive; no thresholds fitted.
fig,ax=plt.subplots(figsize=(11,5)); piv=stats.pivot(index='feature',columns='split',values='missing_rate').loc[F];piv.plot.bar(ax=ax);ax.set_ylabel('Missing fraction');fig.tight_layout();fig.savefig(O/'missing_rate.png',dpi=130);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,5));piv=stats.pivot(index='feature',columns='split',values='median').loc[F[:3]];piv.plot.bar(ax=ax);ax.set_ylabel('Median transactions');fig.tight_layout();fig.savefig(O/'velocity_median.png',dpi=130);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,5)); ndf=pd.DataFrame(nov); ndf.assign(key=ndf['split']+' / '+ndf['feature']).set_index('key')['rate_1'].plot.bar(ax=ax);ax.set_ylabel('Novelty fraction');fig.tight_layout();fig.savefig(O/'novelty_rate.png',dpi=130);plt.close(fig)
fig,ax=plt.subplots(figsize=(9,8));im=ax.imshow(pear.to_numpy(),vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(10),F,rotation=75,ha='right');ax.set_yticks(range(10),F);fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(O/'train_pearson_heatmap.png',dpi=130);plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(10,7));
for ax,c in zip(axes.flat,['hist_amt_mean','amt_ratio','txn_recency','hour_deviation']):
 for sp,x in frames.items():
  a=x[c].dropna(); bins=np.linspace(0,float(train[c].quantile(.99)),40); ax.hist(a.clip(bins[0],bins[-1]),bins=bins,density=True,histtype='step',label=sp)
 ax.set_title(c+' (clipped at train P99)');ax.legend()
fig.tight_layout();fig.savefig(O/'distribution_comparison.png',dpi=130);plt.close(fig)
checks={k:bool(v) for k,v in checks.items()};inf=int(stats.inf_count.sum()); inv_pass=all(not any(v.values()) for k,v in inv.items() if k in counts) and not inv['cold']['violations'] and not any(tie_bad.values()) and inf==0
result={'checks':checks,'invariants':inv,'invariants_pass':inv_pass,'hashes':hashes,'runtime_seconds':round(time.perf_counter()-start,2),'peak_working_set_bytes':peak_memory(),'python':platform.python_version(),'pandas':pd.__version__,'pyarrow':pa.__version__,'charts':5,'split_hash':H}
(O/'assessment_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8'); print(json.dumps(result,indent=2));
if not all(checks.values()) or not inv_pass: sys.exit(2)
