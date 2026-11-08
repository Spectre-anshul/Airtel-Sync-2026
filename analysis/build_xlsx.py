import json, pandas as pd, numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.comments import Comment
R=json.load(open('recovery.json')); R['Only wanted a mobile plan'][2]=0
SI=json.load(open('seg_inputs.json'))
segs=['Micro retail & services','Professional offices','Small multi-site businesses','Small manufacturers']
short=['Micro','Prof. offices','Multi-site','Manufacturers']
stages=['Lead','Contacted','Needs assessed','Quote accepted','KYC complete']
stage_of={'Not interested on first call':0,'Unreachable after 3 attempts':0,'Wrong or invalid number':0,
'Locked in with current provider':1,'Only wanted a mobile plan':1,'Owner had no time for a visit':1,'Visit not scheduled by sales':1,
'Competitor offered cheaper plan':2,'Decided to wait':2,'Price too high':2,'Quote too complex to understand':2,'Quote took too long to arrive':2,
'Authorised signatory not available':3,'Document details did not match':3,'Found paperwork too long':3,'Missing GST or Udyam document':3,
'Customer cancelled before install':4,'First payment failed':4,'Installation delayed beyond 21 days':4,'Site not feasible for fibre':4}
F='Arial'; BLUE=Font(name=F,color='0000FF'); BLK=Font(name=F); GRN=Font(name=F,color='008000'); B=Font(name=F,bold=True)
H=Font(name=F,bold=True,color='FFFFFF'); HF=PatternFill('solid',fgColor='C00000'); YF=PatternFill('solid',fgColor='FFFF00'); GF=PatternFill('solid',fgColor='F2F2F2')
T=Font(name=F,bold=True,size=14,color='C00000')
INR='₹#,##0;(₹#,##0);-'; PCT='0.0%;(0.0%);-'; NUM='#,##0;(#,##0);-'; X='0.0x'
wb=Workbook()
def sheet(name,title,sub):
    ws=wb.create_sheet(name); ws['A1']=title; ws['A1'].font=T; ws['A2']=sub; ws['A2'].font=Font(name=F,italic=True,color='595959'); return ws
def hdr(ws,row,vals,col=1):
    for i,v in enumerate(vals):
        c=ws.cell(row,col+i,v); c.font=H; c.fill=HF; c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True)
def put(ws,ref,val,font=BLK,fmt=None,fill=None,comment=None):
    c=ws[ref]; c.value=val; c.font=font
    if fmt: c.number_format=fmt
    if fill: c.fill=fill
    if comment: c.comment=Comment(comment,'model')
    return c
wb.remove(wb.active)
# ---------------- README
ws=sheet('Read Me','Project Udyam Digital – Impact & Unit-Economics Model','Accel Business · built from smb_leads.csv (5,000 leads, Apr–Jun 2026, synthetic) · all ₹')
lines=['HOW TO USE',
'1. Edit only BLUE cells on the Assumptions sheet (yellow fill = key levers). Everything else recalculates.',
'2. Uplift Model rebuilds each segment funnel stage by stage: new pass rate = (leads that passed + recovered drops × scenario factor) ÷ leads entering the stage.',
'3. Recovered drops = drops at that stage, by drop_reason, × the share each solution component wins back (Assumptions, col C).',
'4. Scorecard compares today vs three scenarios. Sensitivity shows conversion and CAC across scenario factors.',
'5. Data Findings and KYC Answer Key hold the computed evidence used in the deck (static values computed in Python from the CSVs).',
'','COLOUR CODE','Blue = hardcoded input · Black = formula · Green = link to another sheet · Yellow fill = key assumption',
'','KEY CAVEATS',
'• Data is one synthetic quarter for 22 Tier-1/2 cities; results scale linearly with lead volume, not with India TAM.',
'• Recovery rates are judgement-based and haircut by a scenario factor (Conservative 0.3 / Base 0.5 / Upside 1.0).',
'• "Only wanted a mobile plan" drops are excluded from recovery (they are a separate single-SIM sale, not a bundle).',
'• Contribution margin 40% is an assumption (no cost data in the pack); see sensitivity.',
'• Churn effect rests on the observed link between status-chase calls and 6-month churn (5.9% at 1 call vs 27.9% at 5).']
for i,l in enumerate(lines): ws.cell(4+i,1,l).font=B if l.isupper() else BLK
ws.column_dimensions['A'].width=130
# ---------------- Assumptions
ws=sheet('Assumptions','Assumptions & Scenario Levers','Blue = input. Recovery % = share of leads lost to that reason that the new journey wins back at full effect (factor 1.0).')
hdr(ws,4,['Drop reason','Stage lost (0=Lead…4=KYC)','Recovery at full effect','Solution component that fixes it'])
r0=5
for i,(k,v) in enumerate(R.items()):
    r=r0+i; put(ws,f'A{r}',k); put(ws,f'B{r}',stage_of[k],BLUE); put(ws,f'C{r}',v[2],BLUE,PCT); put(ws,f'D{r}',v[0])
