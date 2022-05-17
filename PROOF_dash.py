"""
Strealit dashboard for PROOF collective 
Data provided by @NFTommo | wgmi.io 
Code by @rbarniker 
"""

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import datetime
from st_aggrid import AgGrid
from st_aggrid.shared import JsCode
from st_aggrid.shared import GridUpdateMode
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Blacklisted from analysis
blacklist=['Rarible',
           'The Misfits Ape Society Col', # Airdrop to all MB
           '#NAME?',
           'PROOF Collective']

# Simplify name for visualization
name_dict=pd.DataFrame()
name_dict.loc['Dead Ringers: Edition by Dmitri Cherniak','Name']='Dead Ringers'
name_dict.loc['Woodies Generative Characters','Name']='Woodies'
name_dict.loc['adidas Originals Into the Metaverse','Name']='Adidas'
name_dict.loc['MetaHero Universe: Planet Tokens','Name']='MetaHero Tokens'
name_dict.loc['Bored Ape Yacht Club','Name']='BAYC'
name_dict.loc['Mutant Ape Yacht Club','Name']='MAYC'
name_dict.loc['Rug Radio - Genesis NFT','Name']='Rug Radio'
name_dict.loc['The Aquatica Collection','Name']='Aquatica Collection'
name_dict.loc['CLONE X - X TAKASHI MURAKAMI','Name']='CLONEX'
name_dict.loc['Angry Ape Army Evolution Collection','Name']='Angry Ape Army'
name_dict.loc['Chromie Squiggle by Snowfro','Name']='Chromie Squiggle'
name_dict.loc['WGMI Premium Membership','Name']='WGMI'
name_dict.loc['CrypToadz by GREMPLIN','Name']='CrypToadz'
name_dict.loc['BFF Friendship Bracelets','Name']='BFF'

# Cols for data read
cols = ['Project',
 'PROOF Owners Holding',
 '% PROOF Members Holding',
 '% Project Held by PROOF Members',
 'Project Floor',
 'Total assets owned',
 'Total Value Held (ETH)',
 'Total Owners',
 'Total Supply']

@st.cache(allow_output_mutation=True)
def clean_data(p):

	# Clean data
    p.columns = cols
    p_filter=p[~p.Project.isin(blacklist)].copy()
    for ix,row in name_dict.iterrows():
        p_filter['Project'] = p_filter['Project'].str.replace(ix,row['Name'])
    p_filter.set_index('Project',inplace=True)
    p_filter = p_filter[~p_filter.index.duplicated(keep='first')]    
    return p_filter

@st.cache(allow_output_mutation=True)
def compute_diff(col_in,col_name_out,p_new_clean,p_old_clean):

	# Diff between timepoints
    p_cat=pd.concat([p_new_clean[col_in],p_old_clean[col_in]],axis=1).fillna(0)
    p_cat.columns=['new','old']
    p_cat[col_name_out]=(p_cat.new - p_cat.old) / p_cat.old
    return p_cat

@st.cache(allow_output_mutation=True)
def build_data(new,old):

	# Read data
	# TODO(rbarniker): Move to wgmi API
	p_new=pd.read_csv('Data/PROOF_%s.csv'%new,thousands=r',')
	p_old=pd.read_csv('Data/PROOF_%s.csv'%old,thousands=r',')

	# Clean
	p_new_clean=clean_data(p_new)
	p_old_clean=clean_data(p_old)

	# Diff 
	d_own=compute_diff('PROOF Owners Holding','% Change PROOF Owners',p_new_clean,p_old_clean)
	d_floor=compute_diff('Project Floor','% Change Floor',p_new_clean,p_old_clean)

	# Build table
	summary_table=pd.concat([p_new_clean,d_own['% Change PROOF Owners']],axis=1)
	summary_table=pd.concat([summary_table,d_floor['% Change Floor']],axis=1)

	# Change column names for vis
	show_cols=['PROOF Owners Holding','% Change PROOF Owners','Project Floor','% Change Floor','% PROOF Members Holding']
	summary_table=summary_table[show_cols]
	new_cols=['PROOF Holders','% Chg Holders','Floor','% Chg Floor','% PROOF Holding']
	summary_table.columns=new_cols
	summary_table.replace(np.inf, 0, inplace=True)
	return summary_table

