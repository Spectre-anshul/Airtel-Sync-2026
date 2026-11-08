import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',260)
m=pd.read_pickle('M2.pkl')
# speed to contact
m['d_contact']=(m.contacted_date-m.created_date).dt.days
c=m[m.r>=1]
print(c.groupby('d_contact').agg(n=('act','size'),conv=('act','mean'),needs=('r',lambda x:(x>=2).mean())).to_string())
m['d_quote']=(m.quote_accepted_date-m.needs_assessed_date).dt.days
q=m[m.r>=3]; print(q.groupby('d_quote').agg(n=('act','size'),conv=('act','mean'),kyc=('r',lambda x:(x>=4).mean())).to_string())
m['d_kyc']=(m.kyc_complete_date-m.quote_accepted_date).dt.days
k=m[m.r>=4]; print(k.groupby('d_kyc').agg(n=('act','size'),conv=('act','mean')).to_string())
print(k.groupby('has_gstin').d_kyc.mean(), k.groupby('has_udyam').d_kyc.mean())
m['d_inst']=(m.activated_date-m.kyc_complete_date).dt.days
print(m[m.act==1].groupby('city_tier').d_inst.mean())
# GST effect within segment
print(m.pivot_table(index='segment',columns='has_gstin',values='act',aggfunc='mean').round(3))
print(m.pivot_table(index='segment',columns='has_gstin',values='act',aggfunc='size'))
# logistic model
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, cross_val_predict
X=pd.get_dummies(m[['lead_source','segment','preferred_language','annual_turnover_band','current_internet','current_provider','contact_role']].fillna('NA'),drop_first=True)
X['tier2']=(m.city_tier==2).astype(int); X['gst']=(m.has_gstin=='Y').astype(int); X['udyam']=(m.has_udyam=='Y').astype(int)
X['gst_bad']=m.status.isin(['Cancelled','Suspended']).astype(int)
X['log_emp']=np.log1p(m.employee_count); X['sites']=m.num_sites; X['log_spend']=np.log1p(m.monthly_telecom_spend_inr); X['npoi']=m.npoi; X['any_inel']=m.any_inel.astype(int)
y=m.act
lr=LogisticRegression(max_iter=3000,C=1.0)
print('LR AUC',cross_val_score(lr,X,y,cv=5,scoring='roc_auc').mean())
gb=GradientBoostingClassifier(random_state=0,max_depth=3,n_estimators=200,learning_rate=0.05)
print('GB AUC',cross_val_score(gb,X,y,cv=5,scoring='roc_auc').mean())
lr.fit(X,y); co=pd.Series(lr.coef_[0],X.columns).sort_values(); print(np.exp(co).round(2).to_string())
p=cross_val_predict(gb,X,y,cv=5,method='predict_proba')[:,1]; m['score']=p
m['dec']=pd.qcut(m.score,10,labels=False)
t=m.groupby('dec').agg(n=('act','size'),act=('act','sum'),conv=('act','mean'),cac=('acquisition_cost_inr','sum')).iloc[::-1]
t['cum_act_share']=t.act.cumsum()/t.act.sum(); t['cum_lead_share']=t.n.cumsum()/t.n.sum(); print(t.round(3).to_string())
m.to_pickle('M3.pkl')
