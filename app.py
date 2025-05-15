import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import folium
from streamlit_folium import folium_static
import json
import matplotlib as plt

# Configure the page
st.set_page_config(
    page_title="Mosquito Net Distribution Dashboard",
    page_icon="🦟",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1.2rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .st-emotion-cache-1r6slb0 {  /* Target metric value */
        font-size: 1.8rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# Cache data loading
@st.cache_data
def load_data():
    """Load and process the survey, campaign nets, and lost nets data"""
    survey_df = pd.read_csv('survey.csv')
    campnets_df = pd.read_csv('campnets.csv')
    lostnets_df = pd.read_csv('lostnets.csv')
    
    return survey_df, campnets_df, lostnets_df

# Load the data
survey_df, campnets_df, lostnets_df = load_data()

# Title
st.title("🦟 Vestergaard LLIN Durability Study")

# Sidebar
with st.sidebar:
    st.title("Dashboard Controls")
    
    st.markdown("""
    ### About this Dashboard
    This dashboard visualizes mosquito net distribution data across different districts
    and subcounties, including household visits, campaign nets distribution, and net loss tracking.
    """)
    
    # Get unique districts and subcounties
    districts = sorted(survey_df['selected_district'].unique()) if 'selected_district' in survey_df.columns else []
    selected_district = st.selectbox("Select District", ['All'] + districts)
    
    if selected_district != 'All':
        subcounties = sorted(survey_df[survey_df['selected_district'] == selected_district]['selected_subcounty'].unique()) if 'selected_subcounty' in survey_df.columns else []
        selected_subcounty = st.selectbox("Select Subcounty", ['All'] + subcounties)
    else:
        selected_subcounty = 'All'

# Filter data based on selection
def filter_data(df):
    if selected_district != 'All':
        df = df[df['selected_district'] == selected_district]
        if selected_subcounty != 'All':
            df = df[df['selected_subcounty'] == selected_subcounty]
    return df

filtered_survey = filter_data(survey_df)
total_households = len(filtered_survey)

# Calculate metrics first
total_villages = filtered_survey.groupby(['selected_village', 'selected_parish']).ngroups
total_campaign_nets = len(campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])])
total_lost_nets = len(lostnets_df[lostnets_df['hhid'].isin(filtered_survey['hhid'])])
lost_nets_percentage = (total_lost_nets / (total_lost_nets + total_campaign_nets)) * 100 if (total_lost_nets + total_campaign_nets) > 0 else 0

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Households Visited", 
        f"{total_households:,}",
        help="Number of households surveyed"
    )

with col2:
    st.metric(
        "Villages Visited", 
        f"{total_villages:,}",
        help="Number of unique villages visited during the survey (differentiated by parish when names are identical)"
    )

with col3:
    st.metric(
        "Campaign Nets Tagged", 
        f"{total_campaign_nets:,}",
        help="Total number of nets tagged during the campaign"
    )

with col4:
    st.metric(
        "Nets Lost (%)", 
        f"{lost_nets_percentage:.1f}%",
        help="Percentage of nets that were lost, damaged, or given away"
    )

st.markdown("---")

# Add Location Summary Section
st.header("Location Coverage Summary")

# Create three columns for district, subcounty, and village summaries
loc_col1, loc_col2 = st.columns(2)

with loc_col1:
    st.subheader("District Coverage")
    
    # District summary
    district_summary = survey_df['selected_district'].value_counts().reset_index()
    district_summary.columns = ['District', 'Number of Households']
    
    # District pie chart
    fig_district = px.pie(
        district_summary,
        values='Number of Households',
        names='District',
        title='Household Distribution by District',
        hole=0.4
    )
    fig_district.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_district, use_container_width=True, key="district_pie")
    
    # District frequency table
    st.markdown("#### District Frequency Table")
    st.dataframe(
        district_summary.style.background_gradient(cmap='Blues'),
        use_container_width=True
    )

with loc_col2:
    st.subheader("Subcounty Coverage")
    
    # Subcounty summary
    subcounty_summary = survey_df.groupby(['selected_district', 'selected_subcounty']).size().reset_index()
    subcounty_summary.columns = ['District', 'Subcounty', 'Number of Households']
    
    # Subcounty pie chart
    fig_subcounty = px.pie(
        subcounty_summary,
        values='Number of Households',
        names='Subcounty',
        title='Household Distribution by Subcounty',
        hole=0.4
    )
    fig_subcounty.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_subcounty, use_container_width=True, key="subcounty_pie")
    
    # Subcounty frequency table
    st.markdown("#### Subcounty Frequency Table")
    st.dataframe(
        subcounty_summary.style.background_gradient(cmap='Blues'),
        use_container_width=True
    )

