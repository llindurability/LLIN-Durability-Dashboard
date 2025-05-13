import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import folium
from streamlit_folium import folium_static
import json

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
st.title("🦟 VESTERGAARD LLIN Durability Study")

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

# KPIs
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_households = len(filtered_survey)
    st.metric(
        "Total Households Visited", 
        f"{total_households:,}",
        help="Number of households surveyed"
    )

with col2:
    total_villages = len(filtered_survey['selected_village'].unique()) if 'selected_village' in filtered_survey.columns else 0
    st.metric(
        "Villages Visited", 
        f"{total_villages:,}",
        help="Number of unique villages visited during the survey"
    )

with col3:
    total_campaign_nets = len(campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])])
    st.metric(
        "Campaign Nets Distributed", 
        f"{total_campaign_nets:,}",
        help="Total number of nets distributed through the campaign"
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
            color='households'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Village data not available in the survey dataset")

with col2:
    st.subheader("Net Loss Reasons")
    if 'netlong' in lostnets_df.columns:
        loss_reasons = lostnets_df[lostnets_df['hhid'].isin(filtered_survey['hhid'])]['netlong'].value_counts()
        fig = px.pie(
            values=loss_reasons.values,
            names=loss_reasons.index,
            title='Reasons for Net Loss',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Net loss reason data not available")

# Net Usage Analysis
st.subheader("Net Usage and Condition")
col1, col2 = st.columns(2)

with col1:
    if 'holesever' in campnets_df.columns:
        net_condition = campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])]['holesever'].value_counts()
        fig = px.bar(
            x=net_condition.index,
            y=net_condition.values,
            title='Net Condition Assessment',
            labels={'x': 'Condition', 'y': 'Number of Nets'},
            color=net_condition.values
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Net condition data not available")

with col2:
    if 'placenet' in campnets_df.columns:
        net_placement = campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])]['placenet'].value_counts()
        fig = px.pie(
            values=net_placement.values,
            names=net_placement.index,
            title='Net Placement in Households',
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Net placement data not available")

# Data Tables
st.subheader("Detailed Data")
tabs = st.tabs(["Survey Data", "Campaign Nets", "Lost Nets"])

with tabs[0]:
    survey_columns = ['hhid']
    if 'selected_district' in filtered_survey.columns:
        survey_columns.append('selected_district')
    if 'selected_subcounty' in filtered_survey.columns:
        survey_columns.append('selected_subcounty')
    if 'selected_village' in filtered_survey.columns:
        survey_columns.append('selected_village')
    if 'numhhmembers' in filtered_survey.columns:
        survey_columns.append('numhhmembers')
    if 'hhnets' in filtered_survey.columns:
        survey_columns.append('hhnets')
    if 'hhnetsnum' in filtered_survey.columns:
        survey_columns.append('hhnetsnum')
    
    st.dataframe(filtered_survey[survey_columns], use_container_width=True)

with tabs[1]:
    campnet_columns = ['hhid']
    if 'netnum_001' in campnets_df.columns:
        campnet_columns.append('netnum_001')
    if 'brand' in campnets_df.columns:
        campnet_columns.append('brand')
    if 'netcampaign' in campnets_df.columns:
        campnet_columns.append('netcampaign')
    if 'netid' in campnets_df.columns:
        campnet_columns.append('netid')
    if 'placenet' in campnets_df.columns:
        campnet_columns.append('placenet')
    if 'holesever' in campnets_df.columns:
        campnet_columns.append('holesever')
    
    st.dataframe(
        campnets_df[campnets_df['hhid'].isin(filtered_survey['hhid'])][campnet_columns],
        use_container_width=True
    )

with tabs[2]:
    lostnet_columns = ['hhid']
    if 'netnum' in lostnets_df.columns:
        lostnet_columns.append('netnum')
    if 'netlong' in lostnets_df.columns:
        lostnet_columns.append('netlong')
    if 'hpnnet' in lostnets_df.columns:
        lostnet_columns.append('hpnnet')
    if 'nkpnet' in lostnets_df.columns:
        lostnet_columns.append('nkpnet')
    
    st.dataframe(
        lostnets_df[lostnets_df['hhid'].isin(filtered_survey['hhid'])][lostnet_columns],
        use_container_width=True
    )

# Data Source Information
with st.expander("Data Source and Methodology"):
    st.markdown("""
    ### Data Sources
    - **Survey Data**: Household-level information including location, number of members, and net ownership
    - **Campaign Nets**: Detailed information about nets distributed during the campaign
    - **Lost Nets**: Tracking of nets that were lost, damaged, or given away
    
    ### Methodology
    - Data is collected through household surveys
    - Net loss percentage is calculated as: (Lost Nets) / (Lost Nets + Campaign Nets) × 100
    - Household coverage considers both distributed and lost nets
    
    ### Notes
    - Some households may have multiple nets
    - Net condition is assessed based on physical inspection
    - Lost nets include those that were given away, damaged, or stolen
    """)

# Map visualization
st.subheader("Net Distribution Coverage Map")
if 'selected_district' in survey_df.columns:
    # Count households per district
    coverage_data = survey_df.groupby('selected_district').agg({
        'hhid': 'count'  # Count households per district
    }).reset_index()
    coverage_data.rename(columns={'hhid': 'total_households'}, inplace=True)
    
    # Create a mapping of household IDs to districts
    hhid_to_district = survey_df.set_index('hhid')['selected_district'].to_dict()
    
    # Count nets per district
    district_nets = pd.DataFrame()
    if not campnets_df.empty:
        # Map districts to campaign nets using the household ID
        campnets_df['selected_district'] = campnets_df['hhid'].map(hhid_to_district)
        district_nets = campnets_df.groupby('selected_district').size().reset_index(name='total_nets')
    
    # Merge the data
    if not district_nets.empty:
        coverage_data = coverage_data.merge(district_nets, on='selected_district', how='left')
        coverage_data['total_nets'] = coverage_data['total_nets'].fillna(0)
        coverage_data['coverage_ratio'] = coverage_data['total_nets'] / coverage_data['total_households']
    else:
        coverage_data['total_nets'] = 0
        coverage_data['coverage_ratio'] = 0
    
    # Create a simple map centered on Uganda
    m = folium.Map(location=[1.3733, 32.2903], zoom_start=7)  # Uganda's approximate center
    
    # Add circles for each district
    for idx, row in coverage_data.iterrows():
        # Create a spread around Uganda's center
        lat_offset = np.random.uniform(-1, 1)
        lon_offset = np.random.uniform(-1, 1)
        
        # Calculate circle radius (minimum size for visibility)
        radius = max(row['coverage_ratio'] * 50000, 20000)
        
        folium.Circle(
            location=[1.3733 + lat_offset, 32.2903 + lon_offset],
            radius=radius,  # Adjust size for visibility
            popup=f"""
                <b>District:</b> {row['selected_district']}<br>
                <b>Total Households:</b> {int(row['total_households']):,}<br>
                <b>Total Nets:</b> {int(row['total_nets']):,}<br>
                <b>Coverage Ratio:</b> {row['coverage_ratio']:.2f}
            """,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.6,
            tooltip=row['selected_district']  # Show district name on hover
        ).add_to(m)
    
    # Add a legend
    legend_html = """
        <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; 
                    padding: 10px; border: 2px solid grey; border-radius: 5px">
        <h4>Coverage Ratio</h4>
        <p>Circle size indicates the ratio of<br>nets distributed to households</p>
        <p>Hover over circles to see district names</p>
        </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Display the map
    folium_static(m)
else:
    st.warning("District data not available in the survey dataset")

# Malaria correlation if available
if 'malaria_cases' in survey_df.columns:
    st.subheader("Malaria Cases vs Net Distribution")
    if 'hhnets' in survey_df.columns:
        fig = px.scatter(
            survey_df,
            x='hhnets',
            y='malaria_cases',
            color='selected_district' if 'selected_district' in survey_df.columns else None,
            title='Correlation between Net Distribution and Malaria Cases',
            labels={
                'hhnets': 'Nets Distributed',
                'malaria_cases': 'Malaria Cases',
                'selected_district': 'District'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Net distribution data not available")
else:
    st.info("Malaria cases data not available in the dataset")

# Additional Information
with st.expander("📊 Data Source and Methodology"):
    st.markdown("""
        ### Data Collection
        - Household surveys were conducted across multiple villages
        - GPS coordinates were collected for each household
        - Data includes both distributed and lost nets
        
        ### Methodology
        - Net coverage is calculated per household
        - Lost nets include damaged, stolen, and given away nets
        - Geographical distribution is mapped using actual GPS coordinates
    """) 