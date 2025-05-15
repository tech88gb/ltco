import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
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
</style>
""", unsafe_allow_html=True)

# Helper function for PDF generation - simplified version without images
def create_simple_pdf_report(campaign, sharing_settings, filtered_df=None):
    """Create a simple text-based PDF report of the campaign without images"""
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading1"]
    subheading_style = styles["Heading2"]
    normal_style = styles["Normal"]
    
    # Content elements
    elements = []
    
    # Add title
    elements.append(Paragraph(campaign['name'], title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add date and client name
    if sharing_settings.get('client_name'):
        elements.append(Paragraph(f"Prepared for: {sharing_settings['client_name']}", normal_style))
    
    elements.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add custom message if it exists
    if sharing_settings.get('custom_message'):
        elements.append(Paragraph(sharing_settings['custom_message'], normal_style))
        elements.append(Spacer(1, 0.25*inch))
    
    # Add metrics if enabled
    if sharing_settings.get('include_metrics', True):
        elements.append(Paragraph("Campaign Performance", heading_style))
        
        # Create a table for metrics
        metrics_data = []
        metrics_headers = ["Metric", "Value"]
        metrics_data.append(metrics_headers)
        
        # Add views
        metrics_data.append(["Total Views", f"{campaign['metrics']['total_views']:,}"])
        
        # Add cost if enabled
        if sharing_settings.get('include_costs', False):
            metrics_data.append(["Total Investment", f"₹{campaign['metrics']['total_cost']:,.2f}"])
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            metrics_data.append(["Total Likes", f"{campaign['metrics'].get('total_likes', 0):,}"])
            metrics_data.append(["Total Shares", f"{campaign['metrics'].get('total_shares', 0):,}"])
            metrics_data.append(["Total Comments", f"{campaign['metrics'].get('total_comments', 0):,}"])
        
        # Create the table
        metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.5*inch))
    
    # Add summary information about the charts
    if sharing_settings.get('include_dashboard', True) and campaign['influencers']:
        elements.append(Paragraph("Performance Summary", heading_style))
        
        # Create dataframe from influencers
        influencers_df = pd.DataFrame(campaign['influencers'])
        
        # Platform distribution summary
        elements.append(Paragraph("Platform Distribution", subheading_style))
        platform_counts = influencers_df['platform'].value_counts().reset_index()
        platform_counts.columns = ['Platform', 'Count']
        
        # Create a table for platform distribution
        platform_data = [["Platform", "Count"]]
        for _, row in platform_counts.iterrows():
            platform_data.append([row['Platform'], str(row['Count'])])
        
        platform_table = Table(platform_data, colWidths=[2*inch, 1*inch])
        platform_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        
        elements.append(platform_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Post type distribution summary
        elements.append(Paragraph("Post Type Distribution", subheading_style))
        post_counts = influencers_df['post_type'].value_counts().reset_index()
        post_counts.columns = ['Post Type', 'Count']
        
        # Create a table for post type distribution
        post_data = [["Post Type", "Count"]]
        for _, row in post_counts.iterrows():
            post_data.append([row['Post Type'], str(row['Count'])])
        
        post_table = Table(post_data, colWidths=[2*inch, 1*inch])
        post_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        
        elements.append(post_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Views by platform summary
        elements.append(Paragraph("Views by Platform", subheading_style))
        platform_views = influencers_df.groupby('platform')['views'].sum().reset_index()
        
        # Create a table for views by platform
        views_data = [["Platform", "Views"]]
        for _, row in platform_views.iterrows():
            views_data.append([row['platform'], f"{row['views']:,}"])
        
        views_table = Table(views_data, colWidths=[2*inch, 2*inch])
        views_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        
        elements.append(views_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Add engagement summaries if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            elements.append(Paragraph("Engagement by Platform", subheading_style))
            platform_engagement = influencers_df.groupby('platform').agg({
                'likes': 'sum',
                'shares': 'sum',
                'comments': 'sum'
            }).reset_index()
            
            # Create a table for engagement by platform
            engagement_data = [["Platform", "Likes", "Shares", "Comments"]]
            for _, row in platform_engagement.iterrows():
                engagement_data.append([
                    row['platform'], 
                    f"{row['likes']:,}", 
                    f"{row['shares']:,}", 
                    f"{row['comments']:,}"
                ])
            
            engagement_table = Table(engagement_data, colWidths=[1.5*inch, 1.25*inch, 1.25*inch, 1.25*inch])
            engagement_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (3, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (3, 0), colors.black),
                ('ALIGN', (0, 0), (3, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (3, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
            ]))
            
            elements.append(engagement_table)
            elements.append(Spacer(1, 0.25*inch))
        
        # Add cost information if enabled
        if sharing_settings.get('include_costs', False):
            elements.append(Paragraph("Investment by Platform", subheading_style))
            platform_costs = influencers_df.groupby('platform')['cost'].sum().reset_index()
            
            # Create a table for costs by platform
            costs_data = [["Platform", "Investment (₹)"]]
            for _, row in platform_costs.iterrows():
                costs_data.append([row['platform'], f"₹{row['cost']:,.2f}"])
            
            costs_table = Table(costs_data, colWidths=[2*inch, 2*inch])
            costs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ]))
            
            elements.append(costs_table)
            elements.append(Spacer(1, 0.25*inch))
    
    # Add influencer details if enabled
    if sharing_settings.get('include_influencer_details', True) and campaign['influencers']:
        elements.append(Paragraph("Campaign Influencers", heading_style))
        
        # Get influencer data
        if filtered_df is not None and not filtered_df.empty:
            influencers_df = filtered_df
        else:
            influencers_df = pd.DataFrame(campaign['influencers'])
        
        # Select columns to display
        display_columns = ['name', 'platform', 'post_type', 'views']
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            for col in ['likes', 'shares', 'comments']:
                if col in influencers_df.columns:
                    display_columns.append(col)
        
        if sharing_settings.get('include_costs', False):
            if 'cost' in influencers_df.columns:
                display_columns.append('cost')
        
        # Create a clean display dataframe with only selected columns
        # Make sure all selected columns exist in the dataframe
        available_columns = [col for col in display_columns if col in influencers_df.columns]
        display_df = influencers_df[available_columns].copy()
        
        # Rename columns for display
        column_map = {
            'name': 'Name',
            'platform': 'Platform',
            'post_type': 'Post Type',
            'views': 'Views',
            'cost': 'Investment (₹)',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
        # Rename only the columns that exist
        display_df.columns = [column_map.get(col, col) for col in display_df.columns]
        
        # Format numeric columns
        for col in display_df.columns:
            if col == 'Views' and 'Views' in display_df.columns:
                display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Investment (₹)' and 'Investment (₹)' in display_df.columns:
                display_df['Investment (₹)'] = display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "")
            
            if col == 'Likes' and 'Likes' in display_df.columns:
                display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Shares' and 'Shares' in display_df.columns:
                display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Comments' and 'Comments' in display_df.columns:
                display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
        
        # Calculate totals row
        totals = {}
        for col in display_df.columns:
            if col == 'Name':
                totals[col] = 'TOTAL'
            elif col in ['Platform', 'Post Type']:
                totals[col] = ''
            elif col == 'Views':
                totals[col] = f"{influencers_df['views'].sum():,}"
            elif col == 'Investment (₹)':
                totals[col] = f"₹{influencers_df['cost'].sum():,.2f}"
            elif col == 'Likes':
                totals[col] = f"{influencers_df['likes'].sum():,}"
            elif col == 'Shares':
                totals[col] = f"{influencers_df['shares'].sum():,}"
            elif col == 'Comments':
                totals[col] = f"{influencers_df['comments'].sum():,}"
        
        # Add totals row to the end
        display_df = pd.concat([display_df, pd.DataFrame([totals])], ignore_index=True)
        
        # Prepare data for table
        table_data = [display_df.columns.tolist()]
        for _, row in display_df.iterrows():
            table_data.append(row.tolist())
        
        # Determine column widths based on number of columns
        num_cols = len(display_df.columns)
        col_width = 5.5 / num_cols
        col_widths = [col_width * inch] * num_cols
        
        # Create the table
        influencer_table = Table(table_data, colWidths=col_widths)
        
        # Define table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font for table data
        ])
        
        # Right-align numeric columns
        numeric_cols = ['Views', 'Investment (₹)', 'Likes', 'Shares', 'Comments']
        for col_name in numeric_cols:
            if col_name in display_df.columns:
                col_idx = display_df.columns.tolist().index(col_name)
                for row_idx in range(1, len(table_data)):
                    table_style.add('ALIGN', (col_idx, row_idx), (col_idx, row_idx), 'RIGHT')
        
        influencer_table.setStyle(table_style)
        
        # Add table to PDF
        elements.append(influencer_table)
    
    # Add footer
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Campaign Manager v1.0 | Generated Report", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def get_csv_export(campaign, filtered_df=None):
    """Generate a CSV export of the campaign data"""
    # Use filtered data if available, otherwise use all influencers
    if filtered_df is not None and not filtered_df.empty:
        df = filtered_df.copy()
    else:
        df = pd.DataFrame(campaign['influencers'])
    
    # Convert to CSV
    csv = df.to_csv(index=False)
    return csv': 'sum'
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
                fig_engagement.update_layout(width=500, height=400)
                
                # Convert to PIL Image
                engagement_img = get_image_from_plotly(fig_engagement)
                
                # Create ReportLab Image object
                img_width = 4 * inch
                img_height = (engagement_img.height / engagement_img.width) * img_width
                engagement_img_obj = Image(engagement_img, width=img_width, height=img_height)
                
                elements.append(engagement_img_obj)
                elements.append(Spacer(1, 0.25*inch))
            
            # Add cost information if enabled
            if sharing_settings.get('include_costs', False):
                elements.append(Paragraph("Investment Analysis", subheading_style))
                
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
                fig_costs.update_layout(width=500, height=400)
                
                # Convert to PIL Image
                costs_img = get_image_from_plotly(fig_costs)
                
                # Create ReportLab Image object
                img_width = 4 * inch
                img_height = (costs_img.height / costs_img.width) * img_width
                costs_img_obj = Image(costs_img, width=img_width, height=img_height)
                
                elements.append(costs_img_obj)
                elements.append(Spacer(1, 0.25*inch))
                
        except Exception as e:
            elements.append(Paragraph(f"Error generating charts: {str(e)}", normal_style))
    
    # Add influencer details if enabled
    if sharing_settings.get('include_influencer_details', True) and campaign['influencers']:
        elements.append(Paragraph("Campaign Influencers", heading_style))
        
        # Get influencer data
        if filtered_df is not None and not filtered_df.empty:
            influencers_df = filtered_df
        else:
            influencers_df = pd.DataFrame(campaign['influencers'])
        
        # Select columns to display
        display_columns = ['name', 'platform', 'post_type', 'views']
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            for col in ['likes', 'shares', 'comments']:
                if col in influencers_df.columns:
                    display_columns.append(col)
        
        if sharing_settings.get('include_costs', False):
            if 'cost' in influencers_df.columns:
                display_columns.append('cost')
        
        # Create a clean display dataframe with only selected columns
        # Make sure all selected columns exist in the dataframe
        available_columns = [col for col in display_columns if col in influencers_df.columns]
        display_df = influencers_df[available_columns].copy()
        
        # Rename columns for display
        column_map = {
            'name': 'Name',
            'platform': 'Platform',
            'post_type': 'Post Type',
            'views': 'Views',
            'cost': 'Investment (₹)',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
        # Rename only the columns that exist
        display_df.columns = [column_map.get(col, col) for col in display_df.columns]
        
        # Format numeric columns
        for col in display_df.columns:
            if col == 'Views' and 'Views' in display_df.columns:
                display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Investment (₹)' and 'Investment (₹)' in display_df.columns:
                display_df['Investment (₹)'] = display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "")
            
            if col == 'Likes' and 'Likes' in display_df.columns:
                display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Shares' and 'Shares' in display_df.columns:
                display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Comments' and 'Comments' in display_df.columns:
                display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
        
        # Prepare data for table
        table_data = [display_df.columns.tolist()]
        for _, row in display_df.iterrows():
            table_data.append(row.tolist())
        
        # Create the table
        influencer_table = Table(table_data)
        
        # Define table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Right-align numeric columns
        numeric_cols = ['Views', 'Investment (₹)', 'Likes', 'Shares', 'Comments']
        for col_name in numeric_cols:
            if col_name in display_df.columns:
                col_idx = display_df.columns.tolist().index(col_name)
                for row_idx in range(1, len(table_data)):
                    table_style.add('ALIGN', (col_idx, row_idx), (col_idx, row_idx), 'RIGHT')
        
        influencer_table.setStyle(table_style)
        
        # Add table to PDF
        elements.append(influencer_table)
    
    # Add footer
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Campaign Manager v1.0 | Generated Report", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data sure all selected columns exist in the dataframe
        available_columns = [col for col in display_columns if col in influencers_df.columns]
        display_df = influencers_df[available_columns].copy()
        
        # Rename columns for display
        column_map = {
            'name': 'Name',
            'platform': 'Platform',
            'post_type': 'Post Type',
            'views': 'Views',
            'cost': 'Investment (₹)',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
        # Rename only the columns that exist
        display_df.columns = [column_map.get(col, col) for col in display_df.columns]
        
        # Format numeric columns
        for col in display_df.columns:
            if col == 'Views' and 'Views' in display_df.columns:
                display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Investment (₹)' and 'Investment (₹)' in display_df.columns:
                display_df['Investment (₹)'] = display_df['Investment (₹)'].apply(lambda x: f"₹{x:,.2f}" if pd.notnull(x) else "")
            
            if col == 'Likes' and 'Likes' in display_df.columns:
                display_df['Likes'] = display_df['Likes'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Shares' and 'Shares' in display_df.columns:
                display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
            
            if col == 'Comments' and 'Comments' in display_df.columns:
                display_df['Comments'] = display_df['Comments'].apply(lambda x: f"{x:,}" if pd.notnull(x) else "")
        
        # Prepare data for table
        table_data = [display_df.columns.tolist()]
        for _, row in display_df.iterrows():
            table_data.append(row.tolist())
        
        # Create the table
        influencer_table = Table(table_data)
        
        # Define table style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])
        
        # Right-align numeric columns
        numeric_cols = ['Views', 'Investment (₹)', 'Likes', 'Shares', 'Comments']
        for col_name in numeric_cols:
            if col_name in display_df.columns:
                col_idx = display_df.columns.tolist().index(col_name)
                for row_idx in range(1, len(table_data)):
                    table_style.add('ALIGN', (col_idx, row_idx), (col_idx, row_idx), 'RIGHT')
        
        influencer_table.setStyle(table_style)
        
        # Add table to PDF
        elements.append(influencer_table)
    
    # Add footer
    elements.append(Spacer(1, 1*inch))
    elements.append(Paragraph("Campaign Manager v1.0 | Generated Report", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF data
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def get_pdf_download_link(pdf_data, filename):
    """Generate a download link for the PDF"""
    b64_pdf = base64.b64encode(pdf_data).decode()
    return f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}.pdf">Click to download PDF report</a>'

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

# Store filtered_df for PDF generation
filtered_df = None

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
            # Engagement breakdown by type
            engagement_by_type = influencers_df.groupby('post_type').agg({
                'likes': 'sum',
                'shares': 'sum',
                'comments': 'sum'
            }).reset_index()
            
            # Reshape for plotting
            engagement_type_melted = pd.melt(
                engagement_by_type,
                id_vars=['post_type'],
                value_vars=['likes', 'shares', 'comments'],
                var_name='Engagement Type',
                value_name='Count'
            )
            
            fig_engagement_type = px.bar(
                engagement_type_melted,
                x='post_type',
                y='Count',
                color='Engagement Type',
                title='Engagement by Post Type',
                barmode='group',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_engagement_type, use_container_width=True)
    
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
        if sharing_settings.get('include_costs', False):
            sort_options.append("Investment")
        
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
    elif sort_by == "Investment":
        filtered_df = filtered_df.sort_values('cost', ascending=False)
    
    # Display filtered results
    if not filtered_df.empty:
        # Select columns to display
        display_columns = ['name', 'platform', 'post_type', 'views']
        
        # Add engagement metrics if enabled
        if sharing_settings.get('include_engagement_metrics', True):
            display_columns.extend(['likes', 'shares', 'comments'])
        
        if sharing_settings.get('include_costs', False):
            display_columns.append('cost')
        
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
            'cost': 'Investment (₹)',
            'post_url': 'Post URL',
            'likes': 'Likes',
            'shares': 'Shares',
            'comments': 'Comments'
        }
        
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
        
        # Show record count and display the dataframe
        st.write(f"Showing {len(filtered_df)} influencers")
        st.dataframe(filtered_display_df, use_container_width=True)
    else:
        st.info("No influencers match your filter criteria")

elif not campaign['influencers']:
    st.info("No influencers added to this campaign yet.")

# Add Download Report and Export options
st.subheader("Download Options")

# Create columns for download options
download_col1, download_col2 = st.columns(2)

with download_col1:
    st.write("### PDF Report")
    st.write("Download a text-based PDF report with all campaign data.")
    
    # PDF Download button
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                # Generate PDF with current filtered data
                pdf_data = create_simple_pdf_report(campaign, sharing_settings, filtered_df)
                
                # Create download link
                pdf_filename = f"{campaign['name']}_report"
                
                # Use base64 encoding for the PDF and display download link
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}.pdf" class="download-button">Download PDF Report</a>'
                
                # Add CSS to style the download button
                st.markdown("""
                <style>
                    .download-button {
                        display: inline-block;
                        padding: 0.5em 1em;
                        background-color: #4CAF50;
                        color: white;
                        text-align: center;
                        text-decoration: none;
                        font-size: 16px;
                        border-radius: 4px;
                        border: none;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .download-button:hover {
                        background-color: #45a049;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                # Show more details for debugging
                st.error("Error details: " + str(type(e).__name__) + " - " + str(e))
                st.info("Try refreshing the page and generating the PDF again.")

with download_col2:
    st.write("### CSV Export")
    st.write("Export influencer data to CSV format for use in spreadsheet applications.")
    
    # CSV Export button
    if st.button("Export to CSV"):
        # Generate CSV with current filtered data
        csv_data = get_csv_export(campaign, filtered_df)
        
        # Create download link for CSV
        b64_csv = base64.b64encode(csv_data.encode()).decode()
        href = f'<a href="data:text/csv;base64,{b64_csv}" download="{campaign["name"]}_influencers.csv" class="download-button">Download CSV Data</a>'
        
        # Add CSS to style the download button
        st.markdown("""
        <style>
            .download-button {
                display: inline-block;
                padding: 0.5em 1em;
                background-color: #4CAF50;
                color: white;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 4px;
                border: none;
                cursor: pointer;
                margin-top: 10px;
            }
            .download-button:hover {
                background-color: #45a049;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown(href, unsafe_allow_html=True)
        st.success("CSV generated successfully!")

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
""", unsafe_allow_html=True)}")
        
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
        
        # Show record count and display the dataframe
        st.write(f"Showing {len(filtered_df)} influencers")
        st.dataframe(filtered_display_df, use_container_width=True)
    else:
        st.info("No influencers match your filter criteria")

elif not campaign['influencers']:
    st.info("No influencers added to this campaign yet.")

# Add PDF download section
st.subheader("Download Report")

# Create columns for the download section
download_col1, download_col2 = st.columns([3, 1])

with download_col1:
    st.write("Download a PDF report with all the campaign data shown above.")
    st.write("The report will include all charts and tables based on your current filter selections.")

with download_col2:
    # Generate the PDF data
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                # Generate PDF with current filtered data
                pdf_data = create_pdf_report(campaign, sharing_settings, filtered_df)
                
                # Create download link
                pdf_filename = f"{campaign['name']}_report"
                
                # Use base64 encoding for the PDF and display download link
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}.pdf" class="download-button">Download PDF Report</a>'
                
                # Add CSS to style the download button
                st.markdown("""
                <style>
                    .download-button {
                        display: inline-block;
                        padding: 0.5em 1em;
                        background-color: #4CAF50;
                        color: white;
                        text-align: center;
                        text-decoration: none;
                        font-size: 16px;
                        border-radius: 4px;
                        border: none;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .download-button:hover {
                        background-color: #45a049;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                # Show more details for debugging
                st.error("Error details: " + str(type(e).__name__) + " - " + str(e))
                st.info("Try refreshing the page and generating the PDF again.")

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

# Add PDF download section
st.subheader("Download Report")

# Create columns for the download section
download_col1, download_col2 = st.columns([3, 1])

with download_col1:
    st.write("Download a PDF report with all the campaign data shown above.")
    st.write("The report will include all charts and tables based on your current filter selections.")

with download_col2:
    # Generate the PDF data
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                # Generate PDF with current filtered data
                pdf_data = create_pdf_report(campaign, sharing_settings, filtered_df)
                
                # Create download link
                pdf_filename = f"{campaign['name']}_report"
                
                # Use base64 encoding for the PDF and display download link
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}.pdf" class="download-button">Download PDF Report</a>'
                
                # Add CSS to style the download button
                st.markdown("""
                <style>
                    .download-button {
                        display: inline-block;
                        padding: 0.5em 1em;
                        background-color: #4CAF50;
                        color: white;
                        text-align: center;
                        text-decoration: none;
                        font-size: 16px;
                        border-radius: 4px;
                        border: none;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .download-button:hover {
                        background-color: #45a049;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                # Show more details for debugging
                st.error("Error details: " + str(type(e).__name__) + " - " + str(e))
                st.info("Try refreshing the page and generating the PDF again.")

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
        
        # Show record count and display the dataframe
        st.write(f"Showing {len(filtered_df)} influencers")
        st.dataframe(filtered_display_df, use_container_width=True)
    else:
        st.info("No influencers match your filter criteria")

elif not campaign['influencers']:
    st.info("No influencers added to this campaign yet.")

# Add PDF download section
st.subheader("Download Report")

# Create columns for the download section
download_col1, download_col2 = st.columns([3, 1])

with download_col1:
    st.write("Download a PDF report with all the campaign data shown above.")
    st.write("The report will include all charts and tables based on your current filter selections.")

with download_col2:
    # Generate the PDF data
    if st.button("Generate PDF Report"):
        with st.spinner("Generating PDF report..."):
            try:
                # Generate PDF with current filtered data
                pdf_data = create_pdf_report(campaign, sharing_settings, filtered_df)
                
                # Create download link
                pdf_filename = f"{campaign['name']}_report"
                
                # Use base64 encoding for the PDF and display download link
                b64_pdf = base64.b64encode(pdf_data).decode()
                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{pdf_filename}.pdf" class="download-button">Download PDF Report</a>'
                
                # Add CSS to style the download button
                st.markdown("""
                <style>
                    .download-button {
                        display: inline-block;
                        padding: 0.5em 1em;
                        background-color: #4CAF50;
                        color: white;
                        text-align: center;
                        text-decoration: none;
                        font-size: 16px;
                        border-radius: 4px;
                        border: none;
                        cursor: pointer;
                        margin-top: 10px;
                    }
                    .download-button:hover {
                        background-color: #45a049;
                    }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(href, unsafe_allow_html=True)
                st.success("PDF generated successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
                st.info("Try refreshing the page and generating the PDF again.")

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