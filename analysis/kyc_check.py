import pandas as pd, re
G=pd.read_csv('../data/mock_gstin_registry.csv').set_index('gstin'); U=pd.read_csv('../data/mock_udyam_registry.csv').set_index('udyam_number')
L=pd.read_csv('../data/smb_leads.csv')
CH='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
def gst_ok(g):
    if not re.fullmatch(r'\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]',g): return 'bad format'
    s=0
    for i,c in enumerate(g[:14]):
        v=CH.index(c)*(1 if i%2==0 else 2); s+=v//36+v%36
    return 'ok' if CH[(36-s%36)%36]==g[14] else f'bad checksum (expected {CH[(36-s%36)%36]})'
docs={ # values transcribed from OCR + visual (K02 rotated, K04 blurred)
'K01':dict(gstin='37IHKXV5167L1ZS',udyam=None,name='Vindhya Tours & Travels',sig='Neha Kaur',bill='2026-06-26',sigvalid='2028-03-26'),
'K02':dict(gstin='19EOGXH4115Y1ZL',udyam='UDYAM-WB-00-5053330',name='Harmony Dental Care',sig='Joseph Shah',bill='2026-05-22',sigvalid='2028-09-10'),
'K03':dict(gstin='27XUIXG0767D1ZP',udyam='UDYAM-MH-00-9516696',name='Ganesh Woodcraft',sig='Joseph Singh',bill='2026-05-30',sigvalid='2028-07-04'),
'K04':dict(gstin='27PZSXS1936D1ZH',udyam='UDYAM-MH-00-6131836',name='Saffron Dental Care LLP',sig='Fatima Pillai',bill='2026-05-28',sigvalid='2028-08-03'),
'K05':dict(gstin='32TZAXB5481U1Z1',udyam=None,name='Balaji Realty LLP',sig='Anita Shah',bill='2026-06-11',sigvalid='2029-09-11'),
'K06':dict(gstin='08YKZXS8189L1Z0',udyam='UDYAM-RJ-00-6577157',name='Saffron Unisex Salon',sig='Pooja Shah',bill='2026-06-11',sigvalid='2028-09-15'),
'K07':dict(gstin='07CPCXN0398P1ZT',udyam='UDYAM-DL-00-9565547',name='Neelgiri Physio Clinic',sig='Neha Banerjee',bill='2026-07-05',sigvalid='2030-05-05'),
'K08':dict(gstin='24X0RXG9365M1Z3',udyam='UDYAM-GJ-00-8477445',name='Green Leaf Legal Associates',sig='Joseph Rao',bill='2026-05-26',sigvalid='2027-09-18'),
'K09':dict(gstin='37LDYXK0296F1ZB',udyam='UDYAM-AP-00-9751562',name='Kaveri Insurance Advisors',sig='Anita Kulkarni',bill='2026-07-10',sigvalid='2027-12-22'),
'K10':dict(gstin='27QHIXK0658U1ZL',udyam='UDYAM-MH-00-7183141',name='Kaveri Stays LLP',sig='Nisha Arora',bill='2026-06-18',sigvalid='2029-06-01'),
'K11':dict(gstin='03KGZXT1320R1ZZ',udyam='UDYAM-PB-00-9719478',name='Trinity Bake House Pvt Ltd',sig='Vikram Pillai',bill='2025-10-31',sigvalid='2028-12-23'),
'K12':dict(gstin='37NBLXS1145E1ZU',udyam='UDYAM-AP-00-5186772',name='Star Electronics',sig='Pooja Agarwal',bill='2026-07-06',sigvalid='2029-03-03'),
}
today=pd.Timestamp('2026-07-15')
for k,d in docs.items():
    g=d['gstin']; alts=[g, g.replace('O','0'), g.replace('0','O')]
    found=[a for a in dict.fromkeys(alts) if a in G.index]
    out=[f"fmt:{gst_ok(g)}"]
    if found:
        r=G.loc[found[0]]; out+= [f"reg:{found[0]} {r.status}", f"legal:{r.legal_name}", f"trade:{r.trade_name}", f"addr:{r.principal_place_of_business}"]
    else: out.append('GSTIN NOT IN REGISTRY')
    if d['udyam']:
        if d['udyam'] in U.index: u=U.loc[d['udyam']]; out.append(f"udyam ok: {u.enterprise_name}|{u.enterprise_type}|{u.major_activity}|{u.nic_description}|{u.city}")
        else: out.append('UDYAM NOT IN REGISTRY')
    else: out.append('udyam missing')
    age=(today-pd.Timestamp(d['bill'])).days; out.append(f'bill age {age}d')
    ld=L[L.business_name==d['name']][['lead_id','city','gstin','udyam_number','contact_name','contact_role','has_udyam','stage_reached']]
    out.append('leads:'+ld.to_string(header=False,index=False))
    print('=====',k,d['name'],'| sig',d['sig']); print('\n  '.join(out))
