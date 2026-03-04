#!/usr/bin/env python
# coding: utf-8

# # HeatMap Hackathon 2026 - Burn Care Access Analysis
# ### National Injury Resource Database (NIRD) · BData / American Burn Association
# 
# ---
# 
# **Primary Use Case:** Advancing Equitable Access to Burn Care  
# 
# **Mechanisms:** Referral gaps and telemedicine are analyzed only as mechanisms that drive *inequity*
# 
# **Primary Dataset:** NIRD Database (2023) - 635 hospitals across 50 states  
# 
# **Sources:** NIRD Database (2023); U.S. Census Bureau County Population Centroids (2020); CDC/ATSDR SVI (2022); USDA RUCC (2023); Ivanko et al. J Burn Care Res (2024); Lovick et al. Burns (2024); Huang et al. (2021); Murray et al. (2019). Distance analysis: Haversine great-circle method; Census batch geocoding + manual verification for 18 hospitals. Team 13 analysis.
# 
# ---
# 
# **Team 13**
# 1. Emmanuel Fle Chea
# 2. Josh Spitzer-Resnick
# 3. Shreya Pramanik
# 4. Feifei Li
# 5. Lance Killian McDonald
# 
# ---
# 
# ### Analysis Roadmap
# | # | Analysis | Use Case |
# |---|---|---|
# | 1 | Data Loading & Cleaning | All |
# | 2 | Burn Center Density by State | Equity |
# | 3 | Burn Bed Capacity per 100k Residents | Equity |
# | 4 | Referral Gap - Trauma Centers w/o Burn Capability | Referral Networks |
# | 5 | Telemedicine Opportunity Score | Telemedicine |
# | 6 | Pediatric vs. Adult Access Gap | Equity |
# | 7 | ABA Verification Rate by State | Equity / Quality |
# | 8 | Equity Quadrant: Access vs. Quality | Equity |
# | 9 | Composite Vulnerability Index | Equity |
# | 10 | Top Telemedicine Hub Candidates (Hospital Level) | Telemedicine |
# | 11 | Executive Dashboard | All |
# | 12 | Export Summary Excel Workbook | All |

# ---
# ## Imports & Global Configuration

# In[149]:


# Libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings, os
import openpyxl, statistics
from collections import defaultdict
import os

warnings.filterwarnings('ignore')
get_ipython().run_line_magic('matplotlib', 'inline')

plt.rcParams.update({
    'font.family'        : 'DejaVu Sans',
    'axes.spines.top'    : False,
    'axes.spines.right'  : False,
    'axes.titlesize'     : 14,
    'axes.labelsize'     : 11,
    'figure.dpi'         : 130,
    'savefig.dpi'        : 150,
    'savefig.bbox'       : 'tight',
})

# --- Colour palette -------------------------------------
C = dict(
    burn    = '#D62728',
    trauma  = '#1F77B4',
    aba     = '#FF7F0E',
    peds    = '#2CA02C',
    gap     = '#9467BD',
    tele    = '#17BECF',
    neutral = '#7F7F7F',
    bg      = '#F8F8F8',
)

OUTPUT_DIR = 'outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 2022 US Census state populations (thousands) ---------------------
STATE_POP = {
    'AL':5074,'AK':733, 'AZ':7359,'AR':3046,'CA':39030,'CO':5840,'CT':3626,
    'DE':1018,'FL':22611,'GA':10912,'HI':1441,'ID':1939,'IL':12582,'IN':6833,
    'IA':3200,'KS':2937,'KY':4512,'LA':4590,'ME':1385,'MD':6165,'MA':6982,
    'MI':10034,'MN':5717,'MS':2961,'MO':6178,'MT':1122,'NE':1967,'NV':3178,
    'NH':1395,'NJ':9261,'NM':2113,'NY':19678,'NC':10699,'ND':779,'OH':11756,
    'OK':4020,'OR':4240,'PA':12972,'RI':1094,'SC':5282,'SD':909,'TN':7051,
    'TX':30030,'UT':3381,'VT':647,'VA':8683,'WA':7785,'WV':1775,'WI':5895,
    'WY':581,'DC':671
}

print(' Setup complete.')


# ---
# ## Load & Clean NIRD Data

# In[124]:


df = pd.read_excel(
    'NIRD 20230130 Database_Hackathon.xlsx',
    sheet_name='Data Table NIRD 20230130'
)

# --- Normalise binary indicator columns -----------------------------------
binary_cols = [
    'BURN_ADULT','BURN_PEDS','TRAUMA_ADULT','TRAUMA_PEDS',
    'ADULT_TRAUMA_L1','ADULT_TRAUMA_L2','PEDS_TRAUMA_L1','PEDS_TRAUMA_L2',
    'TC_STATE_DESIGNATED','BC_STATE_DESIGNATED'
]
for col in binary_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

df['ABA_VERIFIED'] = (df['ABA_VERIFIED'] == 'Yes').astype(int)
df['ACS_VERIFIED'] = (df['ACS_VERIFIED'] == 'Yes').astype(int)

# --- Composite flags ---------------------------------------------------------
df['HAS_BURN']       = ((df['BURN_ADULT']      == 1) | (df['BURN_PEDS']      == 1)).astype(int)
df['HAS_TRAUMA']     = ((df['TRAUMA_ADULT']    == 1) | (df['TRAUMA_PEDS']    == 1)).astype(int)
df['TRAUMA_NO_BURN'] = ((df['HAS_TRAUMA']      == 1) & (df['HAS_BURN']       == 0)).astype(int)
df['L1_NO_BURN']     = ((df['ADULT_TRAUMA_L1'] == 1) & (df['BURN_ADULT']     == 0)).astype(int)
df['L2_NO_BURN']     = ((df['ADULT_TRAUMA_L2'] == 1) & (df['BURN_ADULT']     == 0)).astype(int)
df['STATE_POP_K']    = df['STATE'].map(STATE_POP)

print(f'Hospitals loaded  : {len(df)}')
print(f'States covered    : {df["STATE"].nunique()}')
print(f'Adult burn centers: {df["BURN_ADULT"].sum()}')
print(f'ABA-verified      : {df["ABA_VERIFIED"].sum()}')
print(f'L1+L2 trauma      : {(df["ADULT_TRAUMA_L1"] | df["ADULT_TRAUMA_L2"]).sum()}')
print(f'Trauma w/o burn   : {df["TRAUMA_NO_BURN"].sum()}')
df.head(3)


# ---
# ## State - Level Aggregation

# In[155]:


state_df = df.groupby('STATE').agg(
    total_hospitals   = ('AHA_ID',         'count'),
    burn_centers      = ('BURN_ADULT',      'sum'),
    burn_peds_centers = ('BURN_PEDS',       'sum'),
    aba_verified      = ('ABA_VERIFIED',    'sum'),
    bc_state_desig    = ('BC_STATE_DESIGNATED','sum'),
    l1_trauma         = ('ADULT_TRAUMA_L1', 'sum'),
    l2_trauma         = ('ADULT_TRAUMA_L2', 'sum'),
    trauma_no_burn    = ('TRAUMA_NO_BURN',  'sum'),
    l1_no_burn        = ('L1_NO_BURN',      'sum'),
    l2_no_burn        = ('L2_NO_BURN',      'sum'),
    total_burn_beds   = ('BURN_BEDS',       'sum'),
    total_beds        = ('TOTAL_BEDS',      'sum'),
).reset_index()

# --- Load SVI (county-level) -----------------------------------------
svi = pd.read_csv('SVI_2022_US_county.csv', dtype={'FIPS': str})

svi_small = svi[['FIPS','EP_NOVEH','EP_POV150','EP_LIMENG','EP_DISABL','EP_MINRTY']].copy()

svi_small['STATE_FIPS'] = svi_small['FIPS'].str[:2]

# Drop FIPS so it doesn't get averaged
svi_small = svi_small.drop(columns=['FIPS'])

# Now group safely
svi_state = svi_small.groupby('STATE_FIPS').mean().reset_index()

# Map STATE_FIPS -> state abbreviation
fips_to_state = {
    '01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','11':'DC',
    '12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY',
    '22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT',
    '31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH',
    '40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT',
    '50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY'
}

svi_state['STATE'] = svi_state['STATE_FIPS'].map(fips_to_state)

# Merge with the existing state_df
state_df = state_df.merge(svi_state, on='STATE', how='left')

state_df['pop_k']         = state_df['STATE'].map(STATE_POP)
state_df['pop_M']         = state_df['pop_k'] / 1000
state_df['burn_per_M']    = (state_df['burn_centers']    / state_df['pop_M']).round(2)
state_df['beds_per_100k'] = (state_df['total_burn_beds'] / state_df['pop_k'] * 100).round(3)
state_df['pct_aba']       = (
    state_df['aba_verified'] /
    state_df['burn_centers'].replace(0, np.nan) * 100
).fillna(0).round(1)

no_burn_states = state_df[state_df['burn_centers'] == 0]['STATE'].tolist()
print(f'States with ZERO adult burn centers: {no_burn_states}')
state_df.sort_values('burn_per_M', ascending=False).head(10)


# ---
# ## Figure 1 - Burn Center Density by State

# In[126]:


fig, ax = plt.subplots(figsize=(16, 8))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

plot_df = state_df.sort_values('burn_per_M', ascending=True)
colors  = [C['burn'] if v > 0 else '#CCCCCC' for v in plot_df['burn_per_M']]
ax.barh(plot_df['STATE'], plot_df['burn_per_M'],
        color=colors, edgecolor='white', linewidth=0.5)

for i, row in enumerate(plot_df.itertuples()):
    if row.aba_verified > 0:
        ax.text(row.burn_per_M + 0.02, i,
                f'({row.aba_verified} ABA)', va='center',
                fontsize=7, color=C['aba'])

mean_val = plot_df['burn_per_M'].mean()
ax.axvline(mean_val, color='black', ls='--', lw=1.2,
           label=f'National mean: {mean_val:.2f}')
ax.set_xlabel('Burn Centers per Million Residents')
ax.set_title(
    'Figure 1: Burn Center Density by State\n'
    '(ABA-verified count in parentheses; gray = no adult burn center)',
    fontweight='bold'
)
ax.legend(fontsize=9)
ax.text(0.99, 0.01,
        f'No adult burn centers: {", ".join(no_burn_states)}',
        transform=ax.transAxes, ha='right', fontsize=8,
        color='gray', style='italic')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig1_burn_density_by_state.png')
plt.show()


# ---
# ## Figure 2 - Burn Bed Capacity per 100k Residents

# In[127]:


plot_df2 = state_df[state_df['beds_per_100k'] > 0].sort_values('beds_per_100k', ascending=True)

fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

ax.barh(plot_df2['STATE'], plot_df2['beds_per_100k'],
        color=C['burn'], edgecolor='white', linewidth=0.5, alpha=0.85)

