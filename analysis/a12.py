import pandas as pd, numpy as np
A=pd.read_pickle('A.pkl'); P=pd.read_csv('../data/product_catalogue.csv').set_index('product_id')
def nps(s): return round(((s>=9).mean()-(s<=6).mean())*100,1)
print('NPS calls<=1',nps(A[A.customer_follow_up_calls<=1].nps_score),'n',(A.customer_follow_up_calls<=1).sum())
print('NPS calls<=2 & days<=15',nps(A[(A.customer_follow_up_calls<=2)&(A.days_lead_to_activation<=15)].nps_score),((A.customer_follow_up_calls<=2)&(A.days_lead_to_activation<=15)).sum())
print('NPS days<=15',nps(A[A.days_lead_to_activation<=15].nps_score),'days>21',nps(A[A.days_lead_to_activation>21].nps_score))
for c in range(1,6): print(c,nps(A[A.customer_follow_up_calls==c].nps_score))
mid=(P.price_min_inr_per_month+P.price_max_inr_per_month)/2
bundles={
'Dukaan Starter (Micro)':{'P01':1,'P07':1,'P19':1,'P22':1},
'Dukaan Starter - no fibre (5G FWA)':{'P04':1,'P07':1,'P19':1},
'Clinic & Office Pro (Professional)':{'P02':1,'P16':5,'P20':5,'P08':1,'P07':1,'P17':1},
'Multi-site One-Bill (5 sites)':{'P02':5,'P09':5,'P08':5,'P19':5,'P23':10,'P10':5},
'Factory Connect (Manufacturer)':{'P05':1,'P08':3,'P16':10,'P20':10,'P21':1,'P11':1},
}
for n,b in bundles.items():
    lo=sum(P.loc[p,'price_min_inr_per_month']*q for p,q in b.items()); hi=sum(P.loc[p,'price_max_inr_per_month']*q for p,q in b.items())
    su=sum(P.loc[p,'one_time_setup_inr']*q for p,q in b.items()); ct=max(P.loc[p,'min_contract_months'] for p in b); ins=max(P.loc[p,'typical_install_days'] for p in b)
    g=any(P.loc[p,'requires_gstin']=='Y' for p in b)
    print(f'{n}: ₹{lo:,}-{hi:,}/mo setup ₹{su:,} contract {ct}m install {ins}d needs_GST {g}')
# segment actual median bundle
print(A.groupby('segment').monthly_bundle_value_inr.median())
# micro: share of micro leads without GST and with udyam
m=pd.read_pickle('M3.pkl')
print(pd.crosstab(m.segment,[m.has_gstin,m.has_udyam],normalize='index').round(3))
print('compliance: GST-required product sold w/o valid GSTIN',A.viol.map(lambda v:any('gst' in x for x in v)).sum())
print('mis-match: activated who bought none of products asked', (A.overlap==0).sum(), (A.overlap==0).mean())
