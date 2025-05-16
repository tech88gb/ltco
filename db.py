import streamlit as st
import os
import time
from datetime import datetime

# Use this to set up a fallback database for development or when actual DB is unavailable
class FallbackDB:
    def __init__(self):
        self.campaigns = {}
        # Create a sample campaign for demonstration
        sample_campaign_id = int(time.time() * 1000)
        self.campaigns[str(sample_campaign_id)] = {
            "id": sample_campaign_id,
            "name": "Sample Campaign",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "share_token": f"share_{sample_campaign_id}",
            "budget": 50000.0,
            "metrics": {
                "total_views": 0,
                "total_likes": 0,
                "total_shares": 0,
                "total_comments": 0
            },
            "influencers": []
        }

    def get_campaigns(self):
        return self.campaigns
    
    def get_campaign_by_share_token(self, token):
        for campaign_id, campaign in self.campaigns.items():
            if campaign.get('share_token') == token:
                return campaign
        return None
    
    def save_campaign(self, campaign_data):
        campaign_id = campaign_data.get('id')
        if not campaign_id:
            campaign_id = int(time.time() * 1000)
            campaign_data['id'] = campaign_id
        
        self.campaigns[str(campaign_id)] = campaign_data
        return campaign_id
    
    def save_influencer(self, influencer_data):
        campaign_id = influencer_data.get('campaign_id')
        influencer_id = influencer_data.get('id')
        
        if not influencer_id:
            influencer_id = int(time.time() * 1000)
            influencer_data['id'] = influencer_id
        
        # Find the campaign
        campaign = self.campaigns.get(str(campaign_id))
        if campaign and 'influencers' in campaign:
            # Check if influencer already exists
            for i, inf in enumerate(campaign['influencers']):
                if inf.get('id') == influencer_id:
                    campaign['influencers'][i] = influencer_data
                    break
            else:
                # Add new influencer
                campaign['influencers'].append(influencer_data)
        
        return influencer_id
    
    def delete_influencer(self, influencer_id):
        for campaign_id, campaign in self.campaigns.items():
            if 'influencers' in campaign:
                campaign['influencers'] = [inf for inf in campaign['influencers'] if inf.get('id') != influencer_id]
        return True
    
    def delete_campaign(self, campaign_id):
        if str(campaign_id) in self.campaigns:
            del self.campaigns[str(campaign_id)]
            return True
        return False

# Function to create database fallback for app initialization
# This helps your app continue working even with database connection issues
def get_db_fallback():
    if "db_fallback" not in st.session_state:
        st.session_state.db_fallback = FallbackDB()
    return st.session_state.db_fallback