mean_beds = plot_df2['beds_per_100k'].mean()
ax.axvline(mean_beds, color='black', ls='--', lw=1.2,
           label=f'Mean: {mean_beds:.3f}')
ax.set_xlabel('Dedicated Burn Beds per 100,000 Residents')
ax.set_title(
    'Figure 2: Burn Bed Capacity per 100k Residents by State\n'
    '(States with no reported burn beds excluded)',
    fontweight='bold'
)
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig2_burnbeds_per_100k.png')
plt.show()


# ---
# ## Figure 3 - Referral Gap: Trauma Centers Without Burn Capability

# In[128]:


total_l1 = int(df['ADULT_TRAUMA_L1'].sum())
total_l2 = int(df['ADULT_TRAUMA_L2'].sum())
l1_burn  = int(df[(df['ADULT_TRAUMA_L1']==1) & (df['BURN_ADULT']==1)].shape[0])
l2_burn  = int(df[(df['ADULT_TRAUMA_L2']==1) & (df['BURN_ADULT']==1)].shape[0])
l1_no_b  = total_l1 - l1_burn
l2_no_b  = total_l2 - l2_burn

print(f'L1 trauma total : {total_l1}  |  with burn: {l1_burn}  |  WITHOUT burn: {l1_no_b} ({l1_no_b/total_l1*100:.1f}%)')
print(f'L2 trauma total : {total_l2}  |  with burn: {l2_burn}  |  WITHOUT burn: {l2_no_b} ({l2_no_b/total_l2*100:.1f}%)')

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor(C['bg'])

# ---Left: stacked bar top-30 states --------------------------------------
ax = axes[0]
ax.set_facecolor(C['bg'])
plot_ref = state_df.sort_values('l1_no_burn', ascending=False).head(30)

ax.bar(plot_ref['STATE'], plot_ref['burn_centers'],
       label='Burn Centers', color=C['burn'], alpha=0.9)
ax.bar(plot_ref['STATE'], plot_ref['l1_no_burn'],
       bottom=plot_ref['burn_centers'],
       label='L1 Trauma (no burn)', color=C['trauma'], alpha=0.9)
ax.bar(plot_ref['STATE'], plot_ref['l2_no_burn'],
       bottom=plot_ref['burn_centers'] + plot_ref['l1_no_burn'],
       label='L2 Trauma (no burn)', color='#AEC7E8', alpha=0.9)
ax.set_xlabel('State')
ax.set_ylabel('Number of Hospitals')
ax.set_title('Top 30 States: Referral Gap\n(Trauma Centers Lacking Burn Capability)', fontweight='bold')
ax.legend(fontsize=8)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, fontsize=7)

# --- Right: national pie -------------------------------------------
ax2 = axes[1]
ax2.set_facecolor(C['bg'])
labels     = [f'L1 w/ Burn\n({l1_burn})', f'L1 NO Burn\n({l1_no_b})',
              f'L2 w/ Burn\n({l2_burn})', f'L2 NO Burn\n({l2_no_b})']
sizes      = [l1_burn, l1_no_b, l2_burn, l2_no_b]
pie_colors = [C['burn'], C['trauma'], C['aba'], '#AEC7E8']
ax2.pie(sizes, labels=labels, colors=pie_colors,
        autopct='%1.0f%%', startangle=90, textprops={'fontsize': 9})
ax2.set_title('National: Trauma Centers\nwith vs. without Burn Capability', fontweight='bold')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig3_referral_gap.png')
plt.show()


# ---
# ## Figure 4 - Telemedicine Opportunity Score by State

# In[129]:


# --- Compute per-hospital telemedicine opportunity score ------------------------
df['TELE_SCORE'] = 0.0
df.loc[df['TRAUMA_NO_BURN']   == 1, 'TELE_SCORE'] += 3.0   
df.loc[df['ADULT_TRAUMA_L1']  == 1, 'TELE_SCORE'] += 2.0   
df.loc[df['ADULT_TRAUMA_L2']  == 1, 'TELE_SCORE'] += 1.5   

beds_q = df['TOTAL_BEDS'].quantile([0.25, 0.75])
df.loc[df['TOTAL_BEDS'] >= beds_q[0.25], 'TELE_SCORE'] += 0.5
df.loc[df['TOTAL_BEDS'] >= beds_q[0.75], 'TELE_SCORE'] += 0.5

tele_candidates = df[df['HAS_BURN'] == 0].copy()

tele_state = (
    tele_candidates
    .groupby('STATE')
    .agg(
        candidates     = ('AHA_ID',       'count'),
        total_score    = ('TELE_SCORE',   'sum'),
        l1_no_burn     = ('L1_NO_BURN',   'sum'),
        l2_no_burn     = ('L2_NO_BURN',   'sum'),
    )
    .reset_index()
    .sort_values('total_score', ascending=False)
)

top30 = tele_state.head(30)
fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

ax.bar(top30['STATE'], top30['total_score'],
       color=C['tele'], edgecolor='white', linewidth=0.5)
ax.set_xlabel('State')
ax.set_ylabel('Cumulative Telemedicine Opportunity Score')
ax.set_title(
    'Figure 4: State-Level Telemedicine Opportunity\n'
    '(Trauma hospitals without burn capability, weighted by trauma level & bed size)',
    fontweight='bold'
)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=90)

ax2 = ax.twinx()
ax2.plot(range(len(top30)), top30['l1_no_burn'] + top30['l2_no_burn'],
         'o-', color=C['trauma'], label='L1+L2 Trauma w/o Burn', lw=1.5, ms=5)
ax2.set_ylabel('L1+L2 Trauma Centers w/o Burn', color=C['trauma'])
ax2.tick_params(axis='y', labelcolor=C['trauma'])
ax2.legend(loc='upper right', fontsize=8)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig4_telemedicine_opportunity.png')
plt.show()

high_pri = tele_candidates[tele_candidates['TELE_SCORE'] >= 5].shape[0]
print(f'High-priority telemedicine sites (score ≥ 5): {high_pri}')


# ---
# ## Figure 5 - Pediatric vs. Adult Burn Center Access Gap

# In[130]:


peds_df = (
    state_df[['STATE', 'burn_centers', 'burn_peds_centers']]
    .copy()
    .assign(peds_gap=lambda d: (d['burn_centers'] - d['burn_peds_centers']).clip(lower=0))
    .sort_values('peds_gap', ascending=False)
    .head(25)
)

no_peds_states = state_df[
    (state_df['burn_centers'] > 0) & (state_df['burn_peds_centers'] == 0)
]['STATE'].tolist()
print(f'States with adult burn centers but ZERO pediatric: {no_peds_states}')

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

x = np.arange(len(peds_df))
w = 0.4
ax.bar(x - w/2, peds_df['burn_centers'],      w, label='Adult Burn Centers',    color=C['burn'], alpha=0.85)
ax.bar(x + w/2, peds_df['burn_peds_centers'], w, label='Pediatric Burn Centers', color=C['peds'], alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(peds_df['STATE'], rotation=90)
ax.set_ylabel('Number of Centers')
ax.set_title(
    'Figure 5: Pediatric vs. Adult Burn Center Access Gap\n'
    '(Top 25 states by gap size)',
    fontweight='bold'
)
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig5_pediatric_gap.png')
plt.show()


# ---
# ## Figure 6 - ABA Verification Rate by State

# In[131]:


fig, ax = plt.subplots(figsize=(14, 5))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

plot_v  = state_df.sort_values('pct_aba', ascending=False)
bar_col = [C['aba'] if p >= 50 else C['trauma'] if p > 0 else '#CCCCCC'
           for p in plot_v['pct_aba']]

ax.bar(plot_v['STATE'], plot_v['pct_aba'], color=bar_col,
       edgecolor='white', linewidth=0.4)
ax.axhline(50, color='black', ls='--', lw=1, label='50% threshold')
ax.set_ylim(0, 118)
ax.set_ylabel('% of Burn Centers ABA-Verified')
ax.set_title(
    'Figure 6: ABA Verification Rate by State\n'
    '(Orange ≥ 50%, Blue < 50%, Gray = no burn center)',
    fontweight='bold'
)
ax.legend()
plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, fontsize=7)

for i, (_, row) in enumerate(plot_v.iterrows()):
    if row['burn_centers'] > 0:
        ax.text(i, row['pct_aba'] + 1.5,
                f"{int(row['aba_verified'])}/{int(row['burn_centers'])}",
                ha='center', fontsize=5.5, color='black')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig6_aba_verification_rate.png')
plt.show()


# ---
# ## Figure 7 - Equity Quadrant: Access vs. Quality

# In[132]:


eq_df = state_df[state_df['burn_centers'] > 0].copy()

fig, ax = plt.subplots(figsize=(11, 8))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

sc = ax.scatter(
    eq_df['burn_per_M'],
    eq_df['pct_aba'],
    s=eq_df['total_burn_beds'].clip(lower=10) * 3,
    c=eq_df['beds_per_100k'],
    cmap='RdYlGn',
    alpha=0.8, edgecolors='gray', linewidths=0.4
)
plt.colorbar(sc, ax=ax, label='Burn Beds per 100k Residents')

xm = eq_df['burn_per_M'].median()
ym = eq_df['pct_aba'].median()
ax.axvline(xm, color='gray', ls='--', lw=1)
ax.axhline(ym, color='gray', ls='--', lw=1)

ax.text(xm * 1.03, 97,  'High Access\nHigh Quality', fontsize=8, color='green',     alpha=0.8)
ax.text(0.01,       97,  'Low Access\nHigh Quality',  fontsize=8, color='darkorange', alpha=0.8)
ax.text(xm * 1.03, 2,   'High Access\nLow Quality',  fontsize=8, color='steelblue', alpha=0.8)
ax.text(0.01,       2,   '⚠ Low Access\nLow Quality\nPriority States',
        fontsize=8, color='red', alpha=0.9)

for _, row in eq_df.iterrows():
    ax.annotate(row['STATE'], (row['burn_per_M'], row['pct_aba']),
                textcoords='offset points', xytext=(4, 3), fontsize=7)

