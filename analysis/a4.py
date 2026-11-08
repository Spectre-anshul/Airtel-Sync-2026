import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',300)
m=pd.read_pickle('M.pkl')
P=pd.read_csv('../data/product_catalogue.csv').set_index('product_id')
A=m[m.act==1].copy()
def parse(b): 
    out={}
    for t in str(b).split(';'):
        if 'x' in t: p,q=t.split('x'); out[p]=int(q)
    return out
A['bd']=A.bundle_products.map(parse)
A['nprod']=A.bd.map(len)
# recompute value
def val(d,col): return sum(P.loc[p,col]*q for p,q in d.items())
A['vmin']=A.bd.map(lambda d:val(d,'price_min_inr_per_month')); A['vmax']=A.bd.map(lambda d:val(d,'price_max_inr_per_month'))
A['setup_calc']=A.bd.map(lambda d:val(d,'one_time_setup_inr'))
A['in_range']=(A.monthly_bundle_value_inr>=A.vmin)&(A.monthly_bundle_value_inr<=A.vmax)
print('value in catalogue range',A.in_range.mean(), 'setup match',(A.setup_calc==A.one_time_setup_inr).mean())
print(A[~A.in_range][['monthly_bundle_value_inr','vmin','vmax']].head())
# eligibility violations
def viol(row):
    v=[]
    for p,q in row.bd.items():
        r=P.loc[p]
        if str(row.city_tier) not in str(r.available_city_tiers).split(';'): v.append(f'{p}:tier')
        if row.employee_count<r.min_employees: v.append(f'{p}:emp')
        if row.num_sites<r.min_sites: v.append(f'{p}:sites')
        if r.requires_gstin=='Y' and (row.has_gstin!='Y' or row.status!='Active'): v.append(f'{p}:gst({row.status})')
        if isinstance(r.requires_one_of,str) and not any(x in row.bd for x in r.requires_one_of.split('|')): v.append(f'{p}:dep')
    return v
A['viol']=A.apply(viol,axis=1); A['nviol']=A.viol.map(len)
print('activations with any violation',(A.nviol>0).sum())
from collections import Counter
c=Counter(x.split(':')[1] for v in A.viol for x in v); print(c)
print(A[A.nviol>0][['lead_id','status','bundle_products','viol','churned_within_6_months','nps_score']].head(40).to_string())
print(A.groupby(A.nviol>0).agg(n=('act','size'),churn=('churned_within_6_months',lambda x:(x=='Y').mean()),nps=('nps_score','mean')))
# interest vs bought
A['poi']=A.products_of_interest.fillna('').map(lambda s:set(s.split(';'))-{''})
A['bought']=A.bd.map(lambda d:set(d))
A['overlap']=[len(a&b)/len(a) if a else np.nan for a,b in zip(A.poi,A.bought)]
A['extra']=[len(b-a) for a,b in zip(A.poi,A.bought)]
print('overlap',A.overlap.describe()); print(A.groupby(pd.cut(A.overlap,[-.01,0,.5,.99,1])).agg(n=('act','size'),churn=('churned_within_6_months',lambda x:(x=='Y').mean()),nps=('nps_score','mean')))
print(A.groupby('extra').agg(n=('act','size'),churn=('churned_within_6_months',lambda x:(x=='Y').mean()),nps=('nps_score','mean')))
# churn / nps drivers
A['churn']=(A.churned_within_6_months=='Y').astype(int)
for c in ['customer_follow_up_calls','contract_months','lead_source','segment','preferred_language','city_tier','nprod','status']:
    print('\n--',c); print(A.groupby(c).agg(n=('act','size'),churn=('churn','mean'),nps=('nps_score','mean'),days=('days_lead_to_activation','mean')).round(3).to_string())
A['dbin']=pd.cut(A.days_lead_to_activation,[0,12,15,18,21,40])
print(A.groupby('dbin').agg(n=('act','size'),churn=('churn','mean'),nps=('nps_score','mean'),calls=('customer_follow_up_calls','mean')).round(3))
print(np.corrcoef(A.days_lead_to_activation,A.customer_follow_up_calls)[0,1], np.corrcoef(A.customer_follow_up_calls,A.nps_score)[0,1],np.corrcoef(A.days_lead_to_activation,A.nps_score)[0,1])
# value vs current spend
A['ratio']=A.monthly_bundle_value_inr/A.monthly_telecom_spend_inr
print(A.groupby(pd.qcut(A.ratio,4)).agg(n=('act','size'),churn=('churn','mean'),nps=('nps_score','mean')))
# install days
A['inst_days']=(A.activated_date-A.kyc_complete_date).dt.days
A['max_install']=A.bd.map(lambda d:max(P.loc[p,'typical_install_days'] for p in d))
print(A[['inst_days','max_install']].corr())
# product popularity
cnt=Counter(p for d in A.bd for p in d); print(sorted(cnt.items(),key=lambda x:-x[1]))
A.to_pickle('A.pkl')