RN=r0+len(R)-1
r=RN+3; hdr(ws,r,['Scenario lever','Conservative','Base','Upside','Note'])
lev=[('Scenario factor (× recovery)',0.3,0.5,1.0,PCT,'Haircut applied to every recovery rate. Base = half of full effect.'),
('6-month churn multiplier vs today',0.85,0.72,0.54,PCT,'Segment-controlled logit (churn ~ chase calls + segment; +0.33 log-odds per call, p=0.014): calls 3.0→2 gives ×0.72 (Base); →1 gives ×0.54 (Upside).'),]
for j,(n,a,b,c,f,note) in enumerate(lev):
    rr=r+1+j; put(ws,f'A{rr}',n); 
    for col,v in zip('BCD',(a,b,c)): put(ws,f'{col}{rr}',v,BLUE,f,YF)
    put(ws,f'E{rr}',note)
LAM=r+1; CHM=r+2
r=CHM+2; hdr(ws,r,['Unit-cost input','Value','Note'])
units=[('GenAI advisor cost per lead (₹)',30,INR,'LLM tokens + WhatsApp/RCS conversation charges; assumption'),
('Smart KYC cost per KYC attempt (₹)',50,INR,'GSTIN + Udyam lookup, OCR, e-sign API calls; assumption'),
('Partner commission (× monthly bundle value)',1.5,'0.0x','Derived from data: partner cost on activated leads = ₹900 + 1.5 × MRR (r=0.99999)'),
('Contribution margin on bundle revenue',0.40,PCT,'Assumption – no cost data in pack; tested 30–50% in Sensitivity'),
('LTV horizon (months)',36,'0','Capped at 3 years'),
('Leads per quarter in pack',5000,NUM,'smb_leads.csv'),]
for j,(n,v,f,note) in enumerate(units):
    rr=r+1+j; put(ws,f'A{rr}',n); put(ws,f'B{rr}',v,BLUE,f,YF if j in (3,) else None); put(ws,f'C{rr}',note)
ADV,KYC,COM,GM,HZ=[f'Assumptions!$B${r+1+j}' for j in range(5)]
ws.column_dimensions['A'].width=44; ws.column_dimensions['B'].width=16; ws.column_dimensions['C'].width=16; ws.column_dimensions['D'].width=16; ws.column_dimensions['E'].width=90
# ---------------- Segment inputs
wsI=sheet('Segment Inputs','Baseline per segment (computed from smb_leads.csv)','Blue values are computed from the dataset in Python and pasted as inputs.')
rows=[('Leads','leads',NUM),('Activations','acts',NUM),('Baseline acquisition spend (₹)','cost',INR),('Avg monthly bundle value, activated (₹)','arpu',INR),
('6-month churn, activated','churn',PCT),('Share of leads from channel partners','partner_share',PCT),('Digital handling cost per lead (₹)','handling_per_lead',INR),
('Avg days lead→activation','days','0.0'),('Avg status-chase calls','calls','0.0'),('NPS (promoters − detractors)','nps',PCT),('KYC→activation days (install)','inst','0.0')]
hdr(wsI,4,['Metric']+short+['All / note'])
for i,(n,k,f) in enumerate(rows):
    rr=5+i; put(wsI,f'A{rr}',n)
    for j,s in enumerate(segs): put(wsI,f'{CL(2+j)}{rr}',SI[s][k],BLUE,f)