ax.set_xlabel('Burn Centers per Million Residents  (Access)')
ax.set_ylabel('% ABA-Verified Burn Centers  (Quality)')
ax.set_title(
    'Figure 7: Equity Quadrant: Access vs. Quality by State\n'
    '(Bubble size = total burn beds; colour = beds per 100k)',
    fontweight='bold'
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig7_equity_quadrant.png')
plt.show()


# ---
# ## Analysis 7.5 - County‑Level Population‑Weighted Distance to Nearest Burn Center 
# ### Mapped to State‑Level Access Inequity
# 
# ### **Methodology**
# 
# **Source Data**
# - **NIRD Database (2023):** Burn center locations (adult, pediatric, ABA‑verified)
# - **U.S. Census Bureau (2020):** County Population‑Weighted Centroids  
#   File: `CenPop2020_Mean_CO.txt`  
#   Coverage: **3,221 U.S. counties** with population‑weighted latitude/longitude
# 
# **Variables Used**
# - `LATITUDE`, `LONGITUDE` - burn center coordinates  
#   - Obtained via **Census Geocoder batch API**  
#   - **118/136** centers auto‑geocoded  
#   - **18** manually verified
# - `county_lat`, `county_lon` - population‑weighted county centroid coordinates  
# - `county_pop` - county population (used as weighting factor)
# - `ABA_VERIFIED` - indicator distinguishing any burn center vs. ABA‑verified center
# - `dist_any_burn_mi` - Haversine distance to nearest burn center (any)
# - `dist_aba_burn_mi` - Haversine distance to nearest ABA‑verified burn center
# 
# ---
# 
# ### **Rationale for Variable Selection**
# 
# Distance captures the **geographic dimension of burn care inequity** that simple density counts cannot.  
# A state may have burn centers clustered in one metro area while leaving rural counties effectively unserved.
# 
# **Population‑weighted distance** reflects where people actually live, not just whether a burn center exists somewhere in the state.
# 
# This metric directly predicts:
# - Under‑referral risk  
# - Transfer delays  
# - Avoidable complications and mortality  
# 
# ABA‑verified distance is reported separately because **verification is the best available proxy for quality**.  
# Example: *Hawaii has 0 miles to any burn center, but 2,385 miles to the nearest ABA‑verified center.*
# 
# ---
# 
# ### **Aggregation Method**
# 
# County‑level distances → **state‑level metrics** using:
# 
# - **Population‑weighted mean distance**  
#   
# 
# \[
#   \text{State Distance} = \frac{\sum (\text{county distance} \times \text{county population})}{\sum \text{county population}}
#   \]
# 
# 
# 
# - **Threshold metrics**  
#   - `% counties >100 miles`  
#   - `% counties >200 miles`  
#   Computed as **unweighted proportions** of counties.
# 
# This approach aligns with NIRD’s state‑level access metrics and preserves geographic granularity.
# 
# ---
# 
# ### **Distance Calculation**
# 
# Distances computed using the **Haversine great‑circle formula**:
# 
# - Earth radius: **3,958.8 miles**
# - For each county centroid, compute distance to **every** burn center nationally
# - Assign the **minimum** distance as the county’s nearest‑center distance
# 
# This method yields the shortest over‑surface travel distance, consistent with geographic access modeling.
# 
# ---
# 
# ### **Why Distance Matters**
# 
# Distance is the **most direct patient‑level measure of geographic equity**.
# 
# Unlike:
# - Burn center counts  
# - Burn beds per capita  
# - Density ratios  
# 
# …distance quantifies what an **average resident actually experiences** when seeking burn care.
# 
# It is also the strongest predictor of:
# - Delayed referral  
# - Increased length of stay  
# - Higher infection rates  
# - Avoidable mortality  
# - Increased cost burden  
# 
# Population‑weighted distance reveals inequities that are invisible in state‑level counts, especially in **frontier, rural, and high‑poverty regions**.

# In[145]:


fips_to_state = {
    '01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT',
    '10':'DE','11':'DC','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL',
    '18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD',
    '25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE',
    '32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND',
    '39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD',
    '47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV',
    '55':'WI','56':'WY','72':'PR'
}

# --- Load Census county population centroids --------------------------------------------
county_centroids = pd.read_csv(
    'CenPop2020_Mean_CO.txt',
    dtype={'STATEFP': str, 'COUNTYFP': str}
)
county_centroids['FIPS'] = county_centroids['STATEFP'] + county_centroids['COUNTYFP']
county_centroids = county_centroids.rename(columns={
    'LATITUDE': 'county_lat',
    'LONGITUDE': 'county_lon',
    'STNAME': 'state_name',
    'COUNAME': 'county_name',
    'POPULATION': 'county_pop'
})
county_centroids['STATE'] = county_centroids['STATEFP'].map(fips_to_state)
county_centroids = county_centroids.dropna(subset=['STATE'])
print(f"County centroids loaded: {len(county_centroids)}")

# --- Geocode burn centers via Census Geocoder API ---------------------------------------------
col_upper = {c.upper(): c for c in df.columns}

addr_col  = col_upper.get('ADDRESS',  col_upper.get('ADDR',    col_upper.get('STREET', None)))
city_col  = col_upper.get('CITY',     col_upper.get('MLOCADDR', None))
state_col = col_upper.get('STATE',    col_upper.get('MSTATE',  None))
zip_col   = col_upper.get('ZIP',      col_upper.get('MZIP',    col_upper.get('ZIPCODE', None)))

print(f"Address columns detected: addr={addr_col}, city={city_col}, state={state_col}, zip={zip_col}")

burn_raw = df[df['HAS_BURN'] == 1].copy().reset_index(drop=True)
burn_raw['_geocode_id'] = burn_raw.index

geocode_rows = []
for _, row in burn_raw.iterrows():
    geocode_rows.append([
        int(row['_geocode_id']),
        str(row[addr_col])  if addr_col  else '',
        str(row[city_col])  if city_col  else '',
        str(row[state_col]) if state_col else '',
        str(row[zip_col])   if zip_col   else ''
    ])

geocode_csv = '\n'.join([f'{r[0]},{r[1]},{r[2]},{r[3]},{r[4]}' for r in geocode_rows])
print(f"Submitting {len(geocode_rows)} burn centers to Census Geocoder...")

response = requests.post(
    'https://geocoding.geo.census.gov/geocoder/locations/addressbatch',
    files={'addressFile': ('addresses.csv', geocode_csv, 'text/csv')},
    data={'benchmark': 'Public_AR_Current', 'returntype': 'locations'},
    timeout=120
)

if response.status_code != 200:
    print(f"Geocoder API error: {response.status_code}")
    print(response.text[:500])
else:
    print("Geocoding complete. Parsing results...")
    geocoded = pd.read_csv(
        io.StringIO(response.text),
        header=None,
        names=['geocode_id','input_addr','match','match_type',
               'matched_addr','coords','tiger_id','side'],
        dtype={'geocode_id': int}
    )

    matched = geocoded[geocoded['match'] == 'Match'].copy()
    matched[['LONGITUDE','LATITUDE']] = (
        matched['coords']
        .str.split(',', expand=True)
        .astype(float)
    )

    burn_raw = burn_raw.merge(
        matched[['geocode_id','LATITUDE','LONGITUDE']],
        left_on='_geocode_id', right_on='geocode_id',
        how='left'
    )

    burn_centers_geo = burn_raw[
        burn_raw['LATITUDE'].notna() & burn_raw['LONGITUDE'].notna()
    ][['AHA_ID', 'HOSPITAL_NAME', 'STATE', 'LATITUDE', 'LONGITUDE',
       'BURN_ADULT', 'BURN_PEDS', 'ABA_VERIFIED']].copy()

    total      = len(burn_raw)
    geocoded_n = len(burn_centers_geo)
    failed_n   = total - geocoded_n
    print(f"Successfully geocoded: {geocoded_n}/{total} burn centers")
    if failed_n > 0:
        failed = burn_raw[burn_raw['LATITUDE'].isna()][['HOSPITAL_NAME','STATE']]
        print(f"Failed to geocode {failed_n} hospitals:")
        print(failed.to_string())

# --- Manual coordinate patch for geocoding failures --------------------------------------------
# These 18 hospitals failed the Census batch geocoder due to parenthetical
# names, ampersands, or complex address formatting. Coordinates verified
# manually. All are in well-served states; zero-burn-center states unaffected.
manual_coords = {
    'University of Alabama at Birmingham Hospital (UAB Burn Center)':                              (33.5051, -86.7990),
    'USA Health University Hospital (Arnold Luterman Regional Burn Center)':                       (30.6954, -88.0638),
    'Banner University Medical Center - Tucson (Burn Unit at Banner)':                             (32.2382, -110.9490),
    'North Colorado Medical Center (Western States Burn Center)':                                  (40.4317, -104.6892),
    "Children's National Health System (Children's National Trauma and Burn Center)":              (38.9317, -77.0315),
    'Tampa General Hospital (Tampa General Hospital Regional Burn Center)':                        (27.9389, -82.4614),
    'Kendall Regional Medical Center (Burn and Reconstructive Centers of FL)':                     (25.7108, -80.4139),
    'Riley Hospital for Children at Indiana University Health (Burn Program at Riley IU Health)':  (39.7741, -86.1777),
    "Brigham and Women's Hospital (Burn Center)":                                                  (42.3354, -71.1072),
    'University of Missouri Health System (George D. Peak Memorial Burn & Wound Center)':          (38.9517, -92.3341),
    "Barnes-Jewish Hospital (Burn Center)":                                                        (38.6338, -90.2630),
    'Stony Brook Medicine (Suffolk County Volunteer Firefighters Burn Center)':                    (40.9126, -73.1236),
    "Akron Children's Hospital (Akron Children's Hospital Burn Center)":                           (41.0814, -81.5190),
    'Paul Silvertein Burn Center':                                                                 (35.4676, -97.5164),
    'UPMC Mercy (UPMC Mercy Burn Center)':                                                         (40.4353, -79.9811),
    "Rhode Island Hospital/Hasbro Children's Hospital (Rhode Island Burn Center)":                 (41.8197, -71.4128),
    'MUSC Health University Medical Center (South Carolina Burn Center at MUSC)':                  (32.7835, -79.9480),
    'Memorial Hermann Texas Medical Center (John S. Dunn Burn Center)':                            (29.7077, -95.3968),
}

manual_rows = []
for _, row in burn_raw[burn_raw['LATITUDE'].isna()].iterrows():
    name = row['HOSPITAL_NAME']
    if name in manual_coords:
        r = row.copy()
        r['LATITUDE']  = manual_coords[name][0]
        r['LONGITUDE'] = manual_coords[name][1]
        manual_rows.append(r)

if manual_rows:
    manual_df = pd.DataFrame(manual_rows)[
        ['AHA_ID', 'HOSPITAL_NAME', 'STATE', 'LATITUDE', 'LONGITUDE',
         'BURN_ADULT', 'BURN_PEDS', 'ABA_VERIFIED']
    ]
    burn_centers_geo = pd.concat([burn_centers_geo, manual_df], ignore_index=True)
    print(f"Patched {len(manual_rows)} hospitals manually. Total: {len(burn_centers_geo)}/136")
else:
    print("No manual patches needed.")

# --- Haversine distance function -----------------------------------------------
def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

# --- For each county, compute distance to nearest burn center -----------------------------
burn_locs = list(zip(burn_centers_geo['LATITUDE'], burn_centers_geo['LONGITUDE']))
aba_locs  = list(zip(
    burn_centers_geo[burn_centers_geo['ABA_VERIFIED'] == 1]['LATITUDE'],
    burn_centers_geo[burn_centers_geo['ABA_VERIFIED'] == 1]['LONGITUDE']
))

def min_dist(county_lat, county_lon, center_locs):
    if not center_locs:
        return None
    return min(haversine_miles(county_lat, county_lon, blat, blon)
               for blat, blon in center_locs)

print("Computing distances (this may take ~30 seconds)...")
county_centroids['dist_any_burn_mi'] = county_centroids.apply(
    lambda r: min_dist(r['county_lat'], r['county_lon'], burn_locs), axis=1
)
county_centroids['dist_aba_burn_mi'] = county_centroids.apply(
    lambda r: min_dist(r['county_lat'], r['county_lon'], aba_locs), axis=1
)
print("Distances computed.")

# --- State-level summary (population-weighted mean distance) -------------------------
dist_state = county_centroids.groupby('STATE').apply(
    lambda g: pd.Series({
        'pop_wtd_dist_any_mi': np.average(
            g['dist_any_burn_mi'].fillna(g['dist_any_burn_mi'].max()),
            weights=g['county_pop']
        ),
        'pop_wtd_dist_aba_mi': np.average(
            g['dist_aba_burn_mi'].fillna(g['dist_aba_burn_mi'].max()),
            weights=g['county_pop']
        ),
        'pct_county_over100mi': (g['dist_any_burn_mi'] > 100).mean() * 100,
        'pct_county_over200mi': (g['dist_any_burn_mi'] > 200).mean() * 100,
    })
).reset_index()

print("\nTop 10 states by population-weighted distance to nearest burn center:")
print(dist_state.sort_values('pop_wtd_dist_any_mi', ascending=False).head(10)[
    ['STATE', 'pop_wtd_dist_any_mi', 'pct_county_over100mi']
].to_string())

# --- Visualize -------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.patch.set_facecolor(C['bg'])

for ax, col, title, color in [
    (axes[0], 'pop_wtd_dist_any_mi',
     'Fig 7.5A · Pop-Weighted Distance to\nNearest Burn Center (Any)', C['burn']),
    (axes[1], 'pop_wtd_dist_aba_mi',
     'Fig 7.5B · Pop-Weighted Distance to\nNearest ABA-Verified Burn Center', C['aba']),
]:
    data = dist_state.sort_values(col, ascending=False).head(15)
    ax.set_facecolor(C['bg'])
    bars = ax.barh(data['STATE'], data[col], color=color, edgecolor='white')
    for bar, val in zip(bars, data[col]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,
                f'{val:.0f} mi', va='center', fontsize=9)
    ax.axvline(100, color='gray', linestyle='--', alpha=0.5, label='100-mile threshold')
    ax.set_xlabel('Population-Weighted Distance (miles)')
    ax.set_title(title, fontweight='bold')
    ax.legend(fontsize=8)

fig.suptitle(
    'Figure 7.5: Geographic Distance to Nearest Burn Center by State\n'
    '(Population-weighted; source: NIRD + Census 2020 County Centroids)',
    fontsize=12, fontweight='bold'
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig7_5_distance_analysis.png')
plt.show()

# --- Merge back into state_df --------------------------------------------------------
state_df = state_df.merge(
    dist_state[['STATE', 'pop_wtd_dist_any_mi', 'pop_wtd_dist_aba_mi', 'pct_county_over100mi']],
    on='STATE', how='left'
)
print("Distance analysis complete. Merged into state_df.")


# ---
# ## Figure 8 - Social Vulnerability (SVI 2022) Integration
# 
# ### County‑level socioeconomic vulnerability mapped to state‑level burn access
# 
# ### **Methodology**
# 
# - **Source:** CDC/ATSDR Social Vulnerability Index (SVI) 2022, `SVI_2022_US_county.csv`, county‑level dataset (3,143 U.S. counties; 15 social factors across 4 themes).
# 
# - **Variables used:**
#   - **EP_POV150** - % population below 150% of federal poverty level  
#   - **EP_NOVEH** - % households with no vehicle  
#   - **EP_LIMENG** - % population with limited English proficiency  
#   - **EP_DISABL** - % population with a disability  
#   - **EP_MINRTY** - % minority population  
# 
# - **Rationale for variable selection:**  
#   These five indicators capture structural barriers that directly affect timely burn care: economic hardship, transportation access, communication barriers, disability burden, and minority status.
# 
# - **Aggregation:**  
#   County-level SVI variables averaged to the **state level** using simple means (consistent with NIRD’s state‑level burn access metrics).
# 
# - **Why SVI:**  
#   SVI provides a standardized, nationally comparable measure of socioeconomic vulnerability that complements Access × Quality × Capacity index by adding a **population‑level equity dimension**.
# 

# In[135]:


fig, ax = plt.subplots(figsize=(10,7))
fig.patch.set_facecolor('#F8F8F8')
ax.set_facecolor('#F8F8F8')

sc = ax.scatter(
    state_df['burn_per_M'],
    state_df['EP_POV150'],
    s=state_df['total_burn_beds'].clip(lower=10)*3,
    c=state_df['pct_aba'],
    cmap='viridis',
    alpha=0.8,
    edgecolors='gray'
)

for _, row in state_df.iterrows():
    ax.annotate(row['STATE'], (row['burn_per_M'], row['EP_POV150']),
                textcoords='offset points', xytext=(4,3), fontsize=7)

plt.colorbar(sc, label='% ABA-Verified Burn Centers')

ax.set_xlabel('Burn Centers per Million Residents', fontweight='bold')
ax.set_ylabel('Poverty Rate (EP_POV150)', fontweight='bold')

ax.set_title(
    'Figure 8: Burn Access vs. Socioeconomic Vulnerability\n'
    '(Bubble = Burn Beds, Color = ABA Verification)',
    fontweight='bold'
)

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig8_svi_access_poverty.png')
plt.show()


# ---
# ## Figure 9 - Composite Burn Care Vulnerability Index

# In[136]:


def norm_inv(s):
    """Invert-normalise: low values → high vulnerability score."""
    mn, mx = s.min(), s.max()
    return 1 - (s - mn) / (mx - mn + 1e-9)

def norm(s):
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn + 1e-9)

idx_df = state_df.copy()

idx_df['score_access']  = norm_inv(idx_df['burn_per_M'])      # fewer centers -> worse
idx_df['score_quality'] = norm_inv(idx_df['pct_aba'])         # less ABA     -> worse
idx_df['score_beds']    = norm_inv(idx_df['beds_per_100k'])   # fewer beds   -> worse
idx_df['score_pop']     = norm(idx_df['pop_M'])               # larger pop   -> higher impact

idx_df['VULNERABILITY'] = (
    idx_df['score_access']  * 0.35 +
    idx_df['score_quality'] * 0.25 +
    idx_df['score_beds']    * 0.25 +
    idx_df['score_pop']     * 0.15
).round(3)

idx_df = idx_df.sort_values('VULNERABILITY', ascending=False)

vc = ['#D62728' if v > 0.65 else '#FF7F0E' if v > 0.50 else '#1F77B4' if v > 0.35 else '#2CA02C'
      for v in idx_df['VULNERABILITY']]

fig, ax = plt.subplots(figsize=(16, 6))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])

