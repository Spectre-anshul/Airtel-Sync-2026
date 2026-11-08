import pandas as pd, numpy as np
pd.set_option('display.width',260); pd.set_option('display.max_columns',60); pd.set_option('display.max_rows',300)
m=pd.read_pickle('M.pkl')
P=pd.read_csv('../data/product_catalogue.csv').set_index('product_id')
def pct(ct): return (ct.div(ct.sum(0),axis=1)*100).round(1)
d=m[m.outcome=='Dropped']
for c in ['segment','lead_source','preferred_language','has_gstin','city_tier']:
    print('\n== drop reason share by',c); print(pct(pd.crosstab(d.drop_reason,d[c])).to_string())
# rate of drop reason per lead (incidence)
print('\n== incidence per 100 leads, language'); 
ct=pd.crosstab(m.drop_reason.fillna('ACT'),m.preferred_language); print((ct/ct.sum()*100).round(1).loc[['Quote too complex to understand','Unreachable after 3 attempts','Not interested on first call','Price too high','Owner had no time for a visit']].to_string())
m['vern']=~m.preferred_language.isin(['Hindi','English'])
print(m.groupby('vern').agg(n=('act','size'),conv=('act','mean'),rc=('r',lambda x:(x>=1).mean()),rn=('r',lambda x:(x>=2).mean()),rq=('r',lambda x:(x>=3).mean())))
# conditional stage conversion by vern
def stagecv(g):
    out={}
    for i,s in enumerate(['contact','needs','quote','kyc','act']):
        out[s]=((g.r>=i+1).sum()/max((g.r>=i).sum(),1))
    return pd.Series(out)
for c in ['vern','has_gstin','segment','lead_source','city_tier']:
    print('\n== stage conv by',c); print(m.groupby(c).apply(stagecv).round(3).to_string())
# poi analysis
m['poi']=m.products_of_interest.fillna('').map(lambda s:[x for x in s.split(';') if x])
m['npoi']=m.poi.map(len)
print(m.groupby('npoi').act.agg(['size','mean']))
# poi eligible?
def elig(row,p):
    r=P.loc[p]; why=[]
    if str(row.city_tier) not in str(r.available_city_tiers).split(';'): why.append('tier')
    if row.employee_count<r.min_employees: why.append('emp')
    if row.num_sites<r.min_sites: why.append('sites')
    if r.requires_gstin=='Y' and not (row.has_gstin=='Y' and row.status=='Active'): why.append('gst')
    return why
m['poi_inel']=m.apply(lambda r:[ (p,w) for p in r.poi for w in elig(r,p)],axis=1)
m['any_inel']=m.poi_inel.map(len)>0
print('\nleads with any ineligible interest',m.any_inel.mean(), m.any_inel.sum())
from collections import Counter
print(Counter(w for l in m.poi_inel for _,w in l))
print(m.groupby('any_inel').apply(stagecv).round(3)); print(m.groupby('any_inel').act.mean())
gate=m[m.poi_inel.map(lambda l:any(w=='gst' for _,w in l))]
print('gst-gated interest leads',len(gate),'conv',gate.act.mean(), 'has_udyam share',(gate.has_udyam=='Y').mean())
print(pd.crosstab(gate.drop_reason.fillna('ACT'),gate.stage_reached).to_string())
# product interest popularity by segment
from itertools import chain
for s,g in m.groupby('segment'):
    c=Counter(chain.from_iterable(g.poi)); print(s,[ (k,v) for k,v in c.most_common(8)])
# no-GST leads -- which reasons at quote stage
ng=m[m.has_gstin=='N']
print(ng.groupby('has_udyam').agg(n=('act','size'),conv=('act','mean')))
# month trend
m['mon']=m.created_date.dt.month
print(m.groupby('mon').agg(n=('act','size'),conv=('act','mean')))
# city
print(m.groupby('city').agg(n=('act','size'),conv=('act','mean'),tier=('city_tier','first')).sort_values('conv').to_string())
# Language vs state fit
print(pd.crosstab(m.state,m.preferred_language).to_string())
m.to_pickle('M2.pkl')
