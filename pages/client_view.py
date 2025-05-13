import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from db import get_campaign_by_share_token

# Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Client Campaign View",
    page_icon="🔗",
    layout="wide"
)

# Get the share token from the query params using the non-experimental API
token = st.query_params.get("token", None)

st.title("Client Campaign View")

if not token:
    st.error("No share token provided in the URL.")
    st.stop()

# Get campaign data by token directly from database
campaign = get_campaign_by_share_token(token)

if not campaign:
    st.error("Invalid or expired share token. Please check your link.")
    st.stop()

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
st.subheader("Campaign Report")
st.write(f"**Campaign:** {campaign['name']}")

if sharing_settings.get('client_name'):
    st.write(f"**Prepared for:** {sharing_settings['client_name']}")

st.write(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")

if sharing_settings.get('custom_message'):
    st.info(sharing_settings['custom_message'])

# Show metrics if enabled
if sharing_settings.get('include_metrics', True):
    st.subheader("Campaign Performance")
    
    # First row of metrics
    metric_cols1 = st.columns(2 if sharing_settings.get('include_costs', False) else 1)
    
    with metric_cols1[0]:
        st.metric("Total Views", f"{campaign['metrics']['total_views']:,}")
    
    if sharing_settings.get('include_costs', False):
        with metric_cols1[1]:
            st.metric("Total Investment", f"₹{campaign['metrics']['total_cost']:,.2f}")
    
    # Show engagement metrics if enabled
    if sharing_settings.get('include_engagement_metrics', True):
        # Second row of metrics for engagement
        metric_cols2 = st.columns(3)
        with metric_cols2[0]:
            st.metric("Total Likes", f"{campaign['metrics'].get('total_likes', 0):,}")
        with metric_cols2[1]:
            st.metric("Total Shares", f"{campaign['metrics'].get('total_shares', 0):,}")
        with metric_cols2[2]:
            st.metric("Total Comments", f"{campaign['metrics'].get('total_comments', 0):,}")

# Show dashboard/charts if enabled and influencers exist
if sharing_settings.get('include_dashboard', True) and campaign['influencers']:
    st.subheader("Performance Charts")
    
    # Create dataframe from influencers
    influencers_df = pd.DataFrame(campaign['influencers'])
    
    chart_cols = st.columns(2)
    with chart_cols[0]:
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
    
    with chart_cols[1]:
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
    
    # Show cost information if enabled
    if sharing_settings.get('include_costs', False):
        cost_cols = st.columns(2)
        
        with cost_cols[0]:
            # Cost by platform
            platform_costs = influencers_df.groupby('platform')['cost'].sum().reset_index()
            platform_costs.columns = ['Platform', 'Cost']
            
            fig_costs = px.bar(
                platform_costs,
                x='Platform',
                y='Cost',
                title='Investment by Platform',
                color='Platform',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_costs, use_container_width=True)
        
        with cost_cols[1]:
            # Calculate efficiency (views per cost)
            influencers_df['efficiency'] = influencers_df['views'] / influencers_df['cost'].apply(lambda x: max(x, 1))
            
            # Efficiency by platform
            platform_efficiency = influencers_df.groupby('platform')['efficiency'].mean().reset_index()
            platform_efficiency.columns = ['Platform', 'Views per ₹']
            
            fig_eff = px.bar(
                platform_efficiency,
                x='Platform',
                y='Views per ₹',
                title='Performance by Platform (Views per ₹)',
                color='Platform',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_eff, use_container_width=True)
        
        # If both cost and engagement metrics are enabled, show cost per engagement
        if sharing_settings.get('include_engagement_metrics', True):
            st.subheader("Cost Efficiency Analysis")
            
            # Calculate cost per engagement
            influencers_df['total_engagements'] = influencers_df['likes'] + influencers_df['shares'] + influencers_df['comments']
            
            platform_cost_per_engagement = influencers_df.groupby('platform').apply(
                lambda x: x['cost'].sum() / max(x['total_engagements'].sum(), 1)
            ).reset_index()
            platform_cost_per_engagement.columns = ['Platform', 'Cost per Engagement']
            
            fig_cpe = px.bar(
                platform_cost_per_engagement,
                x='Platform',
                y='Cost per Engagement',
                title='Cost per Engagement by Platform (₹)',
                color='Platform',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_cpe, use_container_width=True)

# Show influencer details if enabled
if sharing_settings.get('include_influencer_details', True) and campaign['influencers']:
    st.subheader("Campaign Influencers")
    
    # Create display dataframe
    influencers_df = pd.DataFrame(campaign['influencers'])
    
    # Select columns to display
    display_columns = ['name', 'platform', 'post_type', 'views']
    
    # Add engagement metrics if enabled
    if sharing_settings.get('include_engagement_metrics', True):
        display_columns.extend(['likes', 'shares', 'comments'])
    
    if sharing_settings.get('include_costs', False):
        display_columns.append('cost')
    
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
        'cost': 'Investment (₹)',
        'post_url': 'Post URL',
        'likes': 'Likes',
        'shares': 'Shares',
        'comments': 'Comments'
    }
    
    display_df.columns = [column_map.get(col, col) for col in display_df.columns]
    
    # Format numeric columns
    if 'Views' in display_df.columns:
        display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
    
    if 'Investment (₹)' in display_df.columns:
        display_df['Investment (₹)'] = display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}")
    
    if 'Likes' in display_df.columns:
        display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}")
    
    if 'Shares' in display_df.columns:
        display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}")
    
    if 'Comments' in display_df.columns:
        display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}")
    
    # Calculate totals row
    totals = {
        'Name': 'TOTAL',
        'Platform': '',
        'Post Type': '',
        'Views': f"{influencers_df['views'].sum():,}"
    }
    
    if 'Investment (₹)' in display_df.columns:
        totals['Investment (₹)'] = f"₹{influencers_df['cost'].sum():,.2f}"
    
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

    # Add filtering capabilities for clients
    if len(influencers_df) > 5:  # Only show filters if there are enough influencers
        st.subheader("Filter Influencers")
        
        filter_cols = st.columns(3)
        
        with filter_cols[0]:
            filter_platform = st.selectbox(
                "Filter by Platform",
                ["All"] + list(influencers_df['platform'].unique())
            )
        
        with filter_cols[1]:
            filter_post_type = st.selectbox(
                "Filter by Post Type",
                ["All"] + list(influencers_df['post_type'].unique())
            )
        
        with filter_cols[2]:
            sort_options = ["Name", "Views"]
            if sharing_settings.get('include_engagement_metrics', True):
                sort_options.extend(["Likes", "Shares", "Comments"])
            if sharing_settings.get('include_costs', False):
                sort_options.append("Investment")
            
            sort_by = st.selectbox("Sort By", sort_options)
        
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
        elif sort_by == "Investment":
            filtered_df = filtered_df.sort_values('cost', ascending=False)
        
        # Display filtered results
        if not filtered_df.empty:
            # Create display dataframe with only selected columns
            filtered_display_df = filtered_df[display_columns].copy()
            
            # Rename columns
            filtered_display_df.columns = [column_map.get(col, col) for col in filtered_display_df.columns]
            
            # Format numeric columns
            if 'Views' in filtered_display_df.columns:
                filtered_display_df['Views'] = filtered_display_df['Views'].apply(lambda x: f"{x:,}")
            
            if 'Investment (₹)' in filtered_display_df.columns:
                filtered_display_df['Investment (₹)'] = filtered_display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}")
            
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
            
            if 'Investment (₹)' in filtered_display_df.columns:
                filtered_totals['Investment (₹)'] = f"₹{filtered_df['cost'].sum():,.2f}"
            
            if 'Likes' in filtered_display_df.columns:
                filtered_totals['Likes'] = f"{filtered_df['likes'].sum():,}"
            
            if 'Shares' in filtered_display_df.columns:
                filtered_totals['Shares'] = f"{filtered_df['shares'].sum():,}"
            
            if 'Comments' in filtered_display_df.columns:
                filtered_totals['Comments'] = f"{filtered_df['comments'].sum():,}"
            
            # Add totals row
            filtered_display_df = pd.concat([filtered_display_df, pd.DataFrame([filtered_totals])], ignore_index=True)
            
            st.subheader(f"Filtered Results ({len(filtered_df)} influencers)")
            st.dataframe(filtered_display_df, use_container_width=True)
        else:
            st.info("No influencers match your filter criteria")

elif not campaign['influencers']:
    st.info("No influencers added to this campaign yet.")

# Add optional PDF download button
st.download_button(
    label="Download PDF Report",
    data="This would be a PDF report in a real implementation",
    file_name=f"{campaign['name']}_report.pdf",
    mime="application/pdf",
    disabled=True
)

# Add contact information section
st.subheader("Contact Information")
st.write("If you have any questions about this report, please contact your campaign manager.")

st.markdown("---")
st.markdown("Client View | Powered by Campaign Manager")