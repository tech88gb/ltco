import streamlit as st
import pandas as pd
import uuid
import time
from datetime import datetime
from db import save_campaign, delete_influencer, generate_numeric_id

# Set page configuration
st.set_page_config(
    page_title="Influencer Management",
    page_icon="👤",
    layout="wide"
)

# Hide Streamlit's default GitHub link and menu
hide_streamlit_elements = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
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

# Initialize form fields in session state if they don't exist
if 'im_form_name' not in st.session_state:
    st.session_state.im_form_name = ""
if 'im_form_platform' not in st.session_state:
    st.session_state.im_form_platform = "Instagram"
if 'im_form_post_type' not in st.session_state:
    st.session_state.im_form_post_type = "Post"
if 'im_form_post_url' not in st.session_state:
    st.session_state.im_form_post_url = ""
if 'im_form_cost' not in st.session_state:
    st.session_state.im_form_cost = 0.0
if 'im_form_views' not in st.session_state:
    st.session_state.im_form_views = 0
if 'im_form_likes' not in st.session_state:
    st.session_state.im_form_likes = 0
if 'im_form_shares' not in st.session_state:
    st.session_state.im_form_shares = 0
if 'im_form_comments' not in st.session_state:
    st.session_state.im_form_comments = 0

# Get current campaign data
current_campaign = st.session_state.campaigns[st.session_state.current_campaign_id]

# Helper function to save campaign data
def save_campaign_data():
    """Save campaign data to database"""
    save_campaign(current_campaign)

# Function to reset form fields
def reset_form_fields():
    """Reset all form fields to defaults"""
    st.session_state.im_form_name = ""
    st.session_state.im_form_platform = "Instagram"
    st.session_state.im_form_post_type = "Post"
    st.session_state.im_form_post_url = ""
    st.session_state.im_form_cost = 0.0
    st.session_state.im_form_views = 0
    st.session_state.im_form_likes = 0
    st.session_state.im_form_shares = 0
    st.session_state.im_form_comments = 0

# Page header
st.title(f"Influencer Management: {current_campaign['name']}")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Add Influencers", "Manage Existing", "Bulk Operations"])