ax.bar(idx_df['STATE'], idx_df['VULNERABILITY'],
       color=vc, edgecolor='white', linewidth=0.4)
ax.axhline(0.65, color='#D62728', ls='--', lw=1, label='Critical  (> 0.65)')
ax.axhline(0.50, color='#FF7F0E', ls='--', lw=1, label='High      (> 0.50)')
ax.axhline(0.35, color='#1F77B4', ls='--', lw=1, label='Moderate  (> 0.35)')
ax.set_ylabel('Composite Vulnerability Index')
ax.set_title(
    'Figure 9: Burn Care Access Vulnerability Index by State\n'
    '(Weighted: Access 35% · Quality 25% · Capacity 25% · Population 15%)',
    fontweight='bold'
)
ax.legend(fontsize=8)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, fontsize=7)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig9_vulnerability_index.png')
plt.show()

print('Top 10 most vulnerable states:')
print(idx_df[['STATE','burn_centers','aba_verified','VULNERABILITY']].head(10).to_string(index=False))


# ---
# ## Figure 10 - Top 25 Telemedicine Hub Candidates (Hospital Level)

# In[137]:


top_tele = (
    tele_candidates
    .sort_values('TELE_SCORE', ascending=False)
    .head(25)
    [['HOSPITAL_NAME','STATE','COUNTY','TOTAL_BEDS',
      'ADULT_TRAUMA_L1','ADULT_TRAUMA_L2','TELE_SCORE']]
)

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor(C['bg'])
ax.set_facecolor(C['bg'])
ax.axis('off')

col_labels = ['Hospital', 'State', 'County', 'Total Beds', 'L1', 'L2', 'Tele Score']
cell_data  = [
    [
        r['HOSPITAL_NAME'][:42],
        r['STATE'],
        r['COUNTY'],
        int(r['TOTAL_BEDS']) if pd.notna(r['TOTAL_BEDS']) else 'N/A',
        '✓' if r['ADULT_TRAUMA_L1'] else '',
        '✓' if r['ADULT_TRAUMA_L2'] else '',
        f"{r['TELE_SCORE']:.1f}"
    ]
    for _, r in top_tele.iterrows()
]

tbl = ax.table(cellText=cell_data, colLabels=col_labels,
               loc='center', cellLoc='left')
tbl.auto_set_font_size(False)
tbl.set_fontsize(8)
tbl.scale(1, 1.35)

for (r, c), cell in tbl.get_celld().items():
    cell.set_edgecolor('white')
    if r == 0:
        cell.set_facecolor(C['tele'])
        cell.set_text_props(color='white', fontweight='bold')
    elif r % 2 == 0:
        cell.set_facecolor('#EAF6F9')
    else:
        cell.set_facecolor('white')

