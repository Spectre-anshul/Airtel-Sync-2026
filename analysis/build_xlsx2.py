import pandas as pd, numpy as np, json
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
wb=load_workbook('../model/tmp.xlsx')
F='Arial'; H=Font(name=F,bold=True,color='FFFFFF'); HF=PatternFill('solid',fgColor='C00000'); T=Font(name=F,bold=True,size=14,color='C00000'); B=Font(name=F,bold=True)
m=pd.read_pickle('M3.pkl'); A=pd.read_pickle('A.pkl')
ws=wb.create_sheet('Data Findings'); ws['A1']='Data Findings (computed from smb_leads.csv + registries)'; ws['A1'].font=T
ws['A2']='Static values computed in Python; source = YTL_TrackA_Udyam_Digital_Data (synthetic). Conversion = activated ÷ leads.'; ws['A2'].font=Font(name=F,italic=True)
r=4
def table(title,df,fmts):
    global r
    ws.cell(r,1,title).font=Font(name=F,bold=True,color='C00000'); r+=1
    cols=[df.index.name or '']+list(df.columns)
    for i,c in enumerate(cols):
        x=ws.cell(r,1+i,str(c)); x.font=H; x.fill=HF; x.alignment=Alignment(wrap_text=True)
    r+=1
    for idx,row in df.iterrows():
        ws.cell(r,1,str(idx)).font=Font(name=F)
        for i,c in enumerate(df.columns):
            v=row[c]; v=float(v) if isinstance(v,(np.floating,np.integer)) else v
            x=ws.cell(r,2+i,v); x.font=Font(name=F,color='0000FF'); x.number_format=fmts.get(c,'#,##0')
        r+=1
    r+=2
st=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete','Activated']
f=pd.DataFrame({'Leads reaching stage':[(m.r>=i).sum() for i in range(6)]},index=pd.Index(st,name='Stage'))
f['% of previous']=f['Leads reaching stage']/f['Leads reaching stage'].shift(1); f['Avg days in prior step (activated)']=[np.nan,1.95,2.96,4.11,3.8,4.8]
table('1. Funnel (Apr–Jun 2026)',f,{'% of previous':'0.0%','Avg days in prior step (activated)':'0.0'})
def cut(c):
    g=m.groupby(c).agg(Leads=('act','size'),Activated=('act','sum'),Spend=('acquisition_cost_inr','sum'))
    g['Conversion']=g.Activated/g.Leads; g['CAC per activation']=g.Spend/g.Activated.replace(0,np.nan)
    g['Quote-stage pass']=m.groupby(c).apply(lambda x:(x.r>=3).sum()/max((x.r>=2).sum(),1)); g['KYC-stage pass']=m.groupby(c).apply(lambda x:(x.r>=4).sum()/max((x.r>=3).sum(),1))
    return g.drop(columns='Spend')
fm={'Conversion':'0.0%','CAC per activation':'₹#,##0','Quote-stage pass':'0.0%','KYC-stage pass':'0.0%'}
table('2. By segment',cut('segment'),fm); table('3. By lead source',cut('lead_source'),fm)
m['GSTIN status']=np.where(m.has_gstin=='N','No GSTIN',m.status); table('4. By GSTIN status (registry lookup)',cut('GSTIN status'),fm)
m['Language group']=np.where(m.preferred_language.isin(['Hindi','English']),'Hindi/English','Regional (8 languages)'); table('5. By language',cut('Language group'),fm)
table('6. By city tier',cut('city_tier'),fm)
d=m[m.outcome=='Dropped'].groupby(['drop_reason']).agg(Leads=('act','size'),Stage=('stage_reached','first')).sort_values('Leads',ascending=False)
d['Share of all drops']=d.Leads/d.Leads.sum(); table('7. Drop reasons (4,632 dropped leads)',d,{'Share of all drops':'0.0%'})
A['churn']=(A.churned_within_6_months=='Y').astype(int)
c=A.groupby('customer_follow_up_calls').agg(Customers=('churn','size'),Churn6m=('churn','mean'),NPS=('nps_score',lambda s:((s>=9).mean()-(s<=6).mean())))
c.index.name='Status-chase calls'; table('8. Status chases vs churn & NPS (368 activated)',c,{'Churn6m':'0.0%','NPS':'0%'})
A['Days band']=pd.cut(A.days_lead_to_activation,[0,15,18,21,40],labels=['≤15','16–18','19–21','>21'])
c=A.groupby('Days band').agg(Customers=('churn','size'),Churn6m=('churn','mean'),NPS=('nps_score',lambda s:((s>=9).mean()-(s<=6).mean())))
table('9. Time to activate vs NPS',c,{'Churn6m':'0.0%','NPS':'0%'})
from collections import Counter
cnt=Counter(x.split(':')[1].split('(')[0] for v in A.viol for x in v)
v=pd.DataFrame({'Activations':[ (A.nviol>0).sum(), A.viol.map(lambda v:any('gst' in x for x in v)).sum(), cnt['tier'],cnt['dep'],cnt['emp'], int(A.status.isin(['Cancelled','Suspended']).sum()), (A.overlap==0).sum()]},
 index=pd.Index(['Activations breaking ≥1 catalogue rule','…sold GSTIN-only product without a valid, active GSTIN','…product not sold in that city tier (P03 1G in Tier 2)','…missing required base product (e.g. Static IP w/o fibre)','…below minimum employee count','Activated on a cancelled or suspended GSTIN (any product)','Activated customers who bought none of the products they asked about'],name='Mis-selling & compliance check'))
