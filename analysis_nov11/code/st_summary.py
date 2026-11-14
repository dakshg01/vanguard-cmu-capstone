import sys,pandas as pd,numpy as np
from scipy import stats
S=sys.argv[1]; w=pd.read_csv(f'{S}/out/strategic_tactical_by_fund.csv')
rows=[]
for kind,lab in [('rate','Rate (duration + curve)'),('cred','Credit spread')]:
    for lay in ['strategic','tactical']:
        for wn in ['W1','W2']:
            x=w[f'{kind}_{lay}_pp_{wn}'].dropna(); rows.append(dict(source=lab,layer=lay,window=wn,funds=len(x),mean_pp_per_yr=round(x.mean(),2),median_pp_per_yr=round(x.median(),2),sd_across_funds=round(x.std(),2),share_positive=round((x>0).mean(),2)))
s1=pd.DataFrame(rows); rows=[]
for col in ['rate_strategic_pp','rate_tactical_pp','cred_strategic_pp','cred_tactical_pp','mean_duration_yrs','mean_credit_dur_yrs','duration_sd_yrs','curve_sd_yrs','credit_sd_yrs','rate_hit_rate','cred_hit_rate']:
    x=w[[f'{col}_W1',f'{col}_W2']].dropna(); c,p=stats.spearmanr(x.iloc[:,0],x.iloc[:,1]); rows.append(dict(measure=col,funds=len(x),rho_W1_vs_W2=round(c,2),p=round(p,3)))
s2=pd.DataFrame(rows); rows=[]
for kind in ['rate','cred']:
    for wn in ['W1','W2']:
        x=w[f'{kind}_hit_rate_{wn}'].dropna(); rows.append(dict(source=kind,window=wn,funds=len(x),mean_hit_rate=round(x.mean(),3),share_funds_above_50pct=round((x>.5).mean(),2)))
s3=pd.DataFrame(rows)
notes=['Exposures: filed N-PORT rate sensitivity by tenor (3M,1Y,5Y,10Y,30Y; economic sign from Anna panel) and IG+HY spread duration, screened for implausible filings.',
 'P&L (pp/month) = -exposure(years) x change in Fed zero-coupon yield at the tenor (bp)/100; credit = -(IG+HY spread duration) x change in Baa-10Y spread. Carry and security selection are excluded.',
 'Exposure at a report date is applied to returns in the following months until the next report (reports older than 130 days are skipped). Windows 2019-07..2022-12 and 2023-01..2026-06; min 8 in-window reports. A report from the prior window can carry into the first months of the next. The first months of W1 (before N-PORT starts) cannot be attributed.',
 'Strategic = P&L from the window-average exposure; tactical = P&L from deviations around it. Tactical is a within-fund measure, so family conventions matter less; strategic credit levels are still not comparable across families.',
 'Tactical success = share of report periods (about 3 months each) with positive tactical P&L.','Across-fund t-statistics treat funds as independent; they share market moves, so they overstate significance.',
 'Single credit factor (Baa spread) is applied to HY as well. Columbia and the four return-flagged funds are excluded.',
 'Verified: attributed rate P&L correlates 0.87 (median across funds) with actual monthly fund returns; strategic rate P&L reproduced independently over identical months (-4.02 vs -4.10 in W1).']
with pd.ExcelWriter(f'{S}/out/strategic_tactical.xlsx') as xw:
    s1.to_excel(xw,'pnl_by_layer',index=False); s2.to_excel(xw,'persistence',index=False); s3.to_excel(xw,'tactical_success',index=False); w.to_excel(xw,'by_fund',index=False); pd.DataFrame({'note':notes}).to_excel(xw,'notes',index=False)
print(s2.to_string(index=False))
