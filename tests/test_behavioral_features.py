import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from src.features.behavioral import build_behavioral_features as build
from src.data.split import stable_split_hash


def fixture():
    df=pd.DataFrame([('a','A','2020-01-01 23:00',10.,'m','x',0),('b','A','2020-01-02 00:00',20.,'n','y',1),('c','A','2020-01-02 00:00',30.,'n','y',0),('d','A','2020-01-03 00:00',40.,'m','x',1),('e','B','2020-01-03 00:00',50.,'m','x',0)],columns=['trans_num','cc_num','timestamp','amt','merchant','category','is_fraud'])
    df.timestamp=pd.to_datetime(df.timestamp).astype('datetime64[ns]')
    manifest=pd.DataFrame({'trans_num':df.trans_num,'split':['train','validation','validation','test','test']})
    return df,manifest


def test_values_ties_windows_cross_split_and_card():
    df,m=fixture(); out=build(df,m).set_index('trans_num')
    assert list(out.loc['a',['txn_count_1h','txn_count_24h','txn_count_7d']]) == [0,0,0]
    assert np.isnan(out.loc['a','hist_amt_mean']) and out.loc['a','is_new_merchant']==1
    for name in ['b','c']:
        assert out.loc[name,'txn_count_1h']==1 and out.loc[name,'hist_amt_mean']==10
        assert out.loc[name,'hist_amt_std']==0 and out.loc[name,'txn_recency']==3600
        assert out.loc[name,'is_new_merchant']==1 and out.loc[name,'is_new_category']==1
        assert out.loc[name,'hour_deviation']==pytest.approx(1)
    assert out.loc['b','amt_ratio']==2 and out.loc['c','amt_ratio']==3
    assert out.loc['d','txn_count_24h']==2 and out.loc['d','txn_count_7d']==3
    assert out.loc['d','hist_amt_mean']==20 and out.loc['d','hist_amt_std']==pytest.approx(np.std([10,20,30]))
    assert out.loc['d','is_new_merchant']==0 and out.loc['e','txn_count_7d']==0


def test_future_labels_order_independence():
    df,m=fixture(); base=build(df,m).sort_values('trans_num').reset_index(drop=True)
    df.is_fraud=1-df.is_fraud
    shuffled=build(df.sample(frac=1,random_state=3),m.sample(frac=1,random_state=4)).sort_values('trans_num').reset_index(drop=True)
    assert_frame_equal(base,shuffled)
    future=df.iloc[[0]].copy(); future['trans_num']='future'; future['timestamp']=pd.Timestamp('2021-01-01'); future['amt']=9999.
    extra=pd.concat([df,future],ignore_index=True); mm=pd.concat([m,pd.DataFrame({'trans_num':['future'],'split':['test']})],ignore_index=True)
    got=build(extra,mm).query("trans_num != 'future'").sort_values('trans_num').reset_index(drop=True)
    assert_frame_equal(base,got)


def test_validation_and_hash():
    df,m=fixture(); build(df,m,{'split_hash':stable_split_hash(m)})
    with pytest.raises(ValueError): build(df,m,{'split_hash':'wrong'})
    with pytest.raises(ValueError): build(df,m.iloc[:-1])
    with pytest.raises(ValueError): build(pd.concat([df,df.iloc[:1]]),m)
    for column in ['cc_num','timestamp','amt','merchant','category']:
        bad=df.copy(); bad.loc[0,column]=None
        with pytest.raises(ValueError): build(bad,m)


def test_null_novelty_zero_mean_and_boundaries():
    df,m=fixture(); df.loc[0,'amt']=0.; df.loc[0,'merchant']=None
    out=build(df,m,{'allow_null_categories':True}).set_index('trans_num')
    assert np.isnan(out.loc['a','is_new_merchant']) and out.loc['b','is_new_merchant']==1
    assert np.isnan(out.loc['b','amt_ratio'])
    df.loc[1,'timestamp']=df.loc[0,'timestamp']+pd.Timedelta(days=7)
    out=build(df,m,{'allow_null_categories':True}).set_index('trans_num')
    assert out.loc['b','txn_count_7d']>=1


def test_window_exact_edges_and_one_nanosecond_outside():
    times=['2020-01-01 00:00:00','2020-01-01 00:00:00.000000001','2020-01-08 00:00:00']
    df=pd.DataFrame({'trans_num':['x','y','z'],'cc_num':['A']*3,'timestamp':pd.to_datetime(times,format='mixed').astype('datetime64[ns]'),'amt':[1.,2.,3.],'merchant':['m']*3,'category':['c']*3})
    m=pd.DataFrame({'trans_num':df.trans_num,'split':['train','train','test']})
    result=build(df,m).set_index('trans_num')
    assert result.loc['z','txn_count_7d']==2
    df.loc[2,'timestamp'] += pd.Timedelta(1,unit='ns')
    assert build(df,m).set_index('trans_num').loc['z','txn_count_7d']==1


def test_opposite_hour_undefined():
    df=pd.DataFrame({'trans_num':['x','y','z'],'cc_num':['A']*3,'timestamp':pd.to_datetime(['2020-01-01 00:00','2020-01-01 12:00','2020-01-02 00:00']).astype('datetime64[ns]'),'amt':[1.,2.,3.],'merchant':['m']*3,'category':['c']*3})
    m=pd.DataFrame({'trans_num':df.trans_num,'split':['train','validation','test']})
    assert np.isnan(build(df,m).set_index('trans_num').loc['z','hour_deviation'])

@pytest.mark.parametrize('window,feature', [('1h','txn_count_1h'), ('24h','txn_count_24h'), ('7d','txn_count_7d')])
def test_window_lower_bound_and_tied_anchor(window, feature):
    anchor = pd.Timestamp('2021-01-10 00:00:00')
    boundary = anchor - pd.Timedelta(window)
    df = pd.DataFrame({'trans_num':['outside','edge','anchor_a','anchor_b'], 'cc_num':['A']*4,
        'timestamp':pd.to_datetime([boundary-pd.Timedelta(1,unit='ns'),boundary,anchor,anchor]).astype('datetime64[ns]'),
        'amt':[1.,2.,3.,4.], 'merchant':['m']*4, 'category':['c']*4})
    m = pd.DataFrame({'trans_num':df.trans_num, 'split':['train','train','test','test']})
    out=build(df,m).set_index('trans_num')
    assert out.loc['anchor_a',feature] == 1
    assert out.loc['anchor_b',feature] == 1
