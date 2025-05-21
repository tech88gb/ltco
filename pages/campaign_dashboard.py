import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from db import save_campaign

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Campaign Dashboard",
    page_icon="📈",
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
st.title(f"Dashboard: {current_campaign['name']}")

# Campaign budget section
st.header("Campaign Budget")
budget_col1, budget_col2 = st.columns(2)

with budget_col1:
    # Display current budget
    current_budget = current_campaign.get('budget', 0.0)
    st.metric("Total Budget", f"₹{current_budget:,.2f}")

with budget_col2:
    # Allow editing the budget
    new_budget = st.number_input(
        "Edit Budget (₹)",
        min_value=0.0,
        value=float(current_budget),
        step=1000.0,
        format="%.2f"
    )
    
    if st.button("Update Budget"):
        current_campaign['budget'] = float(new_budget)
        save_campaign_data()
        st.success("Budget updated successfully!")
        st.rerun()

# Campaign analytics section
st.header("Campaign Analytics")

# Display key metrics in a prominent way
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
with col2:
    st.metric("Budget", f"₹{current_campaign.get('budget', 0):,.2f}")

# Calculate cost per view if views > 0 and budget > 0
if current_campaign['metrics']['total_views'] > 0 and current_campaign.get('budget', 0) > 0:
    cost_per_view = current_campaign.get('budget', 0) / current_campaign['metrics']['total_views']
    with col3:
        st.metric("Budget per View", f"₹{cost_per_view:.4f}")

# Display engagement metrics
col4, col5, col6 = st.columns(3)
with col4:
    total_likes = current_campaign['metrics'].get('total_likes', 0)
    st.metric("Total Likes", f"{total_likes:,}")
with col5:
    total_shares = current_campaign['metrics'].get('total_shares', 0)
    st.metric("Total Shares", f"{total_shares:,}")
with col6:
    total_comments = current_campaign['metrics'].get('total_comments', 0)
    st.metric("Total Comments", f"{total_comments:,}")

# Create dataframe from influencers data for visualization
if not current_campaign["influencers"]:
    st.info("Add influencers to view analytics and charts")
else:
    # Convert influencers list to DataFrame
    influencers_df = pd.DataFrame(current_campaign["influencers"])
    
    # Charts Row 1
    st.subheader("Performance Analysis")
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
        # Views by platform bar chart
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
    
    # Charts Row 2
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
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
    
    # Removed Campaign Budget Overview pie chart from chart_col4
    # with chart_col4:
    #     # Budget allocation
    #     # Create a pie chart showing how the budget is distributed
    #     # This is conceptual since we don't allocate budget per influencer anymore
    #     total_influencers = len(influencers_df)
    #     if total_influencers > 0 and current_campaign.get('budget', 0) > 0:
    #         # Just for visualization, we'll distribute budget equally
    #         fig_budget = px.pie(
    #             names=['Allocated Budget'],
    #             values=[current_campaign.get('budget', 0)],
    #             title='Campaign Budget Overview',
    #             color_discrete_sequence=px.colors.qualitative.Pastel
    #         )
    #         fig_budget.update_traces(textinfo='value+percent')
    #         st.plotly_chart(fig_budget, use_container_width=True)
    #     else:
    #         st.info("Set a budget for your campaign to see budget visualization")
    
    # Charts Row 3 - Engagement Metrics
    st.subheader("Engagement Analysis")
    engagement_col1, engagement_col2 = st.columns(2)
    
    with engagement_col1:
        # Engagement breakdown by platform
        engagement_data = influencers_df.groupby('platform').agg({
            'likes': 'sum',
            'shares': 'sum',
            'comments': 'sum'
        }).reset_index()
        
        # Reshape for plotting
        engagement_melted = pd.melt(
            engagement_data,
            id_vars=['platform'],
            value_vars=['likes', 'shares', 'comments'],
            var_name='Engagement Type',
            value_name='Count'
        )
        
        fig_engagement_breakdown = px.bar(
            engagement_melted,
            x='platform',
            y='Count',
            color='Engagement Type',
            title='Engagement Breakdown by Platform',
            labels={'platform': 'Platform', 'Count': 'Number of Engagements'},
            barmode='group',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_engagement_breakdown, use_container_width=True)
    
    with engagement_col2:
        # Budget efficiency - Views per theoretical budget allocation
        total_views = influencers_df['views'].sum()
        campaign_budget = current_campaign.get('budget', 0)
        
        if total_views > 0 and campaign_budget > 0:
            # Calculate views per rupee
            views_per_rupee = total_views / campaign_budget
            
            # Create a gauge chart for budget efficiency
            fig = go.Figure(go.Indicator(
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
                }
            ))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Need views and budget to calculate efficiency")
    
    # Detailed influencer performance
    st.header("Influencer Performance")
    
    # Add filters
    st.subheader("Filter Data")
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        # Platform filter
        platforms = ['All'] + list(influencers_df['platform'].unique())
        selected_platform = st.selectbox("Platform", platforms)
    
    with filter_col2:
        # Post type filter
        post_types = ['All'] + list(influencers_df['post_type'].unique())
        selected_post_type = st.selectbox("Post Type", post_types)
    
    with filter_col3:
        # Sort options
        sort_options = ['Name', 'Views', 'Likes', 'Shares', 'Comments']
        sort_by = st.selectbox("Sort By", sort_options)
    
    # Apply filters
    filtered_df = influencers_df.copy()
    if selected_platform != 'All':
        filtered_df = filtered_df[filtered_df['platform'] == selected_platform]
    
    if selected_post_type != 'All':
        filtered_df = filtered_df[filtered_df['post_type'] == selected_post_type]
    
    # Apply sorting
    if sort_by == 'Name':
        filtered_df = filtered_df.sort_values('name')
    elif sort_by == 'Views':
        filtered_df = filtered_df.sort_values('views', ascending=False)
    elif sort_by == 'Likes':
        filtered_df = filtered_df.sort_values('likes', ascending=False)
    elif sort_by == 'Shares':
        filtered_df = filtered_df.sort_values('shares', ascending=False)
    elif sort_by == 'Comments':
        filtered_df = filtered_df.sort_values('comments', ascending=False)
    
    # Display filtered influencer data
    if not filtered_df.empty:
        st.subheader(f"Showing {len(filtered_df)} Influencers")
        
        # Create a clean display dataframe
        display_df = filtered_df[['name', 'username', 'platform', 'post_type', 'views', 'likes', 'shares', 'comments']]
        display_df.columns = ['Name', 'Username', 'Platform', 'Post Type', 'Views', 'Likes', 'Shares', 'Comments']
        
        # Format numeric columns
        display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
        display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}")
        display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}")
        display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}")
        
        # Calculate totals row
        totals = {
            'Name': 'TOTAL',
            'Username': '',
            'Platform': '',
            'Post Type': '',
            'Views': f"{filtered_df['views'].sum():,}",
            'Likes': f"{filtered_df['likes'].sum():,}",
            'Shares': f"{filtered_df['shares'].sum():,}",
            'Comments': f"{filtered_df['comments'].sum():,}"
        }
        
        # Add totals row to dataframe
        display_df = pd.concat([display_df, pd.DataFrame([totals])], ignore_index=True)
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No influencers match the selected filters")
    
    # Export options
    st.subheader("Export Data")
    
    # Create CSV data
    csv = filtered_df.to_csv(index=False)
    
    st.download_button(
        label="Export to CSV",
        data=csv,
        file_name=f"{current_campaign['name']}_influencers.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("Campaign Manager v1.0 | Campaign Dashboard")