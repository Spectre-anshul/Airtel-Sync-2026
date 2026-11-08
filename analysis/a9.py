import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
from sklearn.linear_model import LogisticRegression, LinearRegression
A=pd.read_pickle('A.pkl'); m=pd.read_pickle('M3.pkl')
A['churn']=(A.churned_within_6_months=='Y').astype(int)
X=A[['customer_follow_up_calls','days_lead_to_activation']]
lr=LogisticRegression().fit(X,A.churn); print('churn coefs',lr.coef_,lr.intercept_)
lr1=LogisticRegression().fit(A[['customer_follow_up_calls']],A.churn)
for c in range(0,6): print(c,round(lr1.predict_proba([[c]])[0,1],3))
Xs=A[['customer_follow_up_calls']].copy(); Xs['customer_follow_up_calls']=1
print('pred churn all at 1 call',lr1.predict_proba(Xs)[:,1].mean(),'actual',A.churn.mean())
ln=LinearRegression().fit(A[['customer_follow_up_calls','days_lead_to_activation']],A.nps_score); print('nps coefs',ln.coef_,ln.intercept_)
Xn=A[['customer_follow_up_calls','days_lead_to_activation']].copy(); Xn['customer_follow_up_calls']=1; Xn['days_lead_to_activation']=7
pn=ln.predict(Xn); print('pred mean nps',pn.mean())
# NPS distribution shift: add delta to each score
d=pn-ln.predict(A[['customer_follow_up_calls','days_lead_to_activation']]); s=np.clip(np.round(A.nps_score+d),0,10)
print('NPS now',((A.nps_score>=9).mean()-(A.nps_score<=6).mean())*100,'-> ',((s>=9).mean()-(s<=6).mean())*100)
# Days: by segment, KYC->act install actual
A['inst']=(A.activated_date-A.kyc_complete_date).dt.days
print(A.groupby('segment').inst.mean().round(1)); print(A.groupby('segment').days_lead_to_activation.mean().round(1))
pre=A.days_lead_to_activation-A.inst; print('pre-install share',pre.sum()/A.days_lead_to_activation.sum())
# new CAC
src_lead_cost=m[m.r==0].groupby('lead_source').acquisition_cost_inr.mean()
print(src_lead_cost)
