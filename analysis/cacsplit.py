import pandas as pd, numpy as np, json
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
R=json.load(open('recovery.json')); R['Only wanted a mobile plan'][2]=0
lad={'Field sales':[420,840,2690,3360,4030],'Channel partner':[150,300,600,750,900]}
lc={'Inbound call':160,'Referral':180,'Website form':120,'WhatsApp campaign':60}
def ladder(s): return lad.get(s,[lc.get(s,0)*k for k in [1,2,4,5,6]])
tot=0; acts=0
for seg,g in m.groupby('segment'):
    pn=[]
    for i in range(5):
        ent=(g.r>=i).sum(); passed=(g.r>=i+1).sum(); d=g[(g.r==i)&(g.outcome=='Dropped')]
        pn.append((passed+sum(R[x][2]*0.5 for x in d.drop_reason))/ent)
    reach=np.cumprod([1]+pn); conv=reach[5]; arpu=A[A.segment==seg].monthly_bundle_value_inr.mean()
    for src,gs in g.groupby('lead_source'):
        L=ladder(src); n=len(gs)
        c=n*sum(L[k]*(reach[k]-reach[k+1]) for k in range(5))+n*reach[5]*L[4]
        if src=='Channel partner': c+=n*conv*1.5*arpu
        tot+=c
    acts+=len(g)*conv
print('Base: today cost structure on new funnel -> spend',round(tot),'acts',round(acts),'CAC',round(tot/acts))
