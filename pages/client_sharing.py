import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
from datetime import datetime
from db import save_campaign

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Client Sharing",
    page_icon="🔗",
    layout="wide"
)

# Hide Streamlit's default GitHub link and menu
hide_streamlit_elements = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Hide the "Client View" link in the sidebar */
[data-testid="stSidebarNav"] a[href*="client_view"] {
    display: none;
}
</style>
"""
st.markdown(hide_streamlit_elements, unsafe_allow_html=True)

# Check if session state is initialized
if 'campaigns' not in st.session_state or 'current_campaign_id' not in st.session_state:
    st.error("Please navigate to the main page first to select or create a campaign.")
    st.stop()

# Check if a campaign is selected
if st.session_state.current_campaign_id is None:
    st.warning("No campaign selected. Please return to the main page and select a campaign.")
    if st.button("Go to Home"):
        st.switch_page("app.py")
    st.stop()

# Get current campaign data
current_campaign = st.session_state.campaigns[st.session_state.current_campaign_id]

# Helper function to save campaign data
def save_campaign_data():
    """Save campaign data to database"""
    save_campaign(current_campaign)

# Page header
st.title(f"Client Sharing: {current_campaign['name']}")

# Create tabs for different sections
tab1, tab2 = st.tabs(["Sharing Settings", "Preview Client View"])

with tab1:
    st.header("Configure Sharing Settings")
    
    # Display current token
    col1, col2 = st.columns([3, 1])
    
    with col1:
        current_token = current_campaign.get('share_token', str(uuid.uuid4())[:8])
        st.subheader("Share Token")
        st.code(current_token, language="text")
        
        # Generate full shareable link with domain
        full_share_link = f"https://ltcomedia.streamlit.app/client_view?token={current_token}"
        
        # Display link
        st.subheader("Shareable Link")
        
        # Display the full URL in a code block
        st.code(full_share_link, language="text")
        
        # Add a direct link option
        st.markdown(
            f"""
            <a href="{full_share_link}" target="_blank" style="display: inline-block; margin-top: 5px; text-decoration: none;">
                <button style="background-color: #4CAF50; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer;">
                    Open Client View
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        
        st.info("Share this link with your client to give them access to the campaign view")
    
    with col2:
        if st.button("Generate New Token"):
            # Generate new token
            new_token = str(uuid.uuid4())[:8]
            current_campaign['share_token'] = new_token
            save_campaign_data()
            st.success("New token generated!")
            st.rerun()
    
    # Share permissions
    st.subheader("Share Permissions")
    
    # Initialize sharing_settings if it doesn't exist or is None
    if 'sharing_settings' not in current_campaign or current_campaign['sharing_settings'] is None:
        current_campaign['sharing_settings'] = {
            'include_dashboard': True,
            'include_metrics': True,
            'include_budget': False,
            'include_influencer_details': True,
            'include_engagement_metrics': True,
            'expiry_date': None,
            'access_count': 0,
            'client_name': '',
            'custom_message': ''
        }
    
    # Now we can safely use .get() on sharing_settings
    sharing_settings = current_campaign['sharing_settings']
    
    # Dashboard permission
    include_dashboard = st.checkbox(
        "Include Campaign Dashboard", 
        value=sharing_settings.get('include_dashboard', True),
        help="Show performance charts and metrics"
    )
    
    # Metrics permission
    include_metrics = st.checkbox(
        "Include Campaign Metrics", 
        value=sharing_settings.get('include_metrics', True),
        help="Show views and other performance metrics"
    )
    
    # Engagement metrics permission
    include_engagement_metrics = st.checkbox(
        "Include Engagement Metrics", 
        value=sharing_settings.get('include_engagement_metrics', True),
        help="Show likes, shares, and comments metrics"
    )
    
    # Budget permission
    include_budget = st.checkbox(
        "Include Budget Information", 
        value=sharing_settings.get('include_budget', False),
        help="Show campaign budget information"
    )
    
    # Influencer details permission
    include_influencer_details = st.checkbox(
        "Include Influencer Details", 
        value=sharing_settings.get('include_influencer_details', True),
        help="Show detailed information about each influencer"
    )
    
    # Expiry date
    col1, col2 = st.columns(2)
    
    with col1:
        set_expiry = st.checkbox(
            "Set Expiry Date", 
            value=sharing_settings.get('expiry_date') is not None
        )
    
    with col2:
        expiry_date = None
        if set_expiry:
            expiry_date = st.date_input(
                "Expiry Date", 
                value=datetime.now().date()
            )
    
    # Client information
    st.subheader("Client Information")
    
    client_name = st.text_input(
        "Client Name", 
        value=sharing_settings.get('client_name', '')
    )
    
    custom_message = st.text_area(
        "Custom Message to Client", 
        value=sharing_settings.get('custom_message', ''),
        help="This message will be displayed at the top of the client view"
    )
    
    # Save settings
    if st.button("Save Sharing Settings"):
        current_campaign['sharing_settings'] = {
            'include_dashboard': include_dashboard,
            'include_metrics': include_metrics,
            'include_engagement_metrics': include_engagement_metrics,
            'include_budget': include_budget,
            'include_influencer_details': include_influencer_details,
            'expiry_date': expiry_date.strftime("%Y-%m-%d") if expiry_date else None,
            'access_count': sharing_settings.get('access_count', 0),
            'client_name': client_name,
            'custom_message': custom_message
        }
        
        save_campaign_data()
        st.success("Sharing settings saved successfully!")

