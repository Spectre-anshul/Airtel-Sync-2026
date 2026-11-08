import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',250)
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
P=pd.read_csv('../data/product_catalogue.csv').set_index('product_id')
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete']
# cost per lead by source
print(m.groupby('lead_source').acquisition_cost_inr.agg(['mean','median','sum']).round(0))
print(m.groupby('stage_reached').acquisition_cost_inr.mean().round(0))
print(m.groupby(['lead_source','stage_reached']).acquisition_cost_inr.mean().unstack().round(0).to_string())
# monthly churn & LTV by segment
GM=0.40; H=36
def ltv(arpu,churn6):
    mc=1-(1-churn6)**(1/6); return sum(arpu*GM*(1-mc)**t for t in range(H)), mc
rows=[]
for s,g in list(A.groupby('segment'))+[('ALL',A)]:
    mm=m if s=='ALL' else m[m.segment==s]
    arpu=g.monthly_bundle_value_inr.mean(); ch=(g.churned_within_6_months=='Y').mean()
    L_,mc=ltv(arpu,ch); cac=mm.acquisition_cost_inr.sum()/len(g); setup=g.one_time_setup_inr.mean()
    rows.append(dict(seg=s,leads=len(mm),act=len(g),conv=len(g)/len(mm),arpu=arpu,arpu_med=g.monthly_bundle_value_inr.median(),churn6=ch,mchurn=mc,ltv36=L_,cac=cac,ltv_cac=L_/cac,payback=cac/(arpu*GM),nps=((g.nps_score>=9).mean()-(g.nps_score<=6).mean())*100,days=g.days_lead_to_activation.mean(),calls=g.customer_follow_up_calls.mean(),contract=g.contract_months.mean(),mrr_q=g.monthly_bundle_value_inr.sum()))
S=pd.DataFrame(rows).set_index('seg'); print(S.round(3).to_string())
# bundle composition by segment
from collections import Counter
for s,g in A.groupby('segment'):
    c=Counter(p for d in g.bd for p in d); print(s,len(g),[(p,P.loc[p,'product_name'],round(v/len(g),2)) for p,v in c.most_common(7)])
# typical bundle per segment median quantities
print(A.groupby('segment').max_install.describe())
print('install now mean',A.inst_days.mean(),'max typical install mean',A.max_install.mean())
S.to_csv('segment_econ.csv')
