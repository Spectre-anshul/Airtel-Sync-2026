import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
R=json.load(open('recovery.json')); R['Only wanted a mobile plan'][2]=0
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete']
segs=['Micro retail & services','Professional offices','Small multi-site businesses','Small manufacturers']
lead_cost={'Channel partner':150,'Field sales':420,'Inbound call':160,'Referral':180,'Website form':120,'WhatsApp campaign':60}
out={}
for seg in segs:
    g=m[m.segment==seg]; a=A[A.segment==seg]
    d=dict(leads=len(g),acts=int(g.act.sum()),enter=[int((g.r>=i).sum()) for i in range(5)],passed=[int((g.r>=i+1).sum()) for i in range(5)],
      drops={k:int(((g.drop_reason==k)).sum()) for k in R},arpu=a.monthly_bundle_value_inr.mean(),churn=(a.churned_within_6_months=='Y').mean(),
      cost=int(g.acquisition_cost_inr.sum()),partner_share=(g.lead_source=='Channel partner').mean(),
      mrr=a.monthly_bundle_value_inr.sum(),days=a.days_lead_to_activation.mean(),calls=a.customer_follow_up_calls.mean(),nps=((a.nps_score>=9).mean()-(a.nps_score<=6).mean()),
      inst=((a.activated_date-a.kyc_complete_date).dt.days).mean())
    if seg in ['Micro retail & services','Professional offices']:
        d['handling_per_lead']=sum(lead_cost[s]*(2 if s=='Field sales' else 1)*n for s,n in g.lead_source.value_counts().items())/len(g)
    out[seg]=d
# assisted handling per lead: from a11 base cost minus ADV, KYC, commission
S=pd.read_csv('scenarios.csv'); 
def sim(df,lam):
    pn=[]
    for i,s in enumerate(st):
        ent=(df.r>=i).sum(); passed=(df.r>=i+1).sum(); drops=df[(df.r==i)&(df.outcome=='Dropped')]
        pn.append((passed+sum(R[x][2]*lam for x in drops.drop_reason))/ent)
    return pn
for seg in ['Small multi-site businesses','Small manufacturers']:
    g=m[m.segment==seg]; pn=sim(g,0.5); reach=np.cumprod([1]+pn); conv=reach[5]
    row=S[(S.scenario=='Base')&(S.seg==seg)].iloc[0]
    comm=len(g)*conv*(g.lead_source=='Channel partner').mean()*1.5*out[seg]['arpu']
    # note: a11 commission used partner-source conv=segment conv; same here
    h=(row.cost-len(g)*30-len(g)*reach[4]*50-comm)/len(g); out[seg]['handling_per_lead']=h
json.dump(out,open('seg_inputs.json','w'),indent=1,default=float)
for s,d in out.items(): print(s,d['leads'],d['acts'],round(d['handling_per_lead']),round(d['partner_share'],3))