# Village section in full width
st.subheader("Village Coverage")

# Village summary - including parish to differentiate villages
village_summary = filtered_survey.groupby(['selected_district', 'selected_subcounty', 'selected_parish', 'selected_village']).size().reset_index()
village_summary.columns = ['District', 'Subcounty', 'Parish', 'Village', 'Number of Households']

# Create a combined village name with parish for display
village_summary['Village_Display'] = village_summary.apply(
    lambda x: f"{x['Village']} ({x['Parish']})" if x['Village'] == 'PAROMO' else x['Village'],
    axis=1
)

# Verify total villages matches
assert total_villages == len(village_summary), "Village count mismatch between KPI and frequency table"

# Village bar chart
fig_village = px.bar(
    village_summary,
    x='Village_Display',
    y='Number of Households',
    title=f'Household Distribution by Village (Total Villages: {total_villages})',
    color='Number of Households',
    color_continuous_scale='Blues',
    labels={'Village_Display': 'Village (Parish)'}
)
fig_village.update_layout(
    xaxis_tickangle=-45,
    height=500  # Make the chart taller
)
st.plotly_chart(fig_village, use_container_width=True, key="village_bar")

# Village frequency table
st.markdown("#### Village Frequency Table")
# Add percentage calculation
village_summary['Percentage'] = (village_summary['Number of Households'] / village_summary['Number of Households'].sum() * 100).round(1)
village_summary['Percentage'] = village_summary['Percentage'].astype(str) + '%'

# Reorder columns for better readability
village_summary = village_summary[['District', 'Subcounty', 'Parish', 'Village', 'Number of Households', 'Percentage']]

# Display the table with custom width
st.dataframe(
    village_summary.style.background_gradient(cmap='Blues', subset=['Number of Households']),
    use_container_width=True,
    height=400  # Set a fixed height for the table
)

# Update the total villages metric to reflect the correct count
total_villages = len(village_summary)

# Update the villages metric in the KPI section
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_households = len(filtered_survey)
    st.metric(
        "Total Households Visited", 
        f"{total_households:,}",
        help="Number of households surveyed"
    )

with col2:
    st.metric(
        "Villages Visited", 
        f"{total_villages:,}",
        help="Number of unique villages visited during the survey (differentiated by parish when names are identical)"
    )

with col3:
    total_campaign_nets = len(campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])])
    st.metric(
        "Campaign Nets Tagged", 
        f"{total_campaign_nets:,}",
        help="Total number of nets tagged during the campaign"
    )

with col4:
    total_lost_nets = len(lostnets_df[lostnets_df['hhid'].isin(filtered_survey['hhid'])])
    lost_nets_percentage = (total_lost_nets / (total_lost_nets + total_campaign_nets)) * 100 if (total_lost_nets + total_campaign_nets) > 0 else 0
    st.metric(
        "Nets Lost (%)", 
        f"{lost_nets_percentage:.1f}%",
        help="Percentage of nets that were lost, damaged, or given away"
    )

st.markdown("---")

# Visualizations
col1, col2 = st.columns(2)

with col1:
    st.subheader("Net Distribution by Village")
    if 'selected_village' in filtered_survey.columns:
        village_dist = filtered_survey.groupby('selected_village').size().reset_index(name='households')
        fig = px.bar(
            village_dist,
            x='selected_village',
            y='households',
            title='Household Distribution by Village',
            labels={'households': 'Number of Households', 'selected_village': 'Village'},
            color='households',
            color_continuous_scale='Blues'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True, key="village_dist_bar")
    else:
        st.warning("Village data not available in the survey dataset")