notes={'Digital handling cost per lead (₹)':'Micro/Prof: lead-source media cost (field reps ×2 for intro). Multi-site/Mfg: assisted-digital — field/partner stage ladder at Base funnel reach.',
'Share of leads from channel partners':'Partners keep earning commission on activations in their territory'}
for i,(n,k,f) in enumerate(rows):
    if n in notes: put(wsI,f'F{5+i}',notes[n])
put(wsI,'F5','=SUM(B5:E5)'); put(wsI,'F6','=SUM(B6:E6)'); put(wsI,'F7','=SUM(B7:E7)',fmt=INR)
put(wsI,'F8','=SUMPRODUCT(B6:E6,B8:E8)/F6',fmt=INR)
wsI.column_dimensions['A'].width=42
for c in 'BCDE': wsI.column_dimensions[c].width=16
wsI.column_dimensions['F'].width=80
# drop counts table
hdr(wsI,18,['Drop reason','Stage']+short)
for i,k in enumerate(R):
    rr=19+i; put(wsI,f'A{rr}',f'=Assumptions!A{r0+i}',GRN); put(wsI,f'B{rr}',f'=Assumptions!B{r0+i}',GRN)
    for j,s in enumerate(segs): put(wsI,f'{CL(3+j)}{rr}',SI[s]['drops'][k],BLUE,NUM)
DR0,DR1=19,19+len(R)-1
hdr(wsI,DR1+2,['Stage funnel','Stage']+short)
for k in range(5):
    rr=DR1+3+k; put(wsI,f'A{rr}',f'Entering: {stages[k]}'); put(wsI,f'B{rr}',k)
    for j,s in enumerate(segs): put(wsI,f'{CL(3+j)}{rr}',SI[s]['enter'][k],BLUE,NUM)
    rr2=DR1+8+k; put(wsI,f'A{rr2}',f'Passed: {stages[k]}'); put(wsI,f'B{rr2}',k)
    for j,s in enumerate(segs): put(wsI,f'{CL(3+j)}{rr2}',SI[s]['passed'][k],BLUE,NUM)
EN0=DR1+3; PS0=DR1+8
# ---------------- Uplift model
wsU=sheet('Uplift Model','Funnel uplift by segment and scenario','New pass rate = (passed + scenario factor × Σ drops × recovery) ÷ entering. Conversion = product of the five pass rates.')
row=4; res={}
for j,s in enumerate(segs):
    col=CL(3+j)
    wsU.cell(row,1,s).font=Font(name=F,bold=True,color='C00000'); row+=1
    hdr(wsU,row,['Stage','Entering','Passed today','Recoverable drops (full)','Pass rate today','Conservative','Base','Upside']); row+=1
    first=row
    for k in range(5):
        put(wsU,f'A{row}',stages[k])
        put(wsU,f'B{row}',f"='Segment Inputs'!{col}{EN0+k}",GRN,NUM)
        put(wsU,f'C{row}',f"='Segment Inputs'!{col}{PS0+k}",GRN,NUM)
        put(wsU,f'D{row}',f"=SUMPRODUCT(('Segment Inputs'!$B${DR0}:$B${DR1}={k})*'Segment Inputs'!{col}{DR0}:{col}{DR1}*Assumptions!$C${r0}:$C${RN})",fmt='#,##0.0')
        put(wsU,f'E{row}',f'=C{row}/B{row}',fmt=PCT)
        for sc,cc in zip('FGH','BCD'):
            put(wsU,f'{sc}{row}',f'=MIN(1,(C{row}+Assumptions!${cc}${LAM}*D{row})/B{row})',fmt=PCT)
        row+=1
    last=row-1
    put(wsU,f'A{row}','Lead → activation',B)
    for c in 'EFGH': put(wsU,f'{c}{row}',f'=PRODUCT({c}{first}:{c}{last})',Font(name=F,bold=True),PCT)
    res[s]=dict(conv=row,first=first)
    row+=3