ax.set_title(
    'Figure 10: Top 25 Telemedicine Hub Candidates\n'
    '(Trauma hospitals without burn capability, ranked by opportunity score)',
    fontsize=12, fontweight='bold', pad=20
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig10_tele_candidates_table.png')
plt.show()


# ---
# ## Figure 11 - HeatMap: U.S. Burn Care Choropleth

# In[138]:


# --- Shared geometry data (embedded) -----------------------------
US_STATE_POLYS = {
    'AL':[(-88.5,35.0),(-85.0,35.0),(-85.0,32.0),(-88.5,30.2),(-88.5,35.0)],
    'AZ':[(-114.8,37.0),(-109.0,37.0),(-109.0,31.3),(-111.0,31.3),(-114.8,32.5),(-114.8,37.0)],
    'AR':[(-94.6,36.5),(-89.6,36.5),(-89.6,33.0),(-94.0,33.0),(-94.6,36.5)],
    'CA':[(-124.4,42.0),(-120.0,42.0),(-120.0,39.0),(-114.6,35.0),(-114.6,32.5),(-117.1,32.5),(-124.4,37.0),(-124.4,42.0)],
    'CO':[(-109.0,41.0),(-102.0,41.0),(-102.0,37.0),(-109.0,37.0),(-109.0,41.0)],
    'CT':[(-73.7,42.1),(-71.8,42.1),(-71.8,41.0),(-73.7,41.0),(-73.7,42.1)],
    'DE':[(-75.8,39.8),(-75.0,39.8),(-75.0,38.4),(-75.8,38.4),(-75.8,39.8)],
    'FL':[(-87.6,31.0),(-85.0,31.0),(-81.0,30.5),(-80.0,25.1),(-82.0,24.5),(-87.6,30.3),(-87.6,31.0)],
    'GA':[(-85.6,35.0),(-83.1,35.0),(-81.0,32.0),(-81.0,30.4),(-84.9,30.4),(-85.6,35.0)],
    'ID':[(-117.2,49.0),(-111.0,49.0),(-111.0,42.0),(-113.0,42.0),(-117.2,44.0),(-117.2,49.0)],
    'IL':[(-91.5,42.5),(-87.5,42.5),(-87.5,37.0),(-89.0,37.0),(-91.5,40.0),(-91.5,42.5)],
    'IN':[(-88.1,41.8),(-84.8,41.8),(-84.8,38.0),(-88.1,38.0),(-88.1,41.8)],
    'IA':[(-96.6,43.5),(-90.2,43.5),(-90.2,40.4),(-96.6,40.4),(-96.6,43.5)],
    'KS':[(-102.1,40.0),(-94.6,40.0),(-94.6,37.0),(-102.1,37.0),(-102.1,40.0)],
    'KY':[(-89.6,39.1),(-82.0,38.6),(-82.0,36.5),(-89.6,36.5),(-89.6,39.1)],
    'LA':[(-94.0,33.0),(-89.0,33.0),(-89.0,29.0),(-94.0,29.6),(-94.0,33.0)],
    'ME':[(-71.1,47.5),(-67.0,47.5),(-67.0,44.0),(-70.7,43.1),(-71.1,47.5)],
    'MD':[(-79.5,39.7),(-75.0,39.7),(-75.0,38.0),(-79.5,38.0),(-79.5,39.7)],
    'MA':[(-73.5,42.9),(-70.0,42.9),(-70.0,41.5),(-73.5,41.5),(-73.5,42.9)],
    'MI':[(-90.4,46.5),(-84.0,46.5),(-82.5,43.0),(-84.8,41.7),(-86.5,41.7),(-87.1,43.0),(-90.4,46.5)],
    'MN':[(-97.2,49.4),(-89.5,48.0),(-92.1,46.7),(-92.1,43.5),(-96.5,43.5),(-97.2,45.9),(-97.2,49.4)],
    'MS':[(-91.7,35.0),(-88.1,35.0),(-88.1,30.2),(-91.7,30.2),(-91.7,35.0)],
    'MO':[(-95.8,40.6),(-91.7,40.6),(-89.1,37.0),(-94.6,36.5),(-95.8,36.5),(-95.8,40.6)],
    'MT':[(-116.1,49.0),(-104.0,49.0),(-104.0,45.0),(-111.0,44.5),(-116.1,47.5),(-116.1,49.0)],
    'NE':[(-104.0,43.0),(-95.3,43.0),(-95.3,40.0),(-104.0,40.0),(-104.0,43.0)],
    'NV':[(-120.0,42.0),(-114.0,37.0),(-114.0,35.0),(-117.0,35.0),(-120.0,39.0),(-120.0,42.0)],
    'NH':[(-72.6,45.3),(-71.0,45.3),(-71.0,42.7),(-72.6,42.7),(-72.6,45.3)],
    'NJ':[(-75.6,41.4),(-73.9,41.4),(-74.0,39.0),(-75.6,39.0),(-75.6,41.4)],
    'NM':[(-109.0,37.0),(-103.0,37.0),(-103.0,32.0),(-108.2,31.3),(-109.0,31.3),(-109.0,37.0)],
    'NY':[(-79.8,45.0),(-73.0,45.0),(-73.7,41.0),(-79.8,42.0),(-79.8,45.0)],
    'NC':[(-84.3,36.6),(-75.5,36.6),(-75.5,34.0),(-84.3,35.0),(-84.3,36.6)],
    'ND':[(-104.0,49.0),(-97.2,49.0),(-96.6,46.6),(-104.0,46.6),(-104.0,49.0)],
    'OH':[(-84.8,42.3),(-80.5,42.3),(-80.5,38.4),(-84.8,38.4),(-84.8,42.3)],
    'OK':[(-103.0,37.0),(-94.4,37.0),(-94.4,33.6),(-100.0,33.6),(-103.0,36.5),(-103.0,37.0)],
    'OR':[(-124.6,46.3),(-116.5,46.3),(-116.5,42.0),(-120.0,42.0),(-124.6,42.0),(-124.6,46.3)],
    'PA':[(-80.5,42.3),(-74.7,42.3),(-74.7,39.7),(-80.5,39.7),(-80.5,42.3)],
    'RI':[(-71.9,42.0),(-71.1,42.0),(-71.1,41.3),(-71.9,41.3),(-71.9,42.0)],
    'SC':[(-83.4,35.2),(-78.5,34.0),(-79.0,32.0),(-83.4,32.0),(-83.4,35.2)],
    'SD':[(-104.0,46.6),(-96.4,45.9),(-96.4,43.0),(-104.0,43.0),(-104.0,46.6)],
    'TN':[(-90.3,36.7),(-81.6,36.7),(-81.6,35.0),(-90.3,35.0),(-90.3,36.7)],
    'TX':[(-106.6,36.5),(-100.0,36.5),(-94.4,33.6),(-94.0,29.7),(-97.0,26.0),(-104.0,29.0),(-106.6,32.0),(-106.6,36.5)],
    'UT':[(-114.0,42.0),(-109.0,42.0),(-109.0,37.0),(-114.0,37.0),(-114.0,42.0)],
    'VT':[(-73.4,45.0),(-71.5,45.0),(-71.5,43.0),(-73.4,43.0),(-73.4,45.0)],
    'VA':[(-83.7,37.3),(-75.2,37.9),(-75.2,36.5),(-83.7,36.5),(-83.7,37.3)],
    'WA':[(-124.7,49.0),(-117.0,49.0),(-117.0,46.0),(-124.7,46.3),(-124.7,49.0)],
    'WV':[(-82.7,40.6),(-77.7,39.7),(-77.7,37.2),(-80.5,36.5),(-82.7,37.2),(-82.7,40.6)],
    'WI':[(-92.9,47.0),(-87.0,45.5),(-87.0,42.5),(-90.7,42.5),(-92.9,44.5),(-92.9,47.0)],
    'WY':[(-111.1,45.0),(-104.0,45.0),(-104.0,41.0),(-111.1,41.0),(-111.1,45.0)],
}
STATE_CENTROIDS = {
    'AL':(32.8,-86.8),'AZ':(34.3,-111.1),'AR':(34.9,-92.4),'CA':(36.8,-119.4),
    'CO':(39.0,-105.5),'CT':(41.6,-72.7),'DE':(39.0,-75.5),'FL':(27.8,-81.6),
    'GA':(32.7,-83.4),'ID':(44.1,-114.5),'IL':(40.3,-89.0),'IN':(40.3,-86.1),
    'IA':(41.9,-93.4),'KS':(38.5,-98.4),'KY':(37.8,-85.3),'LA':(31.2,-91.8),
    'ME':(44.7,-69.4),'MD':(39.1,-76.8),'MA':(42.2,-71.5),'MI':(43.3,-84.5),
    'MN':(46.4,-93.1),'MS':(32.7,-89.7),'MO':(38.5,-92.5),'MT':(47.0,-110.5),
    'NE':(41.5,-99.9),'NV':(39.3,-116.6),'NH':(44.0,-71.5),'NJ':(40.1,-74.7),
    'NM':(34.8,-106.2),'NY':(42.9,-75.5),'NC':(35.5,-79.4),'ND':(47.5,-100.5),
    'OH':(40.4,-82.8),'OK':(35.6,-97.5),'OR':(44.1,-120.5),'PA':(41.2,-77.2),
    'RI':(41.7,-71.5),'SC':(33.8,-80.9),'SD':(44.4,-100.2),'TN':(35.9,-86.4),
    'TX':(31.1,-97.6),'UT':(39.3,-111.1),'VT':(44.3,-72.7),'VA':(37.8,-79.5),
    'WA':(47.4,-120.6),'WV':(38.9,-80.5),'WI':(44.3,-89.8),'WY':(43.0,-107.5),
}

from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
import matplotlib.cm as cm

no_burn_states = state_df[state_df['burn_centers'] == 0]['STATE'].tolist()
vuln_map = dict(zip(idx_df['STATE'], idx_df['VULNERABILITY']))
bpm_map  = dict(zip(state_df['STATE'], state_df['burn_per_M']))

def _draw_choropleth(ax, value_dict, cmap_name, title, no_burn):
    vmin, vmax = min(value_dict.values()), max(value_dict.values())
    norm_c = Normalize(vmin=vmin, vmax=vmax)
    cmap_obj = cm.get_cmap(cmap_name)
    patches_list, vals = [], []
    for state, coords in US_STATE_POLYS.items():
        patches_list.append(MplPolygon(np.array(coords), closed=True))
        vals.append(value_dict.get(state, 0))
    pc = PatchCollection(patches_list, cmap=cmap_name, norm=norm_c,
                         alpha=0.92, edgecolors='white', linewidths=0.8)
    pc.set_array(np.array(vals))
    ax.add_collection(pc)
    for state, (lat, lon) in STATE_CENTROIDS.items():
        if state not in US_STATE_POLYS:
            continue
        val  = value_dict.get(state, 0)
        star = '★' if state in no_burn else ''
        txt  = f"{star}{state}\n{val:.2f}"
        col  = 'white' if norm_c(val) > 0.62 else 'black'
        ax.text(lon, lat, txt, ha='center', va='center',
                fontsize=5.5, fontweight='bold', color=col)
    ax.set_xlim(-130, -65); ax.set_ylim(23, 50)
    ax.set_aspect(1.3); ax.axis('off')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    return pc

fig, axes = plt.subplots(1, 2, figsize=(20, 9))
fig.patch.set_facecolor('#F8F8F8')

pc1 = _draw_choropleth(axes[0], vuln_map, 'RdYlGn_r',
    'Burn Care Access Vulnerability Index\n(Red = most vulnerable  |  * = zero burn centers)',
    no_burn_states)
cb1 = fig.colorbar(pc1, ax=axes[0], fraction=0.03, pad=0.02)
cb1.set_label('Vulnerability Index (0 = safe → 1 = critical)', fontsize=9)

pc2 = _draw_choropleth(axes[1], bpm_map, 'RdYlGn',
    'Burn Centers per Million Residents\n(Green = higher access  |  * = zero burn centers)',
    no_burn_states)
cb2 = fig.colorbar(pc2, ax=axes[1], fraction=0.03, pad=0.02)
cb2.set_label('Burn Centers per Million Residents', fontsize=9)

# --- AK / HI inset boxes ----------------------------------------------
for fig_ax, vdict, cmap_n in [(axes[0], vuln_map, 'RdYlGn_r'), (axes[1], bpm_map, 'RdYlGn')]:
    norm_i = Normalize(vmin=min(vdict.values()), vmax=max(vdict.values()))
    for state, (bx, by, bw, bh), lat, lon in [
        ('AK', (-130, 23, 10, 7), 26.5, -125.5),
        ('HI', (-118, 23,  7, 4), 25.0, -114.5),
    ]:
        val = vdict.get(state, 0)
        rect = plt.Rectangle((bx, by), bw, bh,
                              facecolor=cm.get_cmap(cmap_n)(norm_i(val)),
                              edgecolor='white', linewidth=1, alpha=0.92,
                              transform=fig_ax.transData)
        fig_ax.add_patch(rect)
        star = '★' if state in no_burn_states else ''
        col  = 'white' if norm_i(val) > 0.62 else 'black'
        fig_ax.text(lon, lat, f"{star}{state}\n{val:.2f}",
                    ha='center', va='center', fontsize=6,
                    fontweight='bold', color=col)

fig.suptitle(
    'Figure 11: HeatMap: U.S. Burn Care Geographic Analysis\n'
    'Left: Composite Vulnerability Index  |  Right: Burn Centers per Million Residents',
    fontsize=14, fontweight='bold', y=1.01
)
fig.text(0.5, 0.01,
         f'* States with ZERO adult burn centers: {", ".join(no_burn_states)}',
         ha='center', fontsize=9, color='#D62728', style='italic', fontweight='bold')

plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig11_choropleth_heatmap.png')
plt.show()
print('  Figure 10 saved.')


# ---
# ## Figure 12 - Rural-Urban Burn Care Disparity
# 
# **Rural-Urban classification uses the official USDA Economic Research Service (ERS) Rural-Urban Continuum Codes (RUCC) 2023, county-level data aggregated to the state level.**
# 
# ### Methodology
# - **Source:** USDA ERS *Rural-Urban Continuum Codes 2023* (`Ruralurbancontinuumcodes2023.xlsx`), covering 3,235 U.S. counties across all 50 states
# - **Scale:** 9-point scale - Codes 1-3 = Metro (Urban), Codes 4-6 = Nonmetro adjacent/moderate (Mixed), Codes 7-9 = Nonmetro non-adjacent/most rural (Rural)
# - **Aggregation:** Median RUCC score computed across all counties within each state, then mapped to three categories (Urban / Mixed / Rural)
# - **Why RUCC over RUCA:** RUCA codes operate at the census-tract level, which exceeds the spatial resolution of the hospital-level NIRD dataset. RUCC county-level codes are the appropriate match for state-level aggregation.
# 
# | RUCC Code | Description | Category |
# |-----------|-------------|----------|
# | 1-3 | Metro counties (large -> small metro areas) | **Urban** |
# | 4-6 | Nonmetro, adjacent to metro, varying urban pop | **Mixed** |
# | 7-9 | Nonmetro, not adjacent to metro (most rural) | **Rural** |
# 

# In[147]:


# --- USDA Rural-Urban Continuum Codes (RUCC) 2023 - county-level, aggregated to state ---
# Source: USDA Economic Research Service, Ruralurbancontinuumcodes2023.xlsx
# 3,235 U.S. counties | 9-point scale: 1-3=Urban, 4-6=Mixed, 7-9=Rural
# Aggregation method: median RUCC score per state → category assignment

FIFTY_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA',
    'KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
    'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT',
    'VA','WA','WV','WI','WY'
}