# Format table columns 
def color_col(gb,col,table_view):
    
    out=pd.qcut(np.array(table_view[col].rank(method='first')),
                4,
                labels=['lowest','low','mid','top'])
    d=pd.DataFrame(table_view[col])
    d.index=out

    try:
        cellsytle_jscode = JsCode(
        """function(params) {
            if (params.value <= %s ) {
                return {
                    'color': 'white',
                    'backgroundColor': '#1E80C1'
                }
            } else if (params.value >= %s && params.value <= %s) {
                return {
                    'color': 'white',
                    'backgroundColor': '#A5DEF2'
                }
            } else if (params.value >= %s && params.value <= %s) {
                return {
                    'color': 'white',
                    'backgroundColor': '#FED8B1'
                }
            } else {
                return {
                    'color': 'white',
                    'backgroundColor': '#F07470'
                }
            }};"""%(d.loc['lowest'].max().values[0],
                    d.loc['low'].min().values[0],
                    d.loc['low'].max().values[0],
                    d.loc['mid'].min().values[0],
                    d.loc['mid'].max().values[0])
        )
    except:
            cellsytle_jscode = JsCode(
        """function(params) {
                return {
                    'color': 'white',
                    'backgroundColor': '#002947'
            }};"""
        )
            
    gb.configure_column(col, 
                        cellStyle=cellsytle_jscode)

# Build table 
new='051522'
old='042522' 
summary_table=build_data(new,old)

# Header 
st.title("PROOF Collective NFT Ownership")
st.info("Data from wgmi.io. Dashboard by @rbarniker. Comparing %s to %s"%(new,old))

# Filters
col1,col2 = st.columns(2) 

with col1:

	price = st.slider('Min current price (ETH)', min_value=0.01, max_value=10.0,value=1.0)
	table_view = summary_table[summary_table['Floor'] >= price] 

with col2:

	pct = st.slider('% Proof Members Holding', min_value=0.0, max_value=20.0,value=1.0)
	table_view = table_view[table_view['% PROOF Holding'] >= pct] 

# Prepare data for vis
table_view.sort_values('PROOF Holders',ascending=False,inplace=True)
table_view = table_view.round(3)
table_view=table_view.reset_index()

# Create table
gb = GridOptionsBuilder.from_dataframe(table_view)
gb.configure_pagination() 
color_col(gb,"PROOF Holders",table_view)
color_col(gb,'% Chg Holders',table_view)
color_col(gb,"Floor",table_view)
color_col(gb,"% Chg Floor",table_view)
color_col(gb,"% PROOF Holding",table_view)
gb.configure_selection(selection_mode="single", use_checkbox=True)
gridOptions = gb.build()
data = AgGrid(table_view,
	gridOptions=gridOptions,
	allow_unsafe_jscode=True,
	update_mode=GridUpdateMode.SELECTION_CHANGED)

# Selected project to highlight in scatterplot
try:
	proj = data["selected_rows"][0]['Project']
except IndexError:
	proj = table_view['Project'][0]

# Plot limits 
xmin=table_view['PROOF Holders'].min()
xmax=table_view['PROOF Holders'].max()
ymin=table_view['Floor'].min()
ymax=table_view['Floor'].max()

# Colors for floor 
c_labels = ['lowest','low','mid','top']
c_values = ['#1E80C1', '#A5DEF2', '#FED8B1','#F07470']
floor_chg=pd.qcut(np.array(table_view['% Chg Floor'].rank(method='first')),4,labels=c_labels)
table_view['% Chg Floor (cats)']=floor_chg

# Scatter plot 
points = alt.Chart(table_view).mark_point(filled=True,opacity=1).encode(
    x=alt.X('PROOF Holders:Q',scale=alt.Scale(domain=[xmin,xmax],type='log')),
    y=alt.Y('Floor:Q',scale=alt.Scale(domain=[ymin,ymax],type='log')),
    ).properties(
    width=700,
    height=700)
text = points.mark_text(
    align='left',
    baseline='middle',
    dx=7
).encode(
    text='Project'
).properties(
    width=700,
    height=700)

# Project highlight
table_view_highlight=pd.DataFrame(table_view[table_view.Project==proj])
points_highlight = alt.Chart(table_view_highlight).mark_point(filled=False,opacity=1,color='#F07470',size=50).encode(
    x=alt.X('PROOF Holders:Q',scale=alt.Scale(domain=[xmin,xmax],type='log')),
    y=alt.Y('Floor:Q',scale=alt.Scale(domain=[ymin,ymax],type='log')),
    ).properties(
    width=700,
    height=700)
text_highlight = points_highlight.mark_text(
    align='left',
    baseline='middle',
    dx=7,
    color="#F07470"
).encode(
    text='Project'
).properties(
    width=700,
    height=700)

# Create plot 
# Note: point scaling should be done after text is created 
st.altair_chart(points.encode(size='% Chg Holders',color=alt.Color('% Chg Floor (cats)',scale=alt.Scale(domain=c_labels, range=c_values))).interactive() + text + points_highlight + text_highlight,use_container_width=True)