v['Share of 368']=v.Activations/368; table('10. Rules-engine audit of activated bundles',v,{'Share of 368':'0.0%'})
m['Existing Accel customer']=np.where(m.current_provider.fillna('').str.startswith('Accel'),'Yes','No')
ib=m.pivot_table(index='segment',columns='Existing Accel customer',values='act',aggfunc='mean'); ib.index.name='Conversion by segment'
table('12. Installed base converts ~2× in prof. offices & multi-site',ib,{'Yes':'0.0%','No':'0.0%'})
fs=m[m.lead_source=='Field sales'].groupby('segment').agg(Leads=('act','size'),Activated=('act','sum'),Spend=('acquisition_cost_inr','sum')); fs['CAC']=fs.Spend/fs.Activated; fs=fs.drop(columns='Spend'); fs.index.name='Field sales by segment'
table('13. Field sales CAC by segment (micro = ₹53k)',fs,{'CAC':'₹#,##0'})
dec=m.groupby('dec').agg(Leads=('act','size'),Activated=('act','sum')).iloc[::-1]; dec['Conversion']=dec.Activated/dec.Leads; dec['Cumulative share of activations']=dec.Activated.cumsum()/dec.Activated.sum()
dec.index=[f'Decile {10-i}' for i in range(10)]; dec.index.name='Propensity (5-fold CV, AUC 0.71)'
table('11. Propensity score – who to call',dec,{'Conversion':'0.0%','Cumulative share of activations':'0%'})
ws.column_dimensions['A'].width=62
for c in 'BCDEFG': ws.column_dimensions[c].width=17
# KYC sheet
k=wb.create_sheet('KYC Answer Key'); k['A1']='Smart KYC – our validation of the 12 specimen applicants'; k['A1'].font=T
k['A2']='Checks: OCR read, GSTIN format+checksum, GSTIN registry status, Udyam registry, name match across docs/registry, address proof ≤90 days (today = 2026-07-15), signatory vs lead contact.'; k['A2'].font=Font(name=F,italic=True)
rows=[('K01','Vindhya Tours & Travels','REJECT','GSTIN 37IHKXV5167L1ZS is CANCELLED in registry; Udyam certificate has a blank registration number (lead L00045 declares no Udyam) → likely invalid certificate','Block GSTIN-only products; offer Udyam/PAN path; route to human'),
('K02','Harmony Dental Care','PASS (auto-fix)','GST certificate scanned at an angle; after deskew all fields match registry (Active) and Udyam','Auto-deskew before OCR'),
('K03','Ganesh Woodcraft','PASS','All four documents consistent with GST (Active) and Udyam registry','—'),
('K04','Saffron Dental Care LLP','RE-CAPTURE','GST certificate too blurred to read; GSTIN unreadable','Ask for re-upload in-chat, or prefill from GSTIN lookup (L01014: 27PZSXS1936O1ZH)'),
('K05','Balaji Realty LLP','PASS (auto-fill) + authority check','MISSING DOCUMENT detected: no Udyam certificate uploaded; lead L04014 has UDYAM-KL-00-5521886 in registry. Signatory designated "Owner" for an LLP','Auto-fill Udyam from lookup; ask for designated-partner confirmation via e-sign'),
('K06','Saffron Unisex Salon','REJECT – mismatch','GSTIN on certificate 08YKZXS8189L1ZO fails checksum and differs from registry/lead 08YKZXS5189L1ZO (8↔5)','Flag possible tampering; verify via lookup + human review'),
('K07','Neelgiri Physio Clinic','REJECT – mismatch','Legal name on certificate "Prop. Shri Physio Clinic" ≠ registry "Prop. Neelgiri Physio Clinic"','Flag possible edited document'),
('K08','Green Leaf Legal Associates','PASS','OCR reads O as 0 (24X0R…); position-aware PAN rule normalises to registry 24XORXG9365M1Z3 (Active)','Normalise O/0 by GSTIN position'),
('K09','Kaveri Insurance Advisors','PASS','All consistent; bill 5 days old','—'),
('K10','Kaveri Stays LLP','HOLD – signatory mismatch','Signatory ID names Nisha Arora but the lead contact/owner is Fatima Menon; GSTIN 27QHJXK0658U1ZL matches registry (OCR read I for J – normalised)','Ask for an authorisation letter from a designated partner + Aadhaar e-sign'),
('K11','Trinity Bake House Pvt Ltd','RE-CAPTURE + authority check','Electricity bill dated 2025-10-31 = 257 days old (> 90-day rule); signatory designated "Owner" for a Pvt Ltd company','Request a recent bill; ask for a board resolution / director authorisation'),
('K12','Star Electronics','PASS','All consistent; bill 9 days old','—')]
hd=['Applicant','Business','Verdict','What our checks found','Action in journey']
for i,c in enumerate(hd):
    x=k.cell(4,1+i,c); x.font=H; x.fill=HF