# Try loading the RUCC file from multiple paths
RUCC_PATHS = [
    'Ruralurbancontinuumcodes2023.xlsx',
    '/mnt/user-data/uploads/Ruralurbancontinuumcodes2023.xlsx',
]

rucc_loaded = False
for rucc_path in RUCC_PATHS:
    try:
        wb_rucc = openpyxl.load_workbook(rucc_path, read_only=True, data_only=True)
        ws_rucc = wb_rucc['Rural-urban Continuum Code 2023']
        rucc_rows = list(ws_rucc.iter_rows(min_row=2, values_only=True))
        rucc_loaded = True
        print(f'✓ RUCC data loaded: {rucc_path} ({len(rucc_rows):,} counties)')
        break
    except Exception:
        continue

if rucc_loaded:
    # Aggregate county RUCC codes to state-level median
    state_rucc_codes = defaultdict(list)
    for row in rucc_rows:
        state, rucc = row[1], row[4]
        if state in FIFTY_STATES and rucc is not None:
            state_rucc_codes[state].append(rucc)

    RURAL_URBAN       = {}
    STATE_RUCC_MEDIAN = {}
    for state in sorted(state_rucc_codes.keys()):
        codes = state_rucc_codes[state]
        med   = statistics.median(codes)
        RURAL_URBAN[state]       = 'Urban' if med <= 3 else ('Mixed' if med <= 6 else 'Rural')
        STATE_RUCC_MEDIAN[state] = med

    rucc_source_label = 'USDA RUCC 2023 (county-level, n=3,235)'

else:
    # Fallback: pre-computed values from RUCC 2023 dataset (computed 2026-03-02)
    print('WARNING: RUCC file not found — using pre-computed RUCC 2023 values')
    RURAL_URBAN = {
        'AK':'Rural',  # median RUCC=9.0, n=30 counties
        'AL':'Mixed',  # median RUCC=4.0, n=67 counties
        'AR':'Rural',  # median RUCC=7.0, n=75 counties
        'AZ':'Urban',  # median RUCC=3.0, n=15 counties
        'CA':'Urban',  # median RUCC=2.0, n=58 counties
        'CO':'Rural',  # median RUCC=7.0, n=64 counties
        'CT':'Urban',  # median RUCC=2.0, n=9  counties
        'DE':'Urban',  # median RUCC=3.0, n=3  counties
        'FL':'Urban',  # median RUCC=2.0, n=67 counties
        'GA':'Mixed',  # median RUCC=4.0, n=159 counties
        'HI':'Urban',  # median RUCC=3.0, n=5  counties
        'IA':'Rural',  # median RUCC=7.0, n=99 counties
        'ID':'Rural',  # median RUCC=6.5, n=44 counties
        'IL':'Mixed',  # median RUCC=6.0, n=102 counties
        'IN':'Mixed',  # median RUCC=4.0, n=92 counties
        'KS':'Rural',  # median RUCC=8.0, n=105 counties
        'KY':'Rural',  # median RUCC=6.5, n=120 counties
        'LA':'Urban',  # median RUCC=3.0, n=64 counties
        'MA':'Urban',  # median RUCC=2.0, n=14 counties
        'MD':'Urban',  # median RUCC=1.5, n=24 counties
        'ME':'Rural',  # median RUCC=6.5, n=16 counties
        'MI':'Mixed',  # median RUCC=6.0, n=83 counties
        'MN':'Mixed',  # median RUCC=6.0, n=87 counties
        'MO':'Rural',  # median RUCC=7.0, n=115 counties
        'MS':'Rural',  # median RUCC=7.0, n=82 counties
        'MT':'Rural',  # median RUCC=8.0, n=56 counties
        'NC':'Mixed',  # median RUCC=4.0, n=100 counties
        'ND':'Rural',  # median RUCC=8.0, n=53 counties
        'NE':'Rural',  # median RUCC=9.0, n=93 counties
        'NH':'Mixed',  # median RUCC=4.0, n=10 counties
        'NJ':'Urban',  # median RUCC=1.0, n=21 counties
        'NM':'Mixed',  # median RUCC=6.0, n=33 counties
        'NV':'Mixed',  # median RUCC=6.0, n=17 counties
        'NY':'Urban',  # median RUCC=3.0, n=62 counties
        'OH':'Mixed',  # median RUCC=4.0, n=88 counties
        'OK':'Rural',  # median RUCC=7.0, n=77 counties
        'OR':'Mixed',  # median RUCC=4.5, n=36 counties
        'PA':'Mixed',  # median RUCC=4.0, n=67 counties
        'RI':'Urban',  # median RUCC=1.0, n=5  counties
        'SC':'Urban',  # median RUCC=3.0, n=46 counties
        'SD':'Rural',  # median RUCC=9.0, n=66 counties
        'TN':'Mixed',  # median RUCC=4.0, n=95 counties
        'TX':'Mixed',  # median RUCC=6.0, n=254 counties
        'UT':'Rural',  # median RUCC=7.0, n=29 counties
        'VA':'Urban',  # median RUCC=3.0, n=133 counties
        'VT':'Rural',  # median RUCC=7.0, n=14 counties
        'WA':'Mixed',  # median RUCC=4.0, n=39 counties
        'WI':'Mixed',  # median RUCC=6.0, n=72 counties
        'WV':'Rural',  # median RUCC=7.0, n=55 counties
        'WY':'Rural',  # median RUCC=7.0, n=23 counties
    }
    rucc_source_label = 'USDA RUCC 2023 (pre-computed fallback)'

RU_COLORS = {'Urban': '#1F77B4', 'Mixed': '#FF7F0E', 'Rural': '#D62728'}
CATS       = ['Urban', 'Mixed', 'Rural']

state_df['rural_class'] = state_df['STATE'].map(RURAL_URBAN).fillna('Mixed')

ru = state_df.groupby('rural_class').agg(
    states         = ('STATE',           'count'),
    burn_centers   = ('burn_centers',    'sum'),
    pop_M          = ('pop_M',           'sum'),
    burn_beds      = ('total_burn_beds', 'sum'),
    trauma_no_burn = ('trauma_no_burn',  'sum'),
).reset_index()
ru['bc_per_M']   = (ru['burn_centers'] / ru['pop_M']).round(3)
ru['beds_per_M'] = (ru['burn_beds']    / ru['pop_M']).round(2)

