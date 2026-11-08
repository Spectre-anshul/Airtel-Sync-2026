import pandas as pd, numpy as np, json, warnings; warnings.filterwarnings('ignore')
pd.set_option('display.width',250)
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete']
# recovery assumptions by drop reason: (component, conservative, base, upside)
R={
'Unreachable after 3 attempts':('WhatsApp-first advisor, async reply',0.15,0.30,0.40),
'Wrong or invalid number':('OTP / silent-auth at lead capture',0.0,0.0,0.0),  # removed at source, not recovered (lead was junk)
'Not interested on first call':('Advisor shows priced bundle in 1st chat',0.05,0.10,0.15),
'Owner had no time for a visit':('No visit needed: advisor on phone',0.35,0.50,0.65),
'Visit not scheduled by sales':('No visit needed: advisor on phone',0.50,0.70,0.80),
'Locked in with current provider':('(not addressed)',0,0,0),
'Only wanted a mobile plan':('Sell single plan instantly (P07/P08)',0.20,0.40,0.60),
'Price too high':('Right-sized starter bundles + toggles',0.10,0.20,0.30),
'Competitor offered cheaper plan':('Right-sized starter bundles + toggles',0.05,0.15,0.20),
'Quote too complex to understand':('Plain-language single monthly price',0.50,0.70,0.80),
'Quote took too long to arrive':('Instant quote',0.70,0.85,0.90),
'Decided to wait':('Saved quote + WhatsApp nudge',0.05,0.10,0.20),
'Missing GST or Udyam document':('Registry lookup replaces upload',0.40,0.60,0.70),
'Found paperwork too long':('Smart KYC: lookup+OCR+DigiLocker',0.50,0.70,0.80),
'Document details did not match':('Real-time OCR mismatch prompt',0.30,0.50,0.60),
'Authorised signatory not available':('Remote e-sign (Aadhaar eSign)',0.40,0.60,0.70),
'Installation delayed beyond 21 days':('Install-slot promise + tracker',0.30,0.50,0.60),
'Customer cancelled before install':('Tracker + proactive updates',0.20,0.30,0.40),
'Site not feasible for fibre':('Pre-check + 5G FWA (P04) fallback',0.40,0.60,0.70),
'First payment failed':('UPI Autopay retry',0.40,0.60,0.70),
}
def simulate(df,col):
    cur=len(df); rows=[]
    for i,s in enumerate(st):
        ent=(df.r>=i).sum(); passed=(df.r>=i+1).sum(); drops=df[(df.r==i)&(df.outcome=='Dropped')]
        rec=sum(R[d][col] for d in drops.drop_reason)
        # junk numbers removed from denominator at Lead stage (they never were real leads)
        rows.append(dict(stage=s,enter=ent,pass_base=passed/ent,pass_new=min((passed+rec)/ent,1.0),rec=rec))
    T=pd.DataFrame(rows)
    base=T.pass_base.prod(); new=T.pass_new.prod()
    return T,base,new
for col,name in [(1,'cons'),(2,'base'),(3,'up')]:
    T,b,n=simulate(m,col); print(name,'conv',round(b*100,2),'->',round(n*100,2),'x',round(n/b,2),'acts',round(5000*n))
T,b,n=simulate(m,2); print(T.round(3).to_string())
for s,g in m.groupby('segment'):
    T,b,n=simulate(g,2); print(s,round(b*100,2),'->',round(n*100,2), round(len(g)*n))
# OTP effect: remove 319 wrong numbers from lead base -> conversion on verified leads
print('conv excluding wrong numbers', 368/(5000-319))
json.dump({k:list(v) for k,v in R.items()},open('recovery.json','w'),indent=1)
print('---- scaled scenarios (lambda x base rates; mobile-only excluded)')
R['Only wanted a mobile plan']=(R['Only wanted a mobile plan'][0],0,0,0)
base_rates={k:v[2] for k,v in R.items()}
def sim2(df,lam):
    rows=[]
    for i,s in enumerate(st):
        ent=(df.r>=i).sum(); passed=(df.r>=i+1).sum(); drops=df[(df.r==i)&(df.outcome=='Dropped')]
        rec=sum(base_rates[d]*lam for d in drops.drop_reason)
        rows.append(dict(stage=s,pb=passed/ent,pn=(passed+rec)/ent))
    T=pd.DataFrame(rows); return T,T.pb.prod(),T.pn.prod()
for lam in [0.3,0.4,0.5,0.6,0.8,1.0]:
    T,b,n=sim2(m,lam); print(lam,round(n*100,2),round(n/b,2),round(5000*n))
T,b,n=sim2(m,0.5); print(T.round(3))
for s,g in m.groupby('segment'):
    T,b,n=sim2(g,0.5); print(s,round(b*100,2),'->',round(n*100,2), round(len(g)*n))