with col2:
    # Filter campnets for the selected households
    filtered_campnets = campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])]
    
    if 'brand' in filtered_campnets.columns:
        st.subheader("Net Brand Distribution")
        # Create brand summary
        brand_summary = filtered_campnets['brand'].value_counts().reset_index()
        brand_summary.columns = ['Brand', 'Number of Nets']
        
        # Create pie chart for brand distribution
        fig_brand = px.pie(
            brand_summary,
            values='Number of Nets',
            names='Brand',
            title='Net Brand Distribution',
            hole=0.4,
            color_discrete_sequence=['#1f77b4', '#ff7f0e']  # Blue and Orange colors
        )
        fig_brand.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_brand, use_container_width=True, key="brand_pie")
        
        # Add brand frequency table below the chart
        st.markdown("##### Brand Frequency Table")
        # Add percentage column
        brand_summary['Percentage'] = (brand_summary['Number of Nets'] / brand_summary['Number of Nets'].sum() * 100).round(1)
        brand_summary['Percentage'] = brand_summary['Percentage'].astype(str) + '%'
        
        # Display the frequency table with styling
        st.dataframe(
            brand_summary.style.background_gradient(cmap='Blues', subset=['Number of Nets']),
            use_container_width=True
        )
        
        # Add total row
        st.markdown(f"**Total Nets: {brand_summary['Number of Nets'].sum():,}**")
    else:
        st.warning("Brand information not available in the dataset")

# Add Nets Lost Distribution Section
st.markdown("---")
st.header("Nets Lost Distribution")
lost_col1, lost_col2 = st.columns(2)

