import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64
from db import get_campaign_by_share_token

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Client Campaign View",
    page_icon="🔗",
    layout="wide",
    # Hide the sidebar and menu to prevent navigation to other pages
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Add CSS to hide the sidebar completely and remove other navigation elements
st.markdown("""
<style>
    /* Hide sidebar */
    [data-testid="collapsedControl"] {
        display: none;
    }
    
    /* Hide full-screen button */
    .fullScreenFrame > div {
        display: none !important;
    }
    
    /* Hide Streamlit menu and footer */
    #MainMenu {
        visibility: hidden;
    }
    footer {
        visibility: hidden;
    }
    
    /* Make sure the sidebar is fully collapsed */
    section[data-testid="stSidebar"] {
        width: 0px !important;
        margin-right: 0px !important;
        display: none !important;
    }
    
    /* Prevent interaction with sidebar */
    .stSidebar {
        pointer-events: none;
    }
    
    /* Style the download button to match Streamlit buttons */
    .download-button {
        display: inline-block;
        padding: 0.25em 0.75em;
        background-color: #0e1117;
        color: #fafafa;
        text-align: center;
        text-decoration: none;
        font-weight: 400;
        font-size: 0.875rem;
        border-radius: 0.25rem;
        border: 1px solid #3b3e46;
        cursor: pointer;
        line-height: 1.6;
        user-select: none;
        transition: color 150ms ease 0s, border-color 150ms ease 0s, background-color 150ms ease 0s;
    }
    .download-button:hover {
        border-color: rgb(128, 132, 149);
        color: rgb(255, 255, 255);
    }
</style>
""", unsafe_allow_html=True)

# Helper function for CSV export
def get_csv_download_link(campaign, filtered_df=None):
    """Generate a CSV and return a download link"""
    # Use filtered data if available, otherwise use all influencers
    if filtered_df is not None and not filtered_df.empty:
        df = filtered_df.copy()
    else:
        df = pd.DataFrame(campaign['influencers'])
    
    # Convert to CSV
    csv = df.to_csv(index=False)
    
    # Create base64 encoded string
    b64_csv = base64.b64encode(csv.encode()).decode()
    
    # Create download link
    href = f'<a style="text-decoration: none;" href="data:text/csv;base64,{b64_csv}" download="{campaign["name"]}_influencers.csv" class="download-button">Download Data</a>'
    
    return href

# Get the share token from the query params using the non-experimental API
token = st.query_params.get("token", None)

if not token:
    st.error("No share token provided in the URL.")
    st.stop()

# Get campaign data by token directly from database
campaign = get_campaign_by_share_token(token)

if not campaign:
    st.error("Invalid or expired share token. Please check your link.")
    st.stop()

# Use campaign name as the page title
st.title(f"{campaign['name']}")

# Get sharing settings (with defaults)
sharing_settings = campaign.get('sharing_settings', {
    'include_dashboard': True,
    'include_metrics': True,
    'include_costs': False,
    'include_influencer_details': True,
    'include_engagement_metrics': True,
    'client_name': '',
    'custom_message': ''
})

# Use default settings if sharing_settings is None
if sharing_settings is None:
    sharing_settings = {
        'include_dashboard': True,
        'include_metrics': True,
        'include_costs': False,
        'include_influencer_details': True,
        'include_engagement_metrics': True,
        'client_name': '',
        'custom_message': ''
    }

# Show client header
if sharing_settings.get('client_name'):
    st.write(f"**Prepared for:** {sharing_settings['client_name']}")

st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")

if sharing_settings.get('custom_message'):
    st.info(sharing_settings['custom_message'])

# Store filtered_df for export
filtered_df = None

# Show metrics if enabled
if sharing_settings.get('include_metrics', True):
    st.subheader("Campaign Performance")
    
    # Create budget display section
    budget = campaign.get('budget', 0)
    
    # First row of metrics - Views and other key metrics
    metric_cols1 = st.columns(3)
    with metric_cols1[0]:
        st.metric("Budget", f"₹{budget:,.2f}")
    with metric_cols1[1]:
        st.metric("Total Views", f"{campaign['metrics']['total_views']:,}")
    with metric_cols1[2]:
        st.metric("Total Likes", f"{campaign['metrics'].get('total_likes', 0):,}")
    
    # Show engagement metrics if enabled
    if sharing_settings.get('include_engagement_metrics', True):
        # Second row of metrics for engagement
        metric_cols2 = st.columns(2)
        with metric_cols2[0]:
            st.metric("Total Shares", f"{campaign['metrics'].get('total_shares', 0):,}")
        with metric_cols2[1]:
            st.metric("Total Comments", f"{campaign['metrics'].get('total_comments', 0):,}")

