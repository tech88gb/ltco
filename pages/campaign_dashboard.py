import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from db import save_campaign

# Set page configuration
st.set_page_config(
    page_title="Campaign Dashboard",
    page_icon="📈",
    layout="wide"
)

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

# Campaign analytics section
st.header("Campaign Analytics")

# Display key metrics in a prominent way
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
with col2:
    st.metric("Total Cost", f"₹{current_campaign['metrics']['total_cost']:,.2f}")

# Calculate cost per view if views > 0
if current_campaign['metrics']['total_views'] > 0:
    cost_per_view = current_campaign['metrics']['total_cost'] / current_campaign['metrics']['total_views']
    with col3:
        st.metric("Cost per View", f"₹{cost_per_view:.4f}")

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
        # Cost by platform bar chart
        platform_costs = influencers_df.groupby('platform')['cost'].sum().reset_index()
        
        fig_costs = px.bar(
            platform_costs,
            x='platform',
            y='cost',
            title='Cost by Platform',
            labels={'platform': 'Platform', 'cost': 'Cost (₹)'},
            color='platform',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_costs, use_container_width=True)
    
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
    
    with chart_col4:
        # Calculate efficiency (views per cost)
        influencers_df['efficiency'] = influencers_df['views'] / influencers_df['cost'].apply(lambda x: max(x, 1))  # Avoid division by zero
        
        # Sort by efficiency for the chart
        top_efficient = influencers_df.sort_values('efficiency', ascending=False).head(10)
        
        fig_efficiency = px.bar(
            top_efficient,
            x='name',
            y='efficiency',
            title='Top Influencers by Efficiency (Views per ₹)',
            labels={'name': 'Influencer', 'efficiency': 'Views per ₹'},
            color='platform',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_efficiency.update_layout(xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig_efficiency, use_container_width=True)
    
    # Charts Row 3 - Engagement Metrics
    st.subheader("Engagement Analysis")
    chart_col5, chart_col6 = st.columns(2)
    
    with chart_col5:
        # Likes by platform
        platform_likes = influencers_df.groupby('platform')['likes'].sum().reset_index()
        
        fig_likes = px.bar(
            platform_likes,
            x='platform',
            y='likes',
            title='Likes by Platform',
            labels={'platform': 'Platform', 'likes': 'Likes'},
            color='platform',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_likes, use_container_width=True)
    
    with chart_col6:
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
    
    # Charts Row 4 - Cost Analysis
    chart_col7, chart_col8 = st.columns(2)
    
    with chart_col7:
        # Cost per engagement by platform
        if 'cost' in influencers_df.columns and all(col in influencers_df.columns for col in ['likes', 'shares', 'comments']):
            influencers_df['total_engagements'] = influencers_df['likes'] + influencers_df['shares'] + influencers_df['comments']
            influencers_df['cost_per_engagement'] = influencers_df['cost'] / influencers_df['total_engagements'].apply(lambda x: max(x, 1))
            
            platform_cpe = influencers_df.groupby('platform')['cost_per_engagement'].mean().reset_index()
            
            fig_cpe = px.bar(
                platform_cpe,
                x='platform',
                y='cost_per_engagement',
                title='Cost per Engagement by Platform (₹)',
                labels={'platform': 'Platform', 'cost_per_engagement': 'Cost per Engagement (₹)'},
                color='platform',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_cpe, use_container_width=True)
    
    with chart_col8:
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
        sort_options = ['Name', 'Views', 'Cost', 'Likes', 'Shares', 'Comments', 'Efficiency']
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
    elif sort_by == 'Cost':
        filtered_df = filtered_df.sort_values('cost', ascending=False)
    elif sort_by == 'Likes':
        filtered_df = filtered_df.sort_values('likes', ascending=False)
    elif sort_by == 'Shares':
        filtered_df = filtered_df.sort_values('shares', ascending=False)
    elif sort_by == 'Comments':
        filtered_df = filtered_df.sort_values('comments', ascending=False)
    elif sort_by == 'Efficiency':
        filtered_df = filtered_df.sort_values('efficiency', ascending=False)
    
    # Display filtered influencer data
    if not filtered_df.empty:
        st.subheader(f"Showing {len(filtered_df)} Influencers")
        
        # Create a clean display dataframe
        display_df = filtered_df[['name', 'platform', 'post_type', 'views', 'cost', 'likes', 'shares', 'comments']]
        display_df.columns = ['Name', 'Platform', 'Post Type', 'Views', 'Cost (₹)', 'Likes', 'Shares', 'Comments']
        
        # Add efficiency column
        display_df['Views per ₹'] = filtered_df['efficiency'].round(2)
        
        # Format numeric columns
        display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
        display_df['Cost (₹)'] = display_df['Cost (₹)'].apply(lambda x: f"₹{x:,.2f}")
        display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}")
        display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}")
        display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}")
        
        # Calculate totals row
        totals = {
            'Name': 'TOTAL',
            'Platform': '',
            'Post Type': '',
            'Views': f"{filtered_df['views'].sum():,}",
            'Cost (₹)': f"₹{filtered_df['cost'].sum():,.2f}",
            'Likes': f"{filtered_df['likes'].sum():,}",
            'Shares': f"{filtered_df['shares'].sum():,}",
            'Comments': f"{filtered_df['comments'].sum():,}",
            'Views per ₹': f"{(filtered_df['views'].sum() / max(filtered_df['cost'].sum(), 1)):,.2f}"
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
st.markdown("Campaign Manager v1.0 | Analytics Dashboard")