for c,w in zip('ABCDEFGH',[30,12,13,22,15,14,14,14]): wsU.column_dimensions[c].width=w
# ---------------- Scorecard
wsS=sheet('Scorecard','Scorecard: today vs scenarios (one quarter, 5,000 leads)','CAC = acquisition spend ÷ activations. LTV = ARPU × margin × Σ survival over horizon.')
hdr(wsS,4,['Segment','Metric','Today','Conservative','Base','Upside'])
r=5; tot_rows={}
metrics=['Lead→activation','Activations','New MRR from cohort (₹/month)','Acquisition spend (₹)','CAC per activation (₹)','6-month churn','LTV per customer (₹)','LTV / CAC','CAC payback (months)']
for j,s in enumerate(segs):
    col=CL(2+j); cr=res[s]['conv']; fr=res[s]['first']
    blk=r
    for i,mname in enumerate(metrics):
        put(wsS,f'A{r+i}',short[j] if i==0 else ''); put(wsS,f'B{r+i}',mname)
    leads=f"'Segment Inputs'!{col}5"; arpu=f"'Segment Inputs'!{col}8"; ch=f"'Segment Inputs'!{col}9"; ps=f"'Segment Inputs'!{col}10"; hd=f"'Segment Inputs'!{col}11"
    # Today
    put(wsS,f'C{r}',f"='Uplift Model'!E{cr}",GRN,PCT); put(wsS,f'C{r+1}',f"='Segment Inputs'!{col}6",GRN,NUM)
    put(wsS,f'C{r+2}',f'=C{r+1}*{arpu}',fmt=INR); put(wsS,f'C{r+3}',f"='Segment Inputs'!{col}7",GRN,INR)
    put(wsS,f'C{r+5}',f'={ch}',GRN,PCT)
    for sc,uc,lc in zip('DEF','FGH','BCD'):
        put(wsS,f'{sc}{r}',f"='Uplift Model'!{uc}{cr}",GRN,PCT)
        put(wsS,f'{sc}{r+1}',f'={leads}*{sc}{r}',fmt=NUM)
        put(wsS,f'{sc}{r+2}',f'={sc}{r+1}*{arpu}',fmt=INR)
        kyc_reach=f"PRODUCT('Uplift Model'!{uc}{fr}:{uc}{fr+3})"
        put(wsS,f'{sc}{r+3}',f'={leads}*({hd}+{ADV})+{leads}*{kyc_reach}*{KYC}+{sc}{r+1}*{ps}*{COM}*{arpu}',fmt=INR)
        put(wsS,f'{sc}{r+5}',f'={ch}*Assumptions!{lc}${CHM}',fmt=PCT)
    for sc in 'CDEF':
        put(wsS,f'{sc}{r+4}',f'=IFERROR({sc}{r+3}/{sc}{r+1},0)',fmt=INR)
        mc=f'(1-(1-{sc}{r+5})^(1/6))'
        put(wsS,f'{sc}{r+6}',f'={arpu}*{GM}*(1-(1-{mc})^{HZ})/{mc}',fmt=INR)
        put(wsS,f'{sc}{r+7}',f'=IFERROR({sc}{r+6}/{sc}{r+4},0)',fmt=X)
        put(wsS,f'{sc}{r+8}',f'=IFERROR({sc}{r+4}/({arpu}*{GM}),0)',fmt='0.0')
    tot_rows[s]=blk; r+=len(metrics)+1
# totals
put(wsS,f'A{r}','ALL SEGMENTS',B)
for i,mname in enumerate(['Lead→activation','Activations','New MRR from cohort (₹/month)','Acquisition spend (₹)','CAC per activation (₹)','Annualised new ARR at this run-rate (₹ cr)','Δ activations vs today','Δ CAC vs today','Retained ARR after 6-mo churn (₹ cr)','CAC if only the funnel improves (today cost structure, Base)']):
    put(wsS,f'B{r+i}',mname)
