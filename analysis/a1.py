import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',50)
L=pd.read_csv('../data/smb_leads.csv',parse_dates=['created_date','contacted_date','needs_assessed_date','quote_accepted_date','kyc_complete_date','activated_date'])
print(L.dtypes.to_string())
for c in ['lead_source','business_type','segment','city_tier','preferred_language','annual_turnover_band','has_gstin','has_udyam','current_internet','current_provider','contact_role','stage_reached','outcome','drop_reason','churned_within_6_months']:
    print('\n--',c); print(L[c].value_counts(dropna=False).to_string())
print(L.describe().T.to_string())