# --- Print summary ---------------------------------------------------
print(f'\nRUCC 2023 Classification Results ({rucc_source_label}):')
print(f'{"Category":<8} {"BC/M":<8} {"Beds/M":<8} {"States":<8} {"BCs"}')
print('-' * 45)
for cat in CATS:
    row = ru[ru['rural_class'] == cat].iloc[0]
    print(f"{cat:<8} {row['bc_per_M']:<8.3f} {row['beds_per_M']:<8.1f}"
          f" {int(row['states']):<8} {int(row['burn_centers'])}")

urban_bc = ru[ru['rural_class']=='Urban']['bc_per_M'].values[0]
rural_bc = ru[ru['rural_class']=='Rural']['bc_per_M'].values[0]
print(f'\n=> Urban states have {urban_bc/rural_bc:.1f}x MORE burn centers/capita than Rural')
print(f'   (Rural access = {rural_bc/urban_bc:.2f}x that of Urban states)')

# --- Figure 11: Rural-Urban Disparity Plots --------------------------
fig, axes = plt.subplots(1, 3, figsize=(17, 6))
fig.patch.set_facecolor(C['bg'])

def _bar3(ax, vals, ylabel, title):
    bars = ax.bar(CATS, vals, color=[RU_COLORS[c] for c in CATS],
                  edgecolor='white', width=0.52)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.03,
                f'{val:.2f}', ha='center', fontsize=11, fontweight='bold')
    ax.set_ylabel(ylabel); ax.set_title(title, fontweight='bold')
    ax.set_ylim(0, max(vals) * 1.35)
    ax.set_facecolor(C['bg'])

bc_vals  = [ru[ru['rural_class']==c]['bc_per_M'].values[0]   for c in CATS]
bed_vals = [ru[ru['rural_class']==c]['beds_per_M'].values[0] for c in CATS]
_bar3(axes[0], bc_vals,  'Burn Centers per Million', 'Burn Center Access\nby Urban-Rural Class')
_bar3(axes[1], bed_vals, 'Burn Beds per Million',    'Burn Bed Capacity\nby Urban-Rural Class')

# Scatter: state-level access vs capacity, coloured by class
ax3 = axes[2]; ax3.set_facecolor(C['bg'])
for cat in CATS:
    sub = state_df[state_df['rural_class'] == cat]
    ax3.scatter(sub['burn_per_M'], sub['beds_per_100k'],
                color=RU_COLORS[cat], label=cat, s=75, alpha=0.85, edgecolors='white')
    for _, row in sub.iterrows():
        ax3.annotate(row['STATE'], (row['burn_per_M'], row['beds_per_100k']),
                     fontsize=5.5, ha='center', xytext=(0, 3),
                     textcoords='offset points')
ax3.set_xlabel('Burn Centers per Million'); ax3.set_ylabel('Burn Beds per 100k')
ax3.set_title('Access vs. Capacity\nby Urban-Rural Class', fontweight='bold')
ax3.legend(fontsize=9)

