import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',250)
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
R=json.load(open('recovery.json')); R['Only wanted a mobile plan'][2]=0
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete']
ADV=30; KYC=50; GM=0.40; H=36
def sim(df,lam):
    pn=[]
    for i,s in enumerate(st):
        ent=(df.r>=i).sum(); passed=(df.r>=i+1).sum(); drops=df[(df.r==i)&(df.outcome=='Dropped')]
        rec=sum(R[d][2]*lam for d in drops.drop_reason); pn.append((passed+rec)/ent if ent else 0)
    return np.prod(pn), pn
lead_cost={'Channel partner':150,'Field sales':420,'Inbound call':160,'Referral':180,'Website form':120,'WhatsApp campaign':60}
assisted=['Small multi-site businesses','Small manufacturers']
out=[]
for lam,name in [(0.3,'Conservative'),(0.5,'Base'),(1.0,'Upside')]:
    rows=[]
    for seg,g in m.groupby('segment'):
        conv,pn=sim(g,lam); acts=len(g)*conv
        arpu=A[A.segment==seg].monthly_bundle_value_inr.mean()
        # reach probabilities under new funnel
        reach=np.cumprod([1]+pn)  # P(reach stage k)
        cost=0
        for src,gs in g.groupby('lead_source'):
            n=len(gs); share_act=n*conv
            if seg in assisted:
                # keep today's per-lead cost profile but scale stage reach to new funnel (assisted-digital) + digital tooling
                ladder={'Field sales':[420,840,2690,3360,4030],'Channel partner':[150,300,600,750,900]}.get(src,[lead_cost[src]*k for k in [1,2,4,5,6]])
                c=n*sum(ladder[k]*(reach[k]-reach[k+1]) for k in range(5)) + n*reach[5]*ladder[4]
            else:
                base=lead_cost[src]*(2 if src=='Field sales' else 1)  # field rep still sources + introduces
                c=n*(base) 
            c+= n*ADV + n*reach[4]*KYC
            if src=='Channel partner': c+= share_act*1.5*arpu
            cost+=c
        churn_now=(A[A.segment==seg].churned_within_6_months=='Y').mean()
        churn_new=churn_now*0.5 if name!='Conservative' else churn_now*0.7
        if name=='Upside': churn_new=churn_now*0.45
        mc=1-(1-churn_new)**(1/6); ltv=sum(arpu*GM*(1-mc)**t for t in range(H))
        rows.append(dict(scenario=name,seg=seg,leads=len(g),conv=conv,acts=acts,arpu=arpu,mrr=acts*arpu,cost=cost,cac=cost/acts,churn6=churn_new,ltv=ltv,ltv_cac=ltv/(cost/acts)))
    D=pd.DataFrame(rows); tot=dict(scenario=name,seg='ALL',leads=D.leads.sum(),acts=D.acts.sum(),mrr=D.mrr.sum(),cost=D.cost.sum())
    tot['conv']=tot['acts']/tot['leads']; tot['cac']=tot['cost']/tot['acts']; tot['arpu']=tot['mrr']/tot['acts']
    D=pd.concat([D,pd.DataFrame([tot])]); out.append(D)
O=pd.concat(out); print(O.round(3).to_string())
O.to_csv('scenarios.csv',index=False)
# baseline
b=m.groupby('segment').agg(leads=('act','size'),acts=('act','sum'),cost=('acquisition_cost_inr','sum'))
print(b, b.cost.sum()/b.acts.sum(), A.monthly_bundle_value_inr.sum())