for sc in 'CDEF':
    put(wsS,f'{sc}{r+1}','='+'+'.join(f'{sc}{tot_rows[s]+1}' for s in segs),fmt=NUM)
    put(wsS,f'{sc}{r}',f"={sc}{r+1}/Assumptions!$B${LAM+9}",fmt=PCT)
    put(wsS,f'{sc}{r+2}','='+'+'.join(f'{sc}{tot_rows[s]+2}' for s in segs),fmt=INR)
    put(wsS,f'{sc}{r+3}','='+'+'.join(f'{sc}{tot_rows[s]+3}' for s in segs),fmt=INR)
    put(wsS,f'{sc}{r+4}',f'={sc}{r+3}/{sc}{r+1}',fmt=INR)
    put(wsS,f'{sc}{r+5}',f'={sc}{r+2}*12*4/10^7',fmt='₹0.0 "cr"')
    put(wsS,f'{sc}{r+6}',f'={sc}{r+1}/$C{r+1}-1',fmt=PCT)
    put(wsS,f'{sc}{r+7}',f'={sc}{r+4}/$C{r+4}-1',fmt=PCT)
    w='+'.join(f'{sc}{tot_rows[s]+2}*(1-{sc}{tot_rows[s]+5})' for s in segs)
    put(wsS,f'{sc}{r+8}',f'=({w})*12*4/10^7',fmt='₹0.0 "cr"')
put(wsS,f'E{r+9}',9856,BLUE,INR,comment='Python: today\'s per-stage cost ladders + partner commission applied to the Base funnel. CAC bridge: ₹15,053 → ₹9,856 (funnel effect, −35%) → ₹7,143 (digital cost mix, −18 pts).')
TOT=r
for c,w in zip('ABCDEF',[16,40,16,16,16,16]): wsS.column_dimensions[c].width=w
wsS.freeze_panes='C5'
# --------------- Sensitivity
wsN=sheet('Sensitivity','Sensitivity: blended conversion & CAC vs scenario factor; LTV/CAC vs margin','Recomputed with closed-form funnel per segment.')
hdr(wsN,4,['Scenario factor']+short+['Blended conversion','Activations'])
lams=[0.2,0.3,0.4,0.5,0.6,0.8,1.0]
for i,l in enumerate(lams):
    rr=5+i; put(wsN,f'A{rr}',l,BLUE,PCT)
    for j,s in enumerate(segs):
        fr=res[s]['first']; parts='*'.join(f"MIN(1,('Uplift Model'!C{fr+k}+$A{rr}*'Uplift Model'!D{fr+k})/'Uplift Model'!B{fr+k})" for k in range(5))
        put(wsN,f'{CL(2+j)}{rr}',f'={parts}',fmt=PCT)
    put(wsN,f'G{rr}',"=SUMPRODUCT(B{0}:E{0},'Segment Inputs'!$B$5:$E$5)".format(rr),fmt=NUM)
    put(wsN,f'F{rr}',f"=G{rr}/'Segment Inputs'!$F$5",fmt=PCT)
hdr(wsN,14,['Contribution margin']+[f'LTV/CAC Base – {x}' for x in short])
for i,gm in enumerate([0.3,0.35,0.4,0.45,0.5]):
    rr=15+i; put(wsN,f'A{rr}',gm,BLUE,PCT)
    for j,s in enumerate(segs):
        b=tot_rows[s]; put(wsN,f'{CL(2+j)}{rr}',f"=Scorecard!E{b+7}*$A{rr}/{GM}",fmt=X)
for c in 'ABCDEFG': wsN.column_dimensions[c].width=20
wb.save('../model/tmp.xlsx'); json.dump({'TOT':TOT,'tot_rows':tot_rows,'res':res},open('xl_map.json','w'))
print('ok')
