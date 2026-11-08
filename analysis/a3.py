import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',300)
L=pd.read_pickle('L.pkl')
G=pd.read_csv('../data/mock_gstin_registry.csv'); U=pd.read_csv('../data/mock_udyam_registry.csv')
print(G.status.value_counts(), G.constitution.value_counts(), U.enterprise_type.value_counts(), U.major_activity.value_counts(), sep='\n')
print('dup gst',G.gstin.duplicated().sum(),'dup udyam',U.udyam_number.duplicated().sum())
# join
m=L.merge(G,on='gstin',how='left',suffixes=('','_g'),indicator='gi')
print(pd.crosstab(m.has_gstin,m.gi))
m=m.merge(U,on='udyam_number',how='left',suffixes=('','_u'),indicator='ui')
print(pd.crosstab(m.has_udyam,m.ui))
# GST status vs outcome
print(m.groupby('status',dropna=False).agg(n=('act','size'),conv=('act','mean'),reach_kyc=('r',lambda x:(x>=4).mean())).to_string())
print(pd.crosstab(m.status.fillna('none'),m.stage_reached).to_string())
print(pd.crosstab(m.status.fillna('none'),m.drop_reason.fillna('ACTIVATED')).T.to_string())
# name match
import re
def norm(s): 
    s=str(s).lower(); s=re.sub(r'\(prop\.?\s*','',s); s=re.sub(r'[^a-z0-9 ]',' ',s); return ' '.join(s.split())
from difflib import SequenceMatcher
def sim(a,b): return SequenceMatcher(None,norm(a),norm(b)).ratio()
mg=m[m.gi=='both'].copy()
mg['tn_sim']=[sim(a,b) for a,b in zip(mg.business_name,mg.trade_name)]
mg['ln_contains']=[norm(a) in norm(b) for a,b in zip(mg.business_name,mg.legal_name)]
mg['state_ok']=mg.state==mg.state_g
print('gst trade name sim dist',mg.tn_sim.describe()); print('state mismatch',(~mg.state_ok).sum())
print((mg.tn_sim<0.9).sum())
print(mg[mg.tn_sim<0.9][['business_name','trade_name','legal_name','stage_reached','drop_reason']].head(20).to_string())
mu=m[m.ui=='both'].copy()
mu['en_sim']=[sim(a,b) for a,b in zip(mu.business_name,mu.enterprise_name)]
mu['st_ok']=mu.state==mu.state_u; mu['city_ok']=mu.city==mu.city_u
print('udyam sim<0.9',(mu.en_sim<0.9).sum(),'state mismatch',(~mu.st_ok).sum(),'city mismatch',(~mu.city_ok).sum())
print(mu[mu.en_sim<0.9][['business_name','enterprise_name','stage_reached','drop_reason']].head(15).to_string())
# udyam enterprise type vs segment
print(pd.crosstab(mu.segment,mu.enterprise_type))
# registry ages
mg['gst_age_days']=(pd.Timestamp('2026-07-15')-pd.to_datetime(mg.registration_date)).dt.days
print(mg.groupby(pd.cut(mg.gst_age_days,[-1,180,365,730,1825,99999])).act.agg(['size','mean']))
m.to_pickle('M.pkl')