for i,row in enumerate(rows):
    for j,v in enumerate(row):
        x=k.cell(5+i,1+j,v); x.font=Font(name=F,bold=(j==2)); x.alignment=Alignment(wrap_text=True,vertical='top')
k['A18']='Summary: 4 clean pass · 2 pass after auto-fix (deskew; missing Udyam auto-filled) · 2 re-capture · 4 reject/hold. 8 of 12 files flagged. Deliberately NOT checked: Udyam certificate date and major activity vs registry (they differ on all 11 certificates – generator noise; matching them would reject good applicants).'; k['A18'].font=B
for c,w in zip('ABCDE',[10,28,20,80,55]): k.column_dimensions[c].width=w
# Sources
s=wb.create_sheet('Sources'); s['A1']='External facts used in the deck (checked 8 Nov 2026)'; s['A1'].font=T
src=[('Udyam + Udyam Assist registrations: "over 7.9 crore"','IANS, 14 May 2026','https://ianslive.in/over-79-crore-enterprises-register-through-udyam-platforms--20260514141009'),
('Active GST taxpayers 1,67,14,646 at 30 Jun 2026; proprietorships 76.9%','GSTN "9 Years of GST" report','https://tutorial.gst.gov.in/offlineutilities/gst_statistics/9YearsReport.pdf'),
('DPDP Rules: consent managers from 13 Nov 2026; full obligations 13 May 2027','Legal500 / multiple law-firm notes','https://www.legal500.com/intelligence/india/privacy/dpdp-act-compliance-mandate'),
('Airtel IQ Gateway (5 Oct 2026): SMS/WhatsApp/RCS/voice + IQ Verify + silent authentication','Airtel press release','https://www.airtel.in/press-release/10-2026/airtel-business-launches-iq-gateway-indias-first-business-communications-platform-with-telco-grade-network-intelligence-for-safe-enterprise-messaging/'),
('Airtel Business revenue +11.4% YoY in Q2 FY27','INDmoney results note','https://www.indmoney.com/blog/stocks/bharti-airtel-q2-results-analysis'),
('Only 15% (~5 mn) of 30 mn formalised small businesses sell online; 15 mn SMBs on WhatsApp Business','Bain & Meta, Win with Conversations, May 2024','https://bain.com/insights/win-with-conversations'),
('Jio Business Broadband Max 801: 100 Mbps + JioAttendance/JioMeet/JioGate bundle','TelecomTalk, 13 Mar 2026','https://telecomtalk.info/jio-business-broadband-max801-plan-100mbps-smes/1005076/'),
('Vi Business ReadyForNext: ~2.5 lakh MSMEs engaged since 2022; AP MoU targets 1 lakh','TelecomTalk, 5 Aug 2026','https://telecomtalk.info/vi-business-mou-andhra-pradesh-govt-msmes/1010420/'),
('MSME base 6 crore+; segment shares 55/25/15/5','Case study (Airtel SYNC – Project Udyam Digital), Appendix A2','case PDF')]
for i,c in enumerate(['Fact','Source','Link']):
    x=s.cell(3,1+i,c); x.font=H; x.fill=HF
for i,row in enumerate(src):
    for j,v in enumerate(row): s.cell(4+i,1+j,v).font=Font(name=F)
s.column_dimensions['A'].width=80; s.column_dimensions['B'].width=40; s.column_dimensions['C'].width=90
order=['Read Me','Scorecard','Assumptions','Uplift Model','Segment Inputs','Sensitivity','Data Findings','KYC Answer Key','Sources']
wb._sheets=[wb[n] for n in order]
wb.save('../model/Udyam_Digital_Model.xlsx'); print('saved')