# Show dashboard/charts if enabled and influencers exist
if sharing_settings.get('include_dashboard', True) and campaign['influencers']:
    st.subheader("Performance Charts")
    
    # Create dataframe from influencers
    influencers_df = pd.DataFrame(campaign['influencers'])
    
    chart_cols = st.columns(2)
    
    with chart_cols[0]:
        # Platform distribution pie chart - Added from Campaign Dashboard
        platform_counts = influencers_df['platform'].value_counts().reset_index()
        platform_counts.columns = ['Platform', 'Count']

        fig_platform = px.pie(
            platform_counts,
            values='Count',
            names='Platform',
            title='Influencers by Platform',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_platform, use_container_width=True)
    
    with chart_cols[1]:
        # Views by platform
        platform_views = influencers_df.groupby('platform')['views'].sum().reset_index()
        
        fig_views = px.bar(
            platform_views,
            x='platform',
            y='views',
            title='Views by Platform',
            labels={'platform': 'Platform', 'views': 'Views'},
            color='platform',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_views, use_container_width=True)
    
    # Show engagement charts if enabled
    if sharing_settings.get('include_engagement_metrics', True):
        st.subheader("Engagement Analysis") # Added subheader for clarity
        engagement_cols = st.columns(2)
        
        with engagement_cols[0]:
            # Engagement by platform
            platform_engagement = influencers_df.groupby('platform').agg({
                'likes': 'sum',
                'shares': 'sum',
                'comments': 'sum'
            }).reset_index()
            
            # Reshape for plotting
            platform_engagement_melted = pd.melt(
                platform_engagement,
                id_vars=['platform'],
                value_vars=['likes', 'shares', 'comments'],
                var_name='Engagement Type',
                value_name='Count'
            )
            
            fig_engagement = px.bar(
                platform_engagement_melted,
                x='platform',
                y='Count',
                color='Engagement Type',
                title='Engagement by Platform',
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_engagement, use_container_width=True)
        
        with engagement_cols[1]:
            # Budget efficiency - Views per theoretical budget allocation - Added from Campaign Dashboard
            total_views = influencers_df['views'].sum()
            campaign_budget = campaign.get('budget', 0) # Use campaign variable

            if total_views > 0 and campaign_budget > 0:
                # Calculate views per rupee
                views_per_rupee = total_views / campaign_budget

                # Create a gauge chart for budget efficiency
                fig_views_per_rupee = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=views_per_rupee,
                    title={'text': "Views per ₹"},
                    gauge={
                        'axis': {'range': [0, views_per_rupee * 2]},
                        'bar': {'color': "lightblue"},
                        'steps': [
                            {'range': [0, views_per_rupee/2], 'color': "lightgray"},
                            {'range': [views_per_rupee/2, views_per_rupee * 1.5], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': views_per_rupee * 1.5
                        }
                    }
                ))
                st.plotly_chart(fig_views_per_rupee, use_container_width=True)
            else:
                st.info("Need views and budget to calculate efficiency")