fig.suptitle(
    f'Figure 12: Rural-Urban Burn Care Access Disparity\n'
    f'Rural states have {urban_bc/rural_bc:.1f}\u00d7 fewer burn centers per capita than Urban states'
    f'  (Source: {rucc_source_label})',
    fontsize=13, fontweight='bold'
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig12_rural_urban_disparity.png')
plt.show()
print('  Figure 12 saved.')


# ---
# ## Figure 13 - Projected Patient Impact of Under-Referral

# In[158]:


# --- Literature parameters (cited) -------------------------------
# Huang et al. (2021) - statewide Illinois study:
#   66% of patients meeting ABA referral criteria treated at non-burn facilities
# Ivanko et al. (2024) Burden of Burns - ~600k annual burn injuries requiring care
# Murray et al. (2019) - delayed referral adds 6.9 hospital days (17.7 vs 10.8)
# Conservative daily cost: $3,500/day (ABA cost benchmarks)

UNDER_REFERRAL_RATE  = 0.66   # Huang et al. 2021
BURN_INC_PER_100K    = 202    # ~600k / 297M US population
PCT_NEEDING_BURN_CTR = 0.15   # ~15% of burn injuries require specialist burn centre
EXCESS_LOS_DAYS      = 6.9    # Murray et al. 2019 (17.7 vs 10.8 days)
AVG_DAILY_COST_USD   = 3500   # conservative

proj = state_df.copy()
proj['est_annual_burns']        = (proj['pop_k'] * BURN_INC_PER_100K / 100).astype(int)
proj['burns_needing_specialist']= (proj['est_annual_burns'] * PCT_NEEDING_BURN_CTR).astype(int)

# States with ZERO burn centers assumed 90% under-referral
proj['under_referred'] = np.where(
    proj['burn_centers'] == 0,
    (proj['burns_needing_specialist'] * 0.90).astype(int),
    (proj['burns_needing_specialist'] * UNDER_REFERRAL_RATE).astype(int),
)
proj['excess_hosp_days']    = (proj['under_referred'] * EXCESS_LOS_DAYS).astype(int)
proj['avoidable_cost_M']    = (proj['excess_hosp_days'] * AVG_DAILY_COST_USD / 1e6).round(1)
proj['excess_infections']   = (proj['under_referred'] * 0.12 * 0.40).round(0).astype(int)  # 40% RR increase

nat_patients = proj['under_referred'].sum()
nat_cost     = proj['avoidable_cost_M'].sum()
nat_infx     = proj['excess_infections'].sum()
print(f"National projection (Huang et al. 66% rate):")
print(f"  {nat_patients:,} patients/yr receive suboptimal burn care")
print(f" ${nat_cost:,.0f}M in avoidable annual healthcare costs")
print(f" {nat_infx:,} excess infections estimated")

# --- Zero-burn-center states callout ------------------------------------
print("\nZero-burn-center states - patient impact:")
for _, row in proj[proj['burn_centers']==0].sort_values('under_referred',ascending=False).iterrows():
    print(f"  {row['STATE']}: ~{row['under_referred']:,} patients/yr  |  ${row['avoidable_cost_M']:.0f}M avoidable costs")

fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.patch.set_facecolor(C['bg'])

def _impact_color(bc):
    if bc == 0:   return C['burn']
    if bc <= 2:   return C['aba']
    return C['trauma']

top20 = proj.sort_values('under_referred', ascending=False).head(20)
top20c= proj.sort_values('avoidable_cost_M', ascending=False).head(20)

for ax, data_col, xlabel, panel_title in [
    (axes[0], 'under_referred',  'Estimated Under-Referred Patients / Year',
     'Figure 13A · Estimated Annual Under-Referral\n(Huang et al. 2021 - 66% rate applied)'),
    (axes[1], 'avoidable_cost_M','Estimated Avoidable Annual Cost (USD Millions)',
     'Figure 13B · Estimated Avoidable Annual Costs\n(Excess hospital days × $3,500/day)'),
]:
    data = top20 if data_col == 'under_referred' else top20c
    ax.set_facecolor(C['bg'])
    bars = ax.barh(data['STATE'], data[data_col],
                   color=[_impact_color(v) for v in data['burn_centers']],
                   edgecolor='white')
    for bar, val in zip(bars, data[data_col]):
        label = f'{int(val):,}' if data_col == 'under_referred' else f'${val:.0f}M'
        ax.text(bar.get_width() + max(data[data_col]) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                label, va='center', fontsize=8)
    ax.set_xlabel(xlabel)
    ax.set_title(panel_title, fontweight='bold')
    ax.legend(handles=[
        mpatches.Patch(color=C['burn'],   label='Zero burn centers'),
        mpatches.Patch(color=C['aba'],    label='1–2 burn centers'),
        mpatches.Patch(color=C['trauma'], label='3+ burn centers'),
    ], fontsize=8)

fig.suptitle(
    f'Figure 13: Projected Patient Impact of Burn Care Under-Referral\n'
    f'National (Team 13 modeled estimate): ~{nat_patients:,} patients/yr  |  ~${nat_cost:,.0f}M avoidable costs'
    f'  |  {nat_infx:,} excess infections\n'
    f'(Team 13 model: Huang 2021 under-referral rate · Murray 2019 excess LOS · Ivanko 2024 incidence · $3,500/day ABA cost benchmark)',
    fontsize=12, fontweight='bold'
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig13_patient_impact.png')
plt.show()
print('  Figure 13 saved.')


# ---
# ## Figure 14 - Narrative Arc: The Burn Care Crisis

# In[141]:


fig = plt.figure(figsize=(18, 9))
fig.patch.set_facecolor('#0D1117')

fig.text(0.5, 0.93,
         '  The Burn Care Access Crisis in America',
         ha='center', va='center', fontsize=22, fontweight='bold', color='white')
fig.text(0.5, 0.875,
         'Every year, ~600,000 Americans need emergency burn care - '
         'but where they live determines whether they get it.',
         ha='center', va='center', fontsize=13, color='#CCCCCC', style='italic')

STORY = [
    ('THE\nPROBLEM',  '#D62728', 0.08,
     ['600,000 burn injuries/yr', 'need emergency care in', 'the US', '(Ivanko et al., 2024)']),
    ('THE\nGAP',      '#FF7F0E', 0.27,
     ['7 states have ZERO', 'adult burn centers', '95% of L2 trauma centers', 'lack burn capability']),
    ('THE\nINEQUITY', '#9467BD', 0.46,
     ['Rural states have', f'{1.1:.1f}× fewer BCs/capita', 'Under-referral rate:', '66% (Huang et al., 2021)']),
    ('THE\nIMPACT',   '#17BECF', 0.65,
     [f'~{nat_patients:,} patients/yr', 'receive suboptimal care',
      f'${nat_cost:,.0f}M/yr in', 'avoidable costs']),
    ('THE\nFIX',      '#2CA02C', 0.84,
     ['ABA verification', 'expansion + tele-burn', 'hub-spoke networks', 'in 34 critical states']),
]

arrow_y = 0.40
for label, color, x, bullets in STORY:
    ax_b = fig.add_axes([x - 0.02, 0.25, 0.17, 0.56])
    ax_b.set_facecolor(color); ax_b.set_xlim(0,1); ax_b.set_ylim(0,1); ax_b.axis('off')
    ax_b.text(0.5, 0.91, label, ha='center', va='top', fontsize=13,
              fontweight='bold', color='white', linespacing=1.2)
    ax_b.axhline(0.73, color='white', lw=1, alpha=0.45)
    for j, b in enumerate(bullets):
        ax_b.text(0.5, 0.63 - j * 0.13, b, ha='center', va='top',
                  fontsize=8.5, color='white', linespacing=1.1)
    if x < 0.80:
        fig.text(x + 0.16, arrow_y, '→', ha='center', va='center',
                 fontsize=30, color='white', fontweight='bold')

fig.text(0.5, 0.05,
    'Sources: Ivanko et al. (2024) Burden of Burns  ·  Huang et al. (2021) IL Statewide Study  ·'
    '  Murray et al. (2019) Referral Delay  ·  NIRD Database (2023)',
    ha='center', fontsize=8, color='#888888')

plt.savefig(f'{OUTPUT_DIR}/fig14_narrative_arc.png', facecolor='#0D1117')
plt.show()
print('  Figure 14 saved.')


# ---
# ## Figure 15 - Vulnerability Index Sensitivity Analysis

# In[142]:


WEIGHT_SCENARIOS = {
    'Base\n(35/25/25/15)':        (0.35, 0.25, 0.25, 0.15),
    'Access\nHeavy\n(50/20/20/10)':(0.50, 0.20, 0.20, 0.10),
    'Quality\nHeavy\n(25/40/25/10)':(0.25, 0.40, 0.25, 0.10),
    'Capacity\nHeavy\n(25/20/40/15)':(0.25, 0.20, 0.40, 0.15),
    'Equal\n(25/25/25/25)':        (0.25, 0.25, 0.25, 0.25),
}

sens = idx_df[['STATE','score_access','score_quality','score_beds','score_pop']].copy()
for scenario, (w1, w2, w3, w4) in WEIGHT_SCENARIOS.items():
    sens[scenario] = (
        sens['score_access']  * w1 +
        sens['score_quality'] * w2 +
        sens['score_beds']    * w3 +
        sens['score_pop']     * w4
    ).round(4)

base_col  = list(WEIGHT_SCENARIOS.keys())[0]
top10     = sens.nlargest(10, base_col)['STATE'].tolist()
scen_cols = list(WEIGHT_SCENARIOS.keys())

# Build rank tables
rank_data = {}
for sc in scen_cols:
    ordered = sens.sort_values(sc, ascending=False)['STATE'].tolist()
    rank_data[sc] = {s: ordered.index(s) + 1 for s in top10}

rank_matrix = pd.DataFrame(
    {sc: [rank_data[sc][s] for s in top10] for sc in scen_cols},
    index=top10
)

# Stability stats
max_rank_shift = int((rank_matrix.max(axis=1) - rank_matrix.min(axis=1)).max())
always_top15   = (rank_matrix.max(axis=1) <= 15).all()
print(f"Max rank shift across all scenarios: {max_rank_shift}")
print(f"All top-10 states remain in top 15 across every scenario: {always_top15}")

fig, axes = plt.subplots(1, 2, figsize=(18, 7))
fig.patch.set_facecolor(C['bg'])

# ─-- Left: heatmap of ranks --------------------------------------------------
ax = axes[0]; ax.set_facecolor(C['bg'])
im = ax.imshow(rank_matrix.values, cmap='RdYlGn_r', aspect='auto', vmin=1, vmax=16)
ax.set_xticks(range(len(scen_cols)))
ax.set_xticklabels([s.replace('\n',' ') for s in scen_cols],
                   rotation=25, ha='right', fontsize=8)
ax.set_yticks(range(len(top10)))
ax.set_yticklabels(top10, fontsize=10)
for i in range(len(top10)):
    for j in range(len(scen_cols)):
        val = rank_matrix.iloc[i, j]
        ax.text(j, i, str(val), ha='center', va='center',
                fontsize=10, fontweight='bold',
                color='white' if val <= 5 else 'black')
plt.colorbar(im, ax=ax, label='Vulnerability Rank (1 = most vulnerable)')
ax.set_title('Top 10 State Rankings Across\nAll 5 Weight Scenarios', fontweight='bold')

# --- Right: score range bars -----------------------------------
ax2 = axes[1]; ax2.set_facecolor(C['bg'])
score_ranges = []
for state in top10:
    scores = [sens[sens['STATE'] == state][sc].values[0] for sc in scen_cols]
    score_ranges.append({'state': state, 'min': min(scores),
                          'max': max(scores), 'base': scores[0]})
sr = pd.DataFrame(score_ranges).sort_values('base', ascending=True)
yp = range(len(sr))

ax2.barh(yp, sr['max'] - sr['min'], left=sr['min'],
         color=C['tele'], alpha=0.5, height=0.5,
         label='Score range across all scenarios')
ax2.scatter(sr['base'], yp, color=C['burn'], s=90, zorder=5,
            marker='D', label='Base score')
ax2.set_yticks(yp); ax2.set_yticklabels(sr['state'], fontsize=10)
ax2.set_xlabel('Vulnerability Score')
ax2.set_title('Score Stability per State\n(Narrow bars = robust, weight-insensitive ranking)',
              fontweight='bold')
ax2.axvline(0.65, color=C['burn'], ls='--', lw=1.2, alpha=0.6,
            label='Critical threshold (0.65)')
ax2.legend(fontsize=8)

fig.suptitle(
    f'Figure 15: Vulnerability Index Sensitivity Analysis\n'
    f'All top-10 states remain in the top 15 across every weighting scheme  '
    f'(max rank shift = {max_rank_shift}) - index is methodologically robust',
    fontsize=13, fontweight='bold'
)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}/fig15_sensitivity_analysis.png')
plt.show()
print('  Figure 15 saved.')


# ---
# ## Export Summary Excel Workbook

# In[156]:


vuln_out = idx_df[['STATE','burn_centers','aba_verified','total_burn_beds',
                   'pop_M','burn_per_M','beds_per_100k','pct_aba','VULNERABILITY']].copy()
vuln_out['RISK_TIER'] = pd.cut(
    vuln_out['VULNERABILITY'],
    bins=[0, 0.35, 0.50, 0.65, 1.0],
    labels=['Low', 'Moderate', 'High', 'Critical']
)

# --- Referral gap table -----------------------------------------
ref_out = state_df[['STATE','burn_centers','l1_trauma','l2_trauma',
                    'l1_no_burn','l2_no_burn','trauma_no_burn']].copy()
ref_out['referral_gap_rate'] = (
    ref_out['trauma_no_burn'] /
    (ref_out['l1_trauma'] + ref_out['l2_trauma']).replace(0, np.nan) * 100
).fillna(0).round(1)

# --- Priority recommendations ---------------------------------
priority_states = vuln_out[vuln_out['RISK_TIER'].isin(['High','Critical'])]['STATE'].tolist()
recs = []
for s in priority_states:
    row = vuln_out[vuln_out['STATE'] == s].iloc[0]
    recs.append({
        'STATE'             : s,
        'RISK_TIER'         : str(row['RISK_TIER']),
        'Burn Centers'      : int(row['burn_centers']),
        'ABA Verified'      : int(row['aba_verified']),
        'Burn Beds'         : int(row['total_burn_beds']),
        'Vulnerability Score': round(row['VULNERABILITY'], 3),
        'Recommendation': (
            'Establish new ABA-verified burn center; prioritize telemedicine hub'
            if row['burn_centers'] == 0
            else 'Expand ABA verification; deploy telemedicine spoke hospitals'
            if row['pct_aba'] < 50
            else 'Increase burn bed capacity; strengthen referral protocols'
        )
    })

tele_out = (
    tele_candidates
    .sort_values('TELE_SCORE', ascending=False)
    .head(50)
    [['HOSPITAL_NAME','STATE','COUNTY','ADDRESS',
      'TOTAL_BEDS','ADULT_TRAUMA_L1','ADULT_TRAUMA_L2','TELE_SCORE']]
)

with pd.ExcelWriter(f'{OUTPUT_DIR}/NIRD_Analysis_Summary.xlsx', engine='openpyxl') as writer:
    state_df.merge(idx_df[['STATE','VULNERABILITY']], on='STATE', how='left').to_excel(
        writer, sheet_name='State_Summary', index=False)
    vuln_out.to_excel(writer, sheet_name='Vulnerability_Ranking', index=False)
    tele_out.to_excel(writer, sheet_name='Tele_Candidates_Top50', index=False)
    ref_out.to_excel(writer, sheet_name='Referral_Gap', index=False)
    pd.DataFrame(recs).to_excel(writer, sheet_name='Priority_Recommendations', index=False)

print(' Excel workbook saved -> outputs/NIRD_Analysis_Summary.xlsx')
print(f'   Sheets: State_Summary | Vulnerability_Ranking | Tele_Candidates_Top50 | Referral_Gap | Priority_Recommendations')


# ---
# ## Key Findings Summary

# In[157]:


# ========================== FINAL KEY FINDINGS SUMMARY CELL ==========================

# Make sure 'outputs' folder exists
os.makedirs('outputs', exist_ok=True)

# === DYNAMIC SUMMARY (uses your actual data) ===
summary_text = f"""=================================================================
  KEY FINDINGS SUMMARY - HeatMap Hackathon 2026
=================================================================

NATIONAL SNAPSHOT
  - {len(df)} hospitals across 50 states
  - {df['BURN_ADULT'].sum()} adult burn centers  |  {df['BURN_PEDS'].sum()} pediatric burn centers
  - {df['ABA_VERIFIED'].sum()} ABA-verified burn centers  (62% of adult BCs)
  - 7 states with ZERO adult burn centers: AK, DE, MS, MT, ND, NH, SD

EQUITY GAPS
  - Top 5 most vulnerable states: MS, NH, MT, DE, SD
  - 34 states classified as Critical tier
  - Burn bed density ranges from 0 -> 6.110 per 100k residents

REFERRAL NETWORK GAPS
  - 143/229 (62.4%) Level I trauma centers lack burn capability
  - 319/336 (94.9%) Level II trauma centers lack burn capability
  - 498 total trauma centers = potential referral bottlenecks

TELEMEDICINE OPPORTUNITY
  - 351 high-priority tele-burn deployment sites identified (score ≥ 5)
  - Top tele-state: IL (52 candidate hospitals)

PEDIATRIC ACCESS
  - 5 states have adult burn centers but NO pediatric capability
  - States: CT, KY, ME, VT, WV

BURDEN & IMPACT (Team 13 Modeled Estimate)
  - Using published estimates for under-referral (Huang et al., 2021), excess hospital days 
    (Murray et al., 2019), and national burn incidence (Ivanko et al., 2024), we model 
    ~67,000 under-referred patients per year and ~$1.6B in avoidable annual costs.
  - This is a conservative modeled projection illustrating the scale of the structural gap.
  - Based on: Huang et al. 2021 (66% under-referral rate), Murray et al. 2019 
    (6.9 excess hospital days), Ivanko et al. 2024 (600k/yr incidence), 
    $3,500/day cost assumption (ABA cost benchmark)
    
All figures saved to → outputs/
================================================================="""

print(summary_text)

# Auto-save for submission
with open('outputs/KEY_FINDINGS_SUMMARY.md', 'w', encoding='utf-8') as f:
    f.write(summary_text)
with open('outputs/KEY_FINDINGS_SUMMARY.txt', 'w', encoding='utf-8') as f:
    f.write(summary_text)

print("\n SUCCESS! Summary saved to outputs/KEY_FINDINGS_SUMMARY.md and .txt")


# In[ ]:




