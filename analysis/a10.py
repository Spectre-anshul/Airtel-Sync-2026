import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
pa=m[(m.lead_source=='Channel partner')&(m.act==1)]
print('partner act cost vs MRR corr',np.corrcoef(pa.acquisition_cost_inr,pa.monthly_bundle_value_inr)[0,1], (pa.acquisition_cost_inr/pa.monthly_bundle_value_inr).describe())
fa=m[(m.lead_source=='Field sales')]
print(fa.groupby('stage_reached').acquisition_cost_inr.describe()[['mean','min','max']])
print(m[m.act==1].groupby('lead_source').apply(lambda g:(g.acquisition_cost_inr/g.monthly_bundle_value_inr).median()))
