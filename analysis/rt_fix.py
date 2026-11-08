import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
import statsmodels.formula.api as smf
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl'); S=pd.read_csv('scenarios.csv')
A['churn']=(A.churned_within_6_months=='Y').astype(int)
f=smf.logit('churn ~ customer_follow_up_calls + C(segment)',A).fit(disp=0); print(f.params.round(3), f.pvalues.round(3))
b=f.params['customer_follow_up_calls']
# churn if calls drop to 1 vs today, segment-controlled
X=A.copy(); p0=f.predict(X).mean(); X['customer_follow_up_calls']=1; p1=f.predict(X).mean(); X['customer_follow_up_calls']=2; p2=f.predict(X).mean()
print('pred churn today',p0,'calls=1',p1,'calls=2',p2, 'rel',p1/p0,p2/p0)
for s,g in A.groupby('segment'):
    Y=g.copy(); a=f.predict(Y).mean(); Y['customer_follow_up_calls']=1; print(s, round(a,3), round(f.predict(Y).mean(),3))
# CAC decomposition: base acts with TODAY cost structure (funnel effect only): cost scales with stage reach under today's ladder
base=S[S.scenario=='Base']; seg_acts=base.set_index('seg').acts
# today cost per lead by segment, applied to same leads => spend unchanged-ish; but more leads reach later stages -> ladder costs rise. approximate spend today (lower bound) 
tot_today=m.acquisition_cost_inr.sum(); acts_base=seg_acts['ALL']
print('CAC funnel-effect only (today spend / base acts):',tot_today/acts_base)
# partner commission rises with acts; add incremental commission
print('installed base:'); m['accel']=m.current_provider.fillna('NA').str.startswith('Accel')
print(m.groupby(['segment','accel']).act.agg(['size','mean']).round(3).unstack())
print(m.groupby('accel').act.agg(['size','mean']))
fs=m[(m.lead_source=='Field sales')]
print(fs.groupby('segment').apply(lambda g: pd.Series({'leads':len(g),'acts':g.act.sum(),'cac':g.acquisition_cost_inr.sum()/max(g.act.sum(),1)})).round(0))
mic=m[m.segment=='Micro retail & services']; print('micro spend median',mic.monthly_telecom_spend_inr.median())
print('cancelled/suspended activations',((m.status.isin(['Cancelled','Suspended']))&(m.act==1)).sum())
print('<40L no gst', (m[m.annual_turnover_band=='< 40 lakh'].has_gstin=='N').mean(), m[(m.annual_turnover_band=='< 40 lakh')&(m.has_gstin=='N')].act.mean())