with tab2:
    st.header("Client View Preview")
    
    # Get sharing settings
    sharing_settings = current_campaign.get('sharing_settings', {})
    
    # Use default settings if sharing_settings is None
    if sharing_settings is None:
        sharing_settings = {
            'include_dashboard': True,
            'include_metrics': True,
            'include_engagement_metrics': True,
            'include_budget': False,
            'include_influencer_details': True,
            'client_name': '',
            'custom_message': ''
        }
    
    # Show client header
    st.subheader("Campaign Report")
    st.write(f"**Campaign:** {current_campaign['name']}")
    
    if sharing_settings.get('client_name'):
        st.write(f"**Prepared for:** {sharing_settings['client_name']}")
    
    st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
    
    if sharing_settings.get('custom_message'):
        st.info(sharing_settings['custom_message'])
    
    # Show metrics if enabled
    if sharing_settings.get('include_metrics', True):
        st.subheader("Campaign Performance")
        
        # First row of metrics
        metric_cols1 = st.columns(2 if sharing_settings.get('include_budget', False) else 1)
        
        with metric_cols1[0]:
            st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
        
        if sharing_settings.get('include_budget', False):
            with metric_cols1[1]:
                st.metric("Campaign Budget", f"₹{current_campaign.get('budget', 0):,.2f}")
        
        # Show engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            # Second row of metrics for engagement
            metric_cols2 = st.columns(3)
            with metric_cols2[0]:
                st.metric("Total Likes", f"{current_campaign['metrics'].get('total_likes', 0):,}")
            with metric_cols2[1]:
                st.metric("Total Shares", f"{current_campaign['metrics'].get('total_shares', 0):,}")
            with metric_cols2[2]:
                st.metric("Total Comments", f"{current_campaign['metrics'].get('total_comments', 0):,}")
    
    # Show dashboard if enabled
    if sharing_settings.get('include_dashboard', True) and current_campaign["influencers"]:
        st.subheader("Campaign Analytics")
        
        # Convert influencers list to DataFrame
        influencers_df = pd.DataFrame(current_campaign["influencers"])
        
        # Charts Row 1
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Platform distribution pie chart
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
        
        with chart_col2:
            # Post type distribution
            post_counts = influencers_df['post_type'].value_counts().reset_index()
            post_counts.columns = ['Post Type', 'Count']
            
            fig_post = px.bar(
                post_counts,
                x='Post Type',
                y='Count',
                title='Content by Post Type',
                color='Post Type',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_post, use_container_width=True)
        
        # Show engagement charts if enabled
        if sharing_settings.get('include_engagement_metrics', True):
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
        
        # Show budget charts if enabled
        if sharing_settings.get('include_budget', False) and current_campaign.get('budget', 0) > 0:
            budget_cols = st.columns(2)
            
            with budget_cols[0]:
                # Budget overview
                fig_budget = go.Figure()
                fig_budget.add_trace(go.Indicator(
                    mode="number+delta",
                    value=current_campaign.get('budget', 0),
                    title={"text": "Campaign Budget (₹)"},
                    domain={'x': [0, 1], 'y': [0, 1]}
                ))
                st.plotly_chart(fig_budget, use_container_width=True)
            
            with budget_cols[1]:
                # Budget efficiency (views per rupee)
                if current_campaign['metrics']['total_views'] > 0:
                    views_per_rupee = current_campaign['metrics']['total_views'] / current_campaign.get('budget', 1)
                    
                    fig_efficiency = go.Figure()
                    fig_efficiency.add_trace(go.Indicator(
                        mode="number",
                        value=views_per_rupee,
                        title={"text": "Views per ₹"},
                        domain={'x': [0, 1], 'y': [0, 1]}
                    ))
                    st.plotly_chart(fig_efficiency, use_container_width=True)
    
    # Show influencer details if enabled
    if sharing_settings.get('include_influencer_details', True) and current_campaign["influencers"]:
        st.subheader("Campaign Influencers")
        
        # Create display dataframe
        influencers_df = pd.DataFrame(current_campaign["influencers"])
        
        # Select columns to display
        display_columns = ['name', 'platform', 'post_type', 'views']
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            display_columns.extend(['likes', 'shares', 'comments'])
        
        if 'post_url' in influencers_df.columns:
            display_columns.append('post_url')
        
        # Create a clean display dataframe with only selected columns
        display_df = influencers_df[display_columns].copy()
        
        # Rename columns for display
        column_map = {
            'name': 'Name',
            'platform': 'Platform',
            'post_type': 'Post Type',
            'views': 'Views',
            'post_url': 'Post URL',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
        display_df.columns = [column_map.get(col, col) for col in display_df.columns]
        
        # Format numeric columns
        if 'Views' in display_df.columns:
            display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
        
        if 'Likes' in display_df.columns:
            display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}")
        
        if 'Shares' in display_df.columns:
            display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}")
        
        if 'Comments' in display_df.columns:
            display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}")
        
        # Calculate totals
        totals = {
            'Name': 'TOTAL',
            'Platform': '',
            'Post Type': '',
            'Views': f"{influencers_df['views'].sum():,}"
        }
        
        if 'Likes' in display_df.columns:
            totals['Likes'] = f"{influencers_df['likes'].sum():,}"
        
        if 'Shares' in display_df.columns:
            totals['Shares'] = f"{influencers_df['shares'].sum():,}"
        
        if 'Comments' in display_df.columns:
            totals['Comments'] = f"{influencers_df['comments'].sum():,}"
        
        # Add totals row
        display_df = pd.concat([display_df, pd.DataFrame([totals])], ignore_index=True)
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
    
    # Download PDF report option
    st.subheader("Download Report")
    
    if st.button("Download PDF Report"):
        st.info("In a complete implementation, this would generate and download a PDF report")

# Footer
st.markdown("---")
st.markdown("Campaign Manager v1.0 | Client Sharing Module")