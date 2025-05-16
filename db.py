import streamlit as st
import os
import time
from datetime import datetime
from dotenv import load_dotenv
#gdsjabsdj
# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_numeric_id():
    """Generate a unique numeric ID based on the current timestamp"""
    return int(time.time() * 1000)  # Milliseconds since epoch as an integer

def save_campaign(campaign_data):
    """Save campaign data to Supabase"""
    # Use an integer ID instead of UUID
    campaign_id = campaign_data.get('id')
    if not campaign_id or not isinstance(campaign_id, int):
        campaign_id = generate_numeric_id()
    
    # Format the data for Supabase
    supabase_campaign = {
        'id': campaign_id,
        'name': campaign_data.get('name'),
        'created_at': campaign_data.get('created_at'),
        'share_token': campaign_data.get('share_token'),
        'metrics': campaign_data.get('metrics', {})
    }
    
    # Add sharing settings if they exist
    if 'sharing_settings' in campaign_data:
        supabase_campaign['sharing_settings'] = campaign_data['sharing_settings']
    
    # Insert or update campaign
    result = supabase.table('campaigns').upsert(supabase_campaign).execute()
    
    # Handle influencers
    if 'influencers' in campaign_data:
        for influencer in campaign_data['influencers']:
            influencer['campaign_id'] = campaign_id
            save_influencer(influencer)
    
    return campaign_id

def save_influencer(influencer_data):
    """Save influencer data to Supabase with only the fields in your schema"""
    # For influencer ID, also use numeric ID
    influencer_id = influencer_data.get('id')
    if not influencer_id or not isinstance(influencer_id, int):
        influencer_id = generate_numeric_id()
    
    # Format the data for Supabase
    supabase_influencer = {
        'id': influencer_id,
        'campaign_id': influencer_data.get('campaign_id'),
        'name': influencer_data.get('name'),
        'platform': influencer_data.get('platform'),
        'post_type': influencer_data.get('post_type'),
        'views': influencer_data.get('views', 0),
        'cost': influencer_data.get('cost', 0),
        'likes': influencer_data.get('likes', 0),
        'shares': influencer_data.get('shares', 0),
        'comments': influencer_data.get('comments', 0)
    }
    
    # Add post_url if it exists
    if 'post_url' in influencer_data:
        supabase_influencer['post_url'] = influencer_data.get('post_url', '')
    
    # Insert or update influencer
    result = supabase.table('influencers').upsert(supabase_influencer).execute()
    return influencer_id

def get_campaigns():
    """Get all campaigns from Supabase"""
    response = supabase.table('campaigns').select('*').execute()
    campaigns = {}
    
    for campaign in response.data:
        campaign_id = campaign['id']
        # Get influencers for this campaign
        influencers_response = supabase.table('influencers').select('*').eq('campaign_id', campaign_id).execute()
        
        campaigns[str(campaign_id)] = {  # Convert ID to string for dictionary key
            'id': campaign_id,
            'name': campaign['name'],
            'created_at': campaign['created_at'],
            'share_token': campaign['share_token'],
            'metrics': campaign['metrics'],
            'influencers': influencers_response.data
        }
        
        # Add sharing settings if they exist
        if 'sharing_settings' in campaign:
            campaigns[str(campaign_id)]['sharing_settings'] = campaign['sharing_settings']
    
    return campaigns

def get_campaign_by_share_token(token):
    """Get campaign by share token"""
    response = supabase.table('campaigns').select('*').eq('share_token', token).execute()
    
    if not response.data:
        return None
    
    campaign = response.data[0]
    campaign_id = campaign['id']
    
    # Get influencers for this campaign
    influencers_response = supabase.table('influencers').select('*').eq('campaign_id', campaign_id).execute()
    
    result = {
        'id': campaign_id,
        'name': campaign['name'],
        'created_at': campaign['created_at'],
        'share_token': campaign['share_token'],
        'metrics': campaign['metrics'],
        'influencers': influencers_response.data
    }
    
    # Add sharing settings if they exist
    if 'sharing_settings' in campaign:
        result['sharing_settings'] = campaign['sharing_settings']
    
    return result

def delete_influencer(influencer_id):
    """Delete an influencer from Supabase"""
    response = supabase.table('influencers').delete().eq('id', influencer_id).execute()
    return response.data

def delete_campaign(campaign_id):
    """Delete a campaign and all its influencers from Supabase"""
    # First delete all influencers
    supabase.table('influencers').delete().eq('campaign_id', campaign_id).execute()
    
    # Then delete the campaign
    response = supabase.table('campaigns').delete().eq('id', campaign_id).execute()
    return response.data