with tab1:
    st.header("Add New Influencer")
    
    # Create a form for adding new influencers
    with st.form("add_influencer_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Influencer Name", value=st.session_state.im_form_name, key="im_name_input")
            platform = st.selectbox(
                "Platform", 
                ["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"],
                index=["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"].index(st.session_state.im_form_platform) 
                if st.session_state.im_form_platform in ["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"] else 0,
                key="im_platform_input"
            )
            post_type = st.selectbox(
                "Post Type", 
                ["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"],
                index=["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"].index(st.session_state.im_form_post_type)
                if st.session_state.im_form_post_type in ["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"] else 0,
                key="im_post_type_input"
            )
            post_url = st.text_input("Post URL (optional)", value=st.session_state.im_form_post_url, key="im_post_url_input")
        
        with col2:
            views = st.number_input("Views/Impressions", min_value=0, step=1000, value=st.session_state.im_form_views, key="im_views_input")
            cost = st.number_input("Cost ($)", min_value=0.0, step=100.0, value=st.session_state.im_form_cost, key="im_cost_input")
        
        # Add engagement metrics
        st.subheader("Engagement Metrics")
        engagement_cols = st.columns(3)
        with engagement_cols[0]:
            likes = st.number_input("Likes", min_value=0, step=100, value=st.session_state.im_form_likes, key="im_likes_input")
        with engagement_cols[1]:
            shares = st.number_input("Shares", min_value=0, step=10, value=st.session_state.im_form_shares, key="im_shares_input")
        with engagement_cols[2]:
            comments = st.number_input("Comments", min_value=0, step=10, value=st.session_state.im_form_comments, key="im_comments_input")
        
        # Submit button
        submitted = st.form_submit_button("Add Influencer")
        
        if submitted:
            if not name:
                st.error("Influencer name is required")
            else:
                # Create new influencer entry
                new_influencer_id = generate_numeric_id()
                
                new_influencer = {
                    "id": new_influencer_id,
                    "name": name,
                    "platform": platform,
                    "post_type": post_type,
                    "post_url": post_url,
                    "views": int(views),
                    "cost": float(cost),
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
                st.rerun()  # Rerun to reset the form

with tab2:
    st.header("Manage Existing Influencers")
    
    if not current_campaign["influencers"]:
        st.info("No influencers added to this campaign yet")
    else:
        # Add search and filter options
        st.subheader("Search & Filter")
        
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search by name")
        
        with col2:
            platforms = ["All"] + list(set([inf["platform"] for inf in current_campaign["influencers"]]))
            filter_platform = st.selectbox("Filter by platform", platforms)
        
        # Apply filters
        filtered_influencers = current_campaign["influencers"]
        
        if search_term:
            filtered_influencers = [inf for inf in filtered_influencers if search_term.lower() in inf["name"].lower()]
        
        if filter_platform != "All":
            filtered_influencers = [inf for inf in filtered_influencers if inf["platform"] == filter_platform]
        
        # Display filtered results
        st.subheader(f"Showing {len(filtered_influencers)} Influencers")
        
        # Convert filtered influencers to dataframe
        df = pd.DataFrame(filtered_influencers)
        
        # Calculate totals row
        if not df.empty:
            totals = {
                'name': 'TOTAL',
                'platform': '',
                'post_type': '',
                'views': df['views'].sum(),
                'cost': df['cost'].sum(),
                'likes': df['likes'].sum() if 'likes' in df.columns else 0,
                'shares': df['shares'].sum() if 'shares' in df.columns else 0,
                'comments': df['comments'].sum() if 'comments' in df.columns else 0
            }
            
            # Add totals row
            df_with_totals = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
            
            # Display the dataframe with totals
            if 'id' in df_with_totals.columns:
                df_with_totals = df_with_totals.drop(columns=['id'])
            if 'post_url' in df_with_totals.columns:
                df_with_totals = df_with_totals.drop(columns=['post_url'])
            if 'campaign_id' in df_with_totals.columns:
                df_with_totals = df_with_totals.drop(columns=['campaign_id'])
                
            st.dataframe(df_with_totals, use_container_width=True)
        
        # Display influencers with edit options
        st.subheader("Edit Influencers")
        
        # Store indexes to delete after loop to avoid modifying list during iteration
        to_delete = []
        
        for i, influencer in enumerate(filtered_influencers):
            with st.expander(f"{influencer['name']} - {influencer['platform']}"):
                # Display and edit influencer details
                col1, col2 = st.columns(2)
                
                with col1:
                    # Basic info
                    new_name = st.text_input("Name", influencer["name"], key=f"name_{influencer['id']}")
                    new_platform = st.selectbox(
                        "Platform", 
                        ["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"],
                        index=["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"].index(influencer["platform"]) if influencer["platform"] in ["Instagram", "TikTok", "YouTube", "Twitter/X", "Facebook", "LinkedIn", "Twitch", "Other"] else 0,
                        key=f"platform_{influencer['id']}"
                    )
                    new_post_type = st.selectbox(
                        "Post Type", 
                        ["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"],
                        index=["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"].index(influencer["post_type"]) if influencer["post_type"] in ["Post", "Story", "Reel", "Video", "Tweet", "Live Stream", "Collaboration", "Other"] else 0,
                        key=f"post_type_{influencer['id']}"
                    )
                    new_post_url = st.text_input("Post URL", influencer.get("post_url", ""), key=f"post_url_{influencer['id']}")
                
                with col2:
                    # Metrics - Note the explicit type casts and matching with step type
                    old_views = int(influencer["views"])
                    new_views = st.number_input("Views", min_value=0, value=old_views, step=1000, key=f"views_{influencer['id']}")
                    
                    # Ensure old_cost is a float
                    old_cost = float(influencer["cost"])
                    new_cost = st.number_input("Cost ($)", min_value=0.0, value=old_cost, step=100.0, key=f"cost_{influencer['id']}")
                
                # Engagement metrics
                engagement_cols = st.columns(3)
                with engagement_cols[0]:
                    old_likes = int(influencer.get("likes", 0))
                    new_likes = st.number_input("Likes", min_value=0, value=old_likes, step=100, key=f"likes_{influencer['id']}")
                
                with engagement_cols[1]:
                    old_shares = int(influencer.get("shares", 0))
                    new_shares = st.number_input("Shares", min_value=0, value=old_shares, step=10, key=f"shares_{influencer['id']}")
                
                with engagement_cols[2]:
                    old_comments = int(influencer.get("comments", 0))
                    new_comments = st.number_input("Comments", min_value=0, value=old_comments, step=10, key=f"comments_{influencer['id']}")
                
                # Save changes button
                if st.button("Save Changes", key=f"save_{influencer['id']}"):
                    # Update campaign metrics by calculating the differences
                    views_diff = int(new_views) - int(old_views)
                    cost_diff = float(new_cost) - float(old_cost)
                    likes_diff = int(new_likes) - int(old_likes)
                    shares_diff = int(new_shares) - int(old_shares)
                    comments_diff = int(new_comments) - int(old_comments)
                    
                    current_campaign["metrics"]["total_views"] += views_diff
                    current_campaign["metrics"]["total_cost"] += cost_diff
                    current_campaign["metrics"]["total_likes"] = current_campaign["metrics"].get("total_likes", 0) + likes_diff
                    current_campaign["metrics"]["total_shares"] = current_campaign["metrics"].get("total_shares", 0) + shares_diff
                    current_campaign["metrics"]["total_comments"] = current_campaign["metrics"].get("total_comments", 0) + comments_diff
                    
                    # Update influencer data - ensure each value has the correct type
                    influencer["name"] = new_name
                    influencer["platform"] = new_platform
                    influencer["post_type"] = new_post_type
                    influencer["post_url"] = new_post_url
                    influencer["views"] = int(new_views)
                    influencer["cost"] = float(new_cost)
                    influencer["likes"] = int(new_likes)
                    influencer["shares"] = int(new_shares)
                    influencer["comments"] = int(new_comments)
                    
                    save_campaign_data()
                    st.success(f"Updated {influencer['name']}'s information!")
                
                # Delete button
                delete_pressed = st.button("Delete Influencer", key=f"delete_{influencer['id']}")
                if delete_pressed:
                    # Find the original index of this influencer in the campaign's influencers list
                    original_idx = next((i for i, inf in enumerate(current_campaign["influencers"]) 
                                        if inf["id"] == influencer["id"]), None)
                    
                    if original_idx is not None:
                        try:
                            # Actually delete from database first
                            delete_influencer(influencer["id"])
                            
                            # Update metrics before removing
                            current_campaign["metrics"]["total_views"] -= int(influencer["views"])
                            current_campaign["metrics"]["total_cost"] -= float(influencer["cost"])
                            current_campaign["metrics"]["total_likes"] = current_campaign["metrics"].get("total_likes", 0) - int(influencer.get("likes", 0))
                            current_campaign["metrics"]["total_shares"] = current_campaign["metrics"].get("total_shares", 0) - int(influencer.get("shares", 0))
                            current_campaign["metrics"]["total_comments"] = current_campaign["metrics"].get("total_comments", 0) - int(influencer.get("comments", 0))
                            
                            # Mark for deletion after the loop
                            to_delete.append(original_idx)
                            
                            st.success(f"Removed {influencer['name']} from the campaign")
                        except Exception as e:
                            st.error(f"Error deleting influencer: {str(e)}")
        
        # Actually remove the influencers from the list after the loop
        if to_delete:
            # Sort in reverse order to avoid index shifting problems
            for idx in sorted(to_delete, reverse=True):
                current_campaign["influencers"].pop(idx)
            
            # Save the updated campaign
            save_campaign_data()
            st.rerun()

with tab3:
    st.header("Bulk Operations")
    
    # Upload CSV file option
    st.subheader("Import Influencers from CSV")
    
    # Sample CSV template
    st.write("Download a CSV template to see the required format:")
    
    # Generate sample CSV data with new engagement metrics
    sample_data = """name,platform,post_type,views,cost,likes,shares,comments,post_url
Influencer1,Instagram,Post,15000,500.0,1200,45,78,https://instagram.com/post1
Influencer2,TikTok,Video,50000,750.0,3500,120,95,https://tiktok.com/video2
Influencer3,YouTube,Collaboration,25000,1200.0,850,65,42,https://youtube.com/video3"""
    
    st.download_button(
        label="Download CSV Template",
        data=sample_data,
        file_name="influencer_template.csv",
        mime="text/csv"
    )
    
    # Upload CSV
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
    
    if uploaded_file is not None:
        # Read the CSV file
        try:
            df = pd.read_csv(uploaded_file)
            st.success(f"Successfully read CSV with {len(df)} records")
            
            st.subheader("Preview")
            st.dataframe(df.head())
            
            # Check required columns
            required_columns = ["name", "platform", "post_type", "views", "cost"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
            else:
                # Process the data
                if st.button("Import Influencers"):
                    new_influencers = []
                    total_views = 0
                    total_cost = 0.0
                    total_likes = 0
                    total_shares = 0
                    total_comments = 0
                    
                    for _, row in df.iterrows():
                        # Create new influencer entry
                        new_influencer_id = generate_numeric_id()
                        
                        new_influencer = {
                            "id": new_influencer_id,
                            "name": row["name"],
                            "platform": row["platform"],
                            "post_type": row["post_type"],
                            "views": int(row["views"]),
                            "cost": float(row["cost"]),
                            "likes": int(row.get("likes", 0)),
                            "shares": int(row.get("shares", 0)),
                            "comments": int(row.get("comments", 0))
                        }
                        
                        # Add post_url if it exists
                        if "post_url" in df.columns:
                            new_influencer["post_url"] = row.get("post_url", "")
                        
                        new_influencers.append(new_influencer)
                        
                        # Update totals
                        total_views += int(row["views"])
                        total_cost += float(row["cost"])
                        total_likes += int(row.get("likes", 0))
                        total_shares += int(row.get("shares", 0))
                        total_comments += int(row.get("comments", 0))
                    
                    # Add to campaign
                    current_campaign["influencers"].extend(new_influencers)
                    
                    # Update metrics
                    current_campaign["metrics"]["total_views"] += total_views
                    current_campaign["metrics"]["total_cost"] += total_cost
                    current_campaign["metrics"]["total_likes"] = current_campaign["metrics"].get("total_likes", 0) + total_likes
                    current_campaign["metrics"]["total_shares"] = current_campaign["metrics"].get("total_shares", 0) + total_shares
                    current_campaign["metrics"]["total_comments"] = current_campaign["metrics"].get("total_comments", 0) + total_comments
                    
                    save_campaign_data()
                    st.success(f"Successfully imported {len(new_influencers)} influencers!")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error processing the CSV file: {str(e)}")
    
    # Export all influencers
    st.subheader("Export All Influencers")
    
    if not current_campaign["influencers"]:
        st.info("No influencers to export")
    else:
        # Create DataFrame from all influencers
        export_df = pd.DataFrame(current_campaign["influencers"])
        
        # Remove internal ID and campaign_id fields
        if "id" in export_df.columns:
            export_df = export_df.drop(columns=["id"])
        if "campaign_id" in export_df.columns:
            export_df = export_df.drop(columns=["campaign_id"])
        
        # Prepare CSV
        csv = export_df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="Export as CSV",
            data=csv,
            file_name=f"{current_campaign['name']}_influencers.csv",
            mime="text/csv"
        )
        
        st.write("This will export all influencer data in a format that can be reimported.")

# Footer
st.markdown("---")
st.markdown("Campaign Manager v1.0 | Influencer Management")