with lost_col1:
    st.subheader("Nets Lost vs Active")
    # Create a doughnut chart for nets lost percentage
    fig = go.Figure(data=[go.Pie(
        labels=['Lost Nets', 'Active Nets'],
        values=[total_lost_nets, total_campaign_nets - total_lost_nets],
        hole=0.7,
        marker_colors=['#FF9999', '#99FF99']
    )])
    fig.update_layout(
        title='Nets Lost vs Active Nets',
        annotations=[dict(text=f'{lost_nets_percentage:.1f}%', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    st.plotly_chart(fig, use_container_width=True, key="nets_lost_donut")

with lost_col2:
    st.subheader("Lost Nets Summary")
    # Create summary table for lost nets
    lost_summary = pd.DataFrame({
        'Category': ['Lost Nets', 'Active Nets', 'Total Nets'],
        'Count': [
            total_lost_nets,
            total_campaign_nets - total_lost_nets,
            total_campaign_nets
        ],
        'Percentage': [
            f"{lost_nets_percentage:.1f}%",
            f"{100 - lost_nets_percentage:.1f}%",
            "100%"
        ]
    })
    
    st.dataframe(
        lost_summary.style.background_gradient(cmap='RdYlGn_r', subset=['Count']),
        use_container_width=True
    )

st.markdown("---")

# Map visualization
st.subheader("Net Distribution Coverage Map")
if 'gpsloc' in survey_df.columns:
    try:
        # Extract latitude and longitude from gpsloc (taking only first two values)
        survey_df[['latitude', 'longitude']] = survey_df['gpsloc'].str.split(expand=True).iloc[:, :2].astype(float)
        
        # Create a map centered on the mean coordinates
        center_lat = survey_df['latitude'].mean()
        center_lon = survey_df['longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

        # Create a legend using Folium's HTML class
        legend = folium.Element("""
            <div class="legend" style="
                position: absolute;
                bottom: 30px;
                right: 10px;
                z-index: 9999;
                background-color: white;
                padding: 10px;
                border: 2px solid rgba(0,0,0,0.2);
                border-radius: 4px;
                font-family: Arial, sans-serif;
                ">
                <div style="text-align: center; margin-bottom: 5px;">
                    <b>Legend</b>
                </div>
                <div style="margin-bottom: 5px;">
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: green; margin-right: 5px;"></span>
                    <span>All Nets Active</span>
                </div>
                <div>
                    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: red; margin-right: 5px;"></span>
                    <span>Has Lost Nets</span>
                </div>
            </div>
            """)
        m.get_root().html.add_child(legend)
        
        # Add markers for each household
        for idx, row in survey_df.iterrows():
            # Count nets for this household
            household_nets = len(campnets_df[campnets_df['hhid'] == row['hhid']])
            household_lost = len(lostnets_df[lostnets_df['hhid'] == row['hhid']])
            
            # Create popup content
            popup_content = f"""
                <b>Household ID:</b> {row['hhid']}<br>
                <b>District:</b> {row['selected_district']}<br>
                <b>Subcounty:</b> {row['selected_subcounty']}<br>
                <b>Village:</b> {row['selected_village']}<br>
                <b>Nets Tagged:</b> {household_nets}<br>
                <b>Nets Lost:</b> {household_lost}
            """
            
            # Add marker with popup
            folium.CircleMarker(
                location=[row['latitude'], row['longitude']],
                radius=8,
                popup=popup_content,
                color='red' if household_lost > 0 else 'green',
                fill=True,
                fill_color='red' if household_lost > 0 else 'green'
            ).add_to(m)

        # Add custom CSS to ensure legend visibility
        css = """
        <style>
        .legend {
            background-color: white;
            padding: 10px;
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            z-index: 9999 !important;
            border: 2px solid rgba(0,0,0,0.2);
            border-radius: 4px;
            font-family: Arial, sans-serif;
        }
        </style>
        """
        m.get_root().html.add_child(folium.Element(css))
        
        # Display the map
        folium_static(m)
    except Exception as e:
        st.error(f"Error processing GPS coordinates: {str(e)}")
else:
    st.warning("GPS location data not available in the survey dataset")

st.markdown("---")
st.header("Campaign Net Distribution Analysis")

# Create a cross-tabulation of net counts
filtered_campnets = campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])]

# Merge with survey data to get village and subcounty information
net_distribution = pd.merge(
    filtered_campnets,
    filtered_survey[['hhid', 'selected_village', 'selected_subcounty', 'selected_district']],
    on='hhid',
    how='left'
)

# Create detailed frequency table
st.subheader("Detailed Net Distribution by Location and Brand")
net_freq_table = net_distribution.groupby(
    ['brand', 'selected_district', 'selected_subcounty', 'selected_village']
).size().reset_index(name='Net Count')

st.dataframe(
    net_freq_table.style.background_gradient(cmap='Blues', subset=['Net Count']),
    use_container_width=True
)

# Create summary tables with totals
st.subheader("Net Distribution Summary Tables")

# 1. District-level summary
district_summary = net_distribution.groupby(['selected_district', 'brand']).size().unstack(fill_value=0)
district_summary.loc['Total'] = district_summary.sum()
district_summary['Total'] = district_summary.sum(axis=1)

st.markdown("#### Distribution by District")
st.dataframe(
    district_summary.style.background_gradient(cmap='Blues', subset=pd.IndexSlice[:, district_summary.columns != 'Total'])
                          .format("{:,.0f}"),
    use_container_width=True
)

# 2. Subcounty-level summary
subcounty_summary = net_distribution.groupby(['selected_district', 'selected_subcounty', 'brand']).size().unstack(fill_value=0)
subcounty_summary.loc['Total'] = subcounty_summary.sum()
subcounty_summary['Total'] = subcounty_summary.sum(axis=1)

st.markdown("#### Distribution by Subcounty")
st.dataframe(
    subcounty_summary.style.background_gradient(cmap='Blues', subset=pd.IndexSlice[:, subcounty_summary.columns != 'Total'])
                            .format("{:,.0f}"),
    use_container_width=True
)

# 3. Village-level summary
village_summary = net_distribution.groupby(['selected_district', 'selected_subcounty', 'selected_village', 'brand']).size().unstack(fill_value=0)
village_summary.loc['Total'] = village_summary.sum()
village_summary['Total'] = village_summary.sum(axis=1)

st.markdown("#### Distribution by Village")
st.dataframe(
    village_summary.style.background_gradient(cmap='Blues', subset=pd.IndexSlice[:, village_summary.columns != 'Total'])
                         .format("{:,.0f}"),
    use_container_width=True
)

# 4. Overall Brand Summary
st.markdown("#### Overall Brand Distribution")
brand_summary = pd.DataFrame({
    'Net Count': net_distribution['brand'].value_counts(),
    'Percentage': (net_distribution['brand'].value_counts(normalize=True) * 100).round(1)
})
brand_summary.loc['Total'] = [brand_summary['Net Count'].sum(), 100.0]

st.dataframe(
    brand_summary.style.background_gradient(cmap='Blues', subset=['Net Count'])
                       .format({
                           'Net Count': '{:,.0f}',
                           'Percentage': '{:.1f}%'
                       }),
    use_container_width=True
)

# Add a bar chart showing distribution by subcounty and brand
subcounty_brand_dist = net_distribution.groupby(['selected_subcounty', 'brand']).size().reset_index(name='Net Count')

fig2 = px.bar(
    subcounty_brand_dist,
    x='selected_subcounty',
    y='Net Count',
    color='brand',
    title='Net Distribution by Subcounty and Brand',
    labels={
        'selected_subcounty': 'Subcounty',
        'Net Count': 'Number of Nets',
        'brand': 'Brand'
    }
)
fig2.update_layout(
    xaxis_tickangle=-45,
    barmode='group'
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# Map visualization continues below... 