import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50); pd.set_option('display.max_rows',200)
L=pd.read_csv('../data/smb_leads.csv',parse_dates=['created_date','contacted_date','needs_assessed_date','quote_accepted_date','kyc_complete_date','activated_date'])
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete','Activated']
rank={s:i for i,s in enumerate(st)}
L['r']=L.stage_reached.map(rank)
L['act']=(L.outcome=='Activated').astype(int)
# funnel
for i,s in enumerate(st): print(s,(L.r>=i).sum())
# drop reason by stage
print(pd.crosstab(L.drop_reason,L.stage_reached).reindex(columns=st[:-1]).to_string())
def grp(c):
    g=L.groupby(c).agg(n=('act','size'),act=('act','sum'),conv=('act','mean'),
      reach_contact=('r',lambda x:(x>=1).mean()),reach_need=('r',lambda x:(x>=2).mean()),reach_quote=('r',lambda x:(x>=3).mean()),reach_kyc=('r',lambda x:(x>=4).mean()),
      cac_total=('acquisition_cost_inr','sum'))
    g['cac_per_act']=g.cac_total/g.act.replace(0,np.nan)
    g['conv']=(g.conv*100).round(2)
    return g
for c in ['lead_source','segment','city_tier','preferred_language','has_gstin','has_udyam','annual_turnover_band','current_internet','current_provider','contact_role']:
    print('\n==',c); print(grp(c).round(3).to_string())
print('\n== gst x udyam'); print(L.pivot_table(index='has_gstin',columns='has_udyam',values='act',aggfunc=['mean','size']).to_string())
print('\nTotal CAC spend',L.acquisition_cost_inr.sum(),' per act',L.acquisition_cost_inr.sum()/L.act.sum())
A=L[L.act==1]
print('\nActivated: median bundle',A.monthly_bundle_value_inr.median(),'mean',A.monthly_bundle_value_inr.mean())
print(A.groupby('segment').agg(n=('act','size'),mbv_mean=('monthly_bundle_value_inr','mean'),mbv_med=('monthly_bundle_value_inr','median'),setup=('one_time_setup_inr','mean'),contract=('contract_months','mean'),days=('days_lead_to_activation','mean'),calls=('customer_follow_up_calls','mean'),churn=('churned_within_6_months',lambda x:(x=='Y').mean()),nps=('nps_score','mean')).round(2).to_string())
print('days',A.days_lead_to_activation.mean(),'calls',A.customer_follow_up_calls.mean(),'churn',(A.churned_within_6_months=='Y').mean(),'nps mean',A.nps_score.mean())
n=A.nps_score; print('NPS = promoters-detractors', ((n>=9).mean()-(n<=6).mean())*100)
# stage durations
for a,b in [('created_date','contacted_date'),('contacted_date','needs_assessed_date'),('needs_assessed_date','quote_accepted_date'),('quote_accepted_date','kyc_complete_date'),('kyc_complete_date','activated_date')]:
    d=(L[b]-L[a]).dt.days; print(a,'->',b,'all mean',round(d.mean(),2),'median',d.median(),'| activated mean',round(d[L.act==1].mean(),2))
L.to_pickle('L.pkl')
