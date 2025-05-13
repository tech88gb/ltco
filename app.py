import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from db import save_campaign, get_campaigns, delete_campaign, generate_numeric_id, delete_influencer

# Set page configuration
st.set_page_config(
    page_title="Campaign Manager",
    page_icon="assets/ltco 4.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'campaigns' not in st.session_state:
    # Load campaigns from database
    st.session_state.campaigns = get_campaigns()

if 'current_campaign_id' not in st.session_state:
    st.session_state.current_campaign_id = None

# Initialize form fields in session state if they don't exist
if 'form_name' not in st.session_state:
    st.session_state.form_name = ""
if 'form_platform' not in st.session_state:
    st.session_state.form_platform = "Instagram"
if 'form_post_type' not in st.session_state:
    st.session_state.form_post_type = "Post"
if 'form_cost' not in st.session_state:
    st.session_state.form_cost = 0.0
if 'form_views' not in st.session_state:
    st.session_state.form_views = 0
if 'form_likes' not in st.session_state:
    st.session_state.form_likes = 0
if 'form_shares' not in st.session_state:
    st.session_state.form_shares = 0
if 'form_comments' not in st.session_state:
    st.session_state.form_comments = 0

# Helper functions
def save_campaign_data():
    """Save campaign data to database"""
    if st.session_state.current_campaign_id:
        current_campaign = st.session_state.campaigns[st.session_state.current_campaign_id]
        save_campaign(current_campaign)

def reset_form_fields():
    """Reset all form fields to defaults"""
    st.session_state.form_name = ""
    st.session_state.form_platform = "Instagram"
    st.session_state.form_post_type = "Post"
    st.session_state.form_cost = 0.0
    st.session_state.form_views = 0
    st.session_state.form_likes = 0
    st.session_state.form_shares = 0
    st.session_state.form_comments = 0

# Main app header
st.title("Campaign Manager")

# Sidebar for navigation
with st.sidebar:
    st.header("Navigation")
    
    # Campaign selection/creation section
    st.subheader("Campaigns")
    
    # Create new campaign button
    col1, col2 = st.columns([1, 4])
    with col1:
        pass  # Removed image
    with col2:
        if st.button("Create New Campaign"):
            # Generate a numeric ID instead of UUID
            new_id = generate_numeric_id()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create new campaign with numeric ID
            st.session_state.campaigns[str(new_id)] = {  # Convert to string for dictionary key
                "id": new_id,  # Actual ID is numeric
                "name": f"Campaign {len(st.session_state.campaigns) + 1}",
                "created_at": current_time,
                "influencers": [],
                "metrics": {
                    "total_reach": 0,
                    "total_cost": 0,
                    "total_views": 0,
                    "total_likes": 0,
                    "total_shares": 0,
                    "total_comments": 0
                },
                "share_token": f"share_{new_id}"  # Use numeric ID in share token
            }
            st.session_state.current_campaign_id = str(new_id)  # String for dictionary key
            save_campaign_data()  # Save to database
            st.rerun()
    
    # Display existing campaigns with delete option
    st.write("Select a campaign:")
    
    for campaign_id, campaign_data in st.session_state.campaigns.items():
        col1, col2 = st.columns([3, 2])
        
        with col1:
            if st.button(f"{campaign_data['name']}", key=f"select_{campaign_id}"):
                st.session_state.current_campaign_id = campaign_id
                st.rerun()
        
        with col2:
            if st.button("Delete", key=f"delete_{campaign_id}", help="Delete this campaign"):
                st.session_state.confirm_delete = campaign_id
                st.rerun()
    
    # Delete confirmation
    if hasattr(st.session_state, 'confirm_delete'):
        campaign_to_delete = st.session_state.confirm_delete
        campaign_name = st.session_state.campaigns[campaign_to_delete]['name']
        
        st.warning(f"Are you sure you want to delete '{campaign_name}'? This cannot be undone.")
            
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete"):
                try:
                    # Delete from database
                    delete_campaign(st.session_state.campaigns[campaign_to_delete]['id'])
                    
                    # Delete from session state
                    del st.session_state.campaigns[campaign_to_delete]
                    
                    # Reset current campaign if it was the deleted one
                    if st.session_state.current_campaign_id == campaign_to_delete:
                        st.session_state.current_campaign_id = None
                    
                    # Remove confirmation state
                    del st.session_state.confirm_delete
                    
                    st.success(f"Campaign '{campaign_name}' deleted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting campaign: {str(e)}")
        
        with col2:
            if st.button("Cancel"):
                # Remove confirmation state
                del st.session_state.confirm_delete
                st.rerun()

# Main content area
if not st.session_state.campaigns:
    st.info("Welcome to Campaign Manager! Get started by creating a new campaign in the sidebar.")
else:
    if st.session_state.current_campaign_id is None:
        st.info("Select a campaign from the sidebar or create a new one.")
    else:
        current_campaign = st.session_state.campaigns[st.session_state.current_campaign_id]
        
        # Campaign header
        col1, col2 = st.columns([3, 1])
        with col1:
            # Make campaign name editable
            new_name = st.text_input("Campaign Name", current_campaign["name"])
            if new_name != current_campaign["name"]:
                current_campaign["name"] = new_name
                save_campaign_data()
        
        with col2:
            st.write(f"Created: {current_campaign['created_at']}")
            st.write(f"Share Code: {current_campaign['share_token']}")
        
        # Campaign tabs
        tab1, tab2, tab3 = st.tabs(["Dashboard", "Influencers", "Client Sharing"])
        
        with tab1:
            st.header("Campaign Dashboard")
            
            # Display campaign metrics
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            with metrics_col1:
                st.metric("Total Cost", f"₹{current_campaign['metrics']['total_cost']:,.2f}")
            with metrics_col2:
                st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
            with metrics_col3:
                st.metric("Total Likes", f"{current_campaign['metrics']['total_likes']:,}")
            
            # Display engagement metrics
            metrics_col4, metrics_col5, metrics_col6 = st.columns(3)
            with metrics_col4:
                total_shares = current_campaign['metrics'].get('total_shares', 0)
                st.metric("Total Shares", f"{total_shares:,}")
            with metrics_col5:
                total_comments = current_campaign['metrics'].get('total_comments', 0)
                st.metric("Total Comments", f"{total_comments:,}")
            
            # Placeholder for charts
            st.subheader("Performance Overview")
            if not current_campaign["influencers"]:
                st.info("Add influencers to see performance charts")
            else:
                # Create dataframe from influencers
                influencers_df = pd.DataFrame(current_campaign["influencers"])
                
                # Platform distribution charts
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
        
        with tab2:
            st.header("Influencers Management")
            
            # Add new influencer form - using session state for field values
            st.subheader("Add New Influencer")
            with st.form("new_influencer_form"):
                cols = st.columns(2)
                with cols[0]:
                    name = st.text_input("Influencer Name", value=st.session_state.form_name, key="name_input")
                    platform = st.selectbox(
                        "Platform", 
                        ["Instagram", "TikTok", "YouTube", "Twitter/X", "Other"],
                        index=["Instagram", "TikTok", "YouTube", "Twitter/X", "Other"].index(st.session_state.form_platform),
                        key="platform_input"
                    )
                    post_type = st.selectbox(
                        "Post Type", 
                        ["Post", "Story", "Reel", "Video", "Tweet", "Other"],
                        index=["Post", "Story", "Reel", "Video", "Tweet", "Other"].index(st.session_state.form_post_type),
                        key="post_type_input"
                    )
                
                with cols[1]:
                    cost = st.number_input("Cost (₹)", min_value=0.0, step=100.0, value=st.session_state.form_cost, key="cost_input")
                    views = st.number_input("Views", min_value=0, step=1000, value=st.session_state.form_views, key="views_input")
                
                # Add engagement metrics
                st.subheader("Engagement Metrics")
                engagement_cols = st.columns(3)
                with engagement_cols[0]:
                    likes = st.number_input("Likes", min_value=0, step=100, value=st.session_state.form_likes, key="likes_input")
                with engagement_cols[1]:
                    shares = st.number_input("Shares", min_value=0, step=10, value=st.session_state.form_shares, key="shares_input")
                with engagement_cols[2]:
                    comments = st.number_input("Comments", min_value=0, step=10, value=st.session_state.form_comments, key="comments_input")
                
                # Submit button
                submitted = st.form_submit_button("Add Influencer")
                if submitted and name:
                    # Create new influencer with numeric ID
                    new_influencer_id = generate_numeric_id()
                    
                    # Create new influencer entry
                    new_influencer = {
                        "id": new_influencer_id,
                        "name": name,
                        "platform": platform,
                        "post_type": post_type,
                        "cost": float(cost),
                        "views": int(views),
                        "likes": int(likes),
                        "shares": int(shares),
                        "comments": int(comments)
                    }
                    
                    # Add to campaign
                    current_campaign["influencers"].append(new_influencer)
                    
                    # Update metrics
                    current_campaign["metrics"]["total_cost"] += float(cost)
                    current_campaign["metrics"]["total_views"] += int(views)
                    current_campaign["metrics"]["total_likes"] = current_campaign["metrics"].get("total_likes", 0) + int(likes)
                    current_campaign["metrics"]["total_shares"] = current_campaign["metrics"].get("total_shares", 0) + int(shares)
                    current_campaign["metrics"]["total_comments"] = current_campaign["metrics"].get("total_comments", 0) + int(comments)
                    
                    # Save to database
                    save_campaign_data()
                    
                    # Reset form fields
                    reset_form_fields()
                    
                    st.success(f"Added {name} to the campaign!")
                    st.rerun()  # Rerun to clear the form
            
            # Display existing influencers
            st.subheader("Current Influencers")
            if not current_campaign["influencers"]:
                st.info("No influencers added yet")
            else:
                # Create a dataframe for better display of all influencers with totals
                influencer_df = pd.DataFrame(current_campaign["influencers"])
                
                # Calculate totals
                totals = {
                    'name': 'TOTAL',
                    'platform': '',
                    'post_type': '',
                    'views': influencer_df['views'].sum(),
                    'cost': influencer_df['cost'].sum(),
                    'likes': influencer_df['likes'].sum() if 'likes' in influencer_df.columns else 0,
                    'shares': influencer_df['shares'].sum() if 'shares' in influencer_df.columns else 0,
                    'comments': influencer_df['comments'].sum() if 'comments' in influencer_df.columns else 0
                }
                
                # Display influencers in a table with totals
                display_df = influencer_df.copy()
                
                # Add totals row
                display_df = pd.concat([display_df, pd.DataFrame([totals])], ignore_index=True)
                
                # Format the table
                display_df = display_df[['name', 'platform', 'post_type', 'views', 'cost', 'likes', 'shares', 'comments']]
                
                st.dataframe(display_df, use_container_width=True)
                
                # Individual influencer details with edit options
                st.subheader("Influencer Details")
                for i, influencer in enumerate(current_campaign["influencers"]):
                    with st.expander(f"{influencer['name']} - {influencer['platform']}"):
                        cols = st.columns(2)
                        
                        # Display influencer details
                        with cols[0]:
                            st.write(f"**Post Type:** {influencer['post_type']}")
                            st.write(f"**Views:** {influencer['views']:,}")
                        
                        with cols[1]:
                            st.write(f"**Cost:** ₹{influencer['cost']:,.2f}")
                            
                            # Engagement metrics
                            st.write(f"**Likes:** {influencer.get('likes', 0):,}")
                            st.write(f"**Shares:** {influencer.get('shares', 0):,}")
                            st.write(f"**Comments:** {influencer.get('comments', 0):,}")
                            
                            # Delete button
                            if st.button("Delete", key=f"delete_{influencer['id']}"):
                                try:
                                    # First delete from database
                                    delete_influencer(influencer['id'])
                                    
                                    # Update metrics before removing
                                    current_campaign["metrics"]["total_cost"] -= float(influencer['cost'])
                                    current_campaign["metrics"]["total_views"] -= int(influencer['views'])
                                    current_campaign["metrics"]["total_likes"] = current_campaign["metrics"].get("total_likes", 0) - int(influencer.get('likes', 0))
                                    current_campaign["metrics"]["total_shares"] = current_campaign["metrics"].get("total_shares", 0) - int(influencer.get('shares', 0))
                                    current_campaign["metrics"]["total_comments"] = current_campaign["metrics"].get("total_comments", 0) - int(influencer.get('comments', 0))
                                    
                                    # Remove from list
                                    current_campaign["influencers"].pop(i)
                                    
                                    # Save updated campaign
                                    save_campaign_data()
                                    
                                    st.success(f"Removed {influencer['name']} from the campaign")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting influencer: {str(e)}")
        
        with tab3:
            st.header("Client Sharing")
            
            # Generate shareable link
            st.subheader("Share with Clients")
            st.write("Your clients can view a read-only version of this campaign using the following:")
            
            # Updated share link to use the new client_view page
            share_link = f"/client_view?token={current_campaign['share_token']}"
            st.code(share_link)
            
            st.write("Client view will include:")
            st.checkbox("Campaign Overview", value=True, disabled=True)
            st.checkbox("Performance Metrics", value=True, disabled=True)
            include_costs = st.checkbox("Cost Information", value=False)
            include_influencer_details = st.checkbox("Detailed Influencer Information", value=True)
            
            if st.button("Update Sharing Settings"):
                # Initialize sharing_settings if it doesn't exist
                if 'sharing_settings' not in current_campaign or current_campaign['sharing_settings'] is None:
                    current_campaign['sharing_settings'] = {}
                
                current_campaign["sharing_settings"] = {
                    "include_costs": include_costs,
                    "include_influencer_details": include_influencer_details
                }
                st.success("Sharing settings updated!")
                save_campaign_data()
                
            # Preview client view 
            st.subheader("Client View Preview")
            
            with st.expander("Show Preview"):
                st.write("This is how clients will see your campaign data")
                
                # Show metrics
                preview_cols = st.columns(3)
                with preview_cols[0]:
                    st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
                with preview_cols[1]:
                    st.metric("Total Views", f"{current_campaign['metrics']['total_views']:,}")
                
                if include_costs:
                    with preview_cols[2]:
                        st.metric("Total Investment", f"₹{current_campaign['metrics']['total_cost']:,.2f}")
                
                # Show influencer list if enabled
                if include_influencer_details and current_campaign["influencers"]:
                    st.subheader("Campaign Influencers")
                    
                    # Create a dataframe for display
                    influencer_data = []
                    for inf in current_campaign["influencers"]:
                        data_row = {
                            "Influencer": inf["name"],
                            "Platform": inf["platform"],
                            "Post Type": inf["post_type"],
                            "Views": f"{inf['views']:,}",
                            "Likes": f"{inf.get('likes', 0):,}",
                            "Shares": f"{inf.get('shares', 0):,}",
                            "Comments": f"{inf.get('comments', 0):,}"
                        }
                        if include_costs:
                            data_row["Cost"] = f"₹{inf['cost']:,.2f}"
                        
                        influencer_data.append(data_row)
                    
                    # Calculate and add totals row
                    totals_row = {
                        "Influencer": "TOTAL",
                        "Platform": "",
                        "Post Type": "",
                        "Views": f"{sum(inf['views'] for inf in current_campaign['influencers']):,}",
                        "Likes": f"{sum(inf.get('likes', 0) for inf in current_campaign['influencers']):,}",
                        "Shares": f"{sum(inf.get('shares', 0) for inf in current_campaign['influencers']):,}",
                        "Comments": f"{sum(inf.get('comments', 0) for inf in current_campaign['influencers']):,}"
                    }
                    
                    if include_costs:
                        totals_row["Cost"] = f"₹{sum(inf['cost'] for inf in current_campaign['influencers']):,.2f}"
                    
                    influencer_data.append(totals_row)
                    
                    # Display as table
                    st.table(pd.DataFrame(influencer_data))

# Footer
st.markdown("---")
st.markdown("Campaign Manager v1.0 | Built with Streamlit")