# Show influencer details if enabled
if sharing_settings.get('include_influencer_details', True) and campaign['influencers']:
    st.subheader("Campaign Influencers")
    
    # Create display dataframe
    influencers_df = pd.DataFrame(campaign['influencers'])
    
    # Add filtering capabilities for clients
    filter_cols = st.columns(3)
    
    with filter_cols[0]:
        filter_platform = st.selectbox(
            "Filter by Platform",
            ["All"] + list(influencers_df['platform'].unique()),
            key="platform_filter"
        )
    
    with filter_cols[1]:
        filter_post_type = st.selectbox(
            "Filter by Post Type",
            ["All"] + list(influencers_df['post_type'].unique()),
            key="post_type_filter"
        )
    
    with filter_cols[2]:
        sort_options = ["Name", "Views"]
        if sharing_settings.get('include_engagement_metrics', True):
            sort_options.extend(["Likes", "Shares", "Comments"])
        #if sharing_settings.get('include_costs', False):
         #   sort_options.append("Investment")
        
        sort_by = st.selectbox("Sort By", sort_options, key="sort_by_filter")
    
    # Apply filters and sorting
    filtered_df = influencers_df.copy()
    
    if filter_platform != "All":
        filtered_df = filtered_df[filtered_df['platform'] == filter_platform]
    
    if filter_post_type != "All":
        filtered_df = filtered_df[filtered_df['post_type'] == filter_post_type]
    
    # Apply sorting
    if sort_by == "Name":
        filtered_df = filtered_df.sort_values('name')
    elif sort_by == "Views":
        filtered_df = filtered_df.sort_values('views', ascending=False)
    elif sort_by == "Likes":
        filtered_df = filtered_df.sort_values('likes', ascending=False)
    elif sort_by == "Shares":
        filtered_df = filtered_df.sort_values('shares', ascending=False)
    elif sort_by == "Comments":
        filtered_df = filtered_df.sort_values('comments', ascending=False)
    #elif sort_by == "Investment":
     #   filtered_df = filtered_df.sort_values('cost', ascending=False)
    
    # Display filtered results
    if not filtered_df.empty:
        # Select columns to display
        display_columns = ['name', 'platform', 'post_type', 'views']
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            display_columns.extend(['likes', 'shares', 'comments'])
        
        #if sharing_settings.get('include_costs', False):
         #   display_columns.append('cost')
        
        if 'post_url' in filtered_df.columns and any(not pd.isna(url) for url in filtered_df['post_url']):
            display_columns.append('post_url')
        
        # Create a clean display dataframe with only selected columns
        filtered_display_df = filtered_df[display_columns].copy()
        
        # Rename columns for display
        column_map = {
            'name': 'Name',
            'platform': 'Platform',
            'post_type': 'Post Type', 
            'views': 'Views',
            #'cost': 'Investment (₹)',
            'post_url': 'Post URL',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
        filtered_display_df.columns = [column_map.get(col, col) for col in filtered_display_df.columns]
        
        # Format numeric columns
        if 'Views' in filtered_display_df.columns:
            filtered_display_df['Views'] = filtered_display_df['Views'].apply(lambda x: f"{x:,}")
        
        #if 'Investment (₹)' in filtered_display_df.columns:
         #   filtered_display_df['Investment (₹)'] = filtered_display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}")
        
        if 'Likes' in filtered_display_df.columns:
            filtered_display_df['Likes'] = filtered_display_df['Likes'].apply(lambda x: f"{x:,}")
        
        if 'Shares' in filtered_display_df.columns:
            filtered_display_df['Shares'] = filtered_display_df['Shares'].apply(lambda x: f"{x:,}")
        
        if 'Comments' in filtered_display_df.columns:
            filtered_display_df['Comments'] = filtered_display_df['Comments'].apply(lambda x: f"{x:,}")
        
        # Calculate filtered totals
        filtered_totals = {
            'Name': 'TOTAL',
            'Platform': '',
            'Post Type': '',
            'Views': f"{filtered_df['views'].sum():,}"
        }
        
        #if 'Investment (₹)' in filtered_display_df.columns:
         #   filtered_totals['Investment (₹)'] = f"₹{filtered_df['cost'].sum():,.2f}"
        
        if 'Likes' in filtered_display_df.columns:
            filtered_totals['Likes'] = f"{filtered_df['likes'].sum():,}"
        
        if 'Shares' in filtered_display_df.columns:
            filtered_totals['Shares'] = f"{filtered_df['shares'].sum():,}"
        
        if 'Comments' in filtered_display_df.columns:
            filtered_totals['Comments'] = f"{filtered_df['comments'].sum():,}"
        
        # Add totals row
        filtered_display_df = pd.concat([filtered_display_df, pd.DataFrame([filtered_totals])], ignore_index=True)
        
        # Show record count and display the dataframe
        st.write(f"Showing {len(filtered_df)} influencers")
        st.dataframe(filtered_display_df, use_container_width=True)
    else:
        st.info("No influencers match your filter criteria")

elif not campaign['influencers']:
    st.info("No influencers added to this campaign yet.")

# Add direct CSV Download button
if campaign['influencers']:
    st.subheader("Export Data")
    
    # Create columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write("Download the current data to use in Excel or other spreadsheet applications.")
    
    with col2:
        # Generate the download link directly
        download_link = get_csv_download_link(campaign, filtered_df)
        st.markdown(download_link, unsafe_allow_html=True)

# Add contact information section
st.subheader("Contact Information")
st.write("If you have any questions about this report, please contact your campaign manager.")

# Footer
st.markdown("---")
st.markdown("Campaign Manager v1.0 | Client view")

# Add a hidden back button that we'll control with CSS
# This is just for better UX in case someone needs to go back
st.markdown("""
<div style="position: fixed; top: 10px; right: 10px;">
    <a href="javascript:history.back()" style="text-decoration: none; color: #666; background-color: #f5f5f5; 
       padding: 5px 10px; border-radius: 4px; font-size: 14px;">
        Back to Campaign Manager
    </a>
</div>
""", unsafe_allow_html=True)