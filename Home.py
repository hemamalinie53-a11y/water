"""
Water Contamination Prediction System - Home Page
Professional landing page with project overview
"""

import streamlit as st
from mongodb_handler import get_mongodb_handler
from sidebar import render_sidebar
from sidebar import render_nav_bar

# Page configuration
st.set_page_config(
    page_title="Water Contamination Prediction System",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }
    
    .hero-section {
        background: white;
        padding: 60px 40px;
        border-radius: 20px;
        margin: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        text-align: center;
    }
    
    .hero-title {
        font-size: 48px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }
    
    .hero-subtitle {
        font-size: 20px;
        color: #64748b;
        margin-bottom: 40px;
        line-height: 1.6;
    }
    
    .feature-card {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 10px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 48px;
        margin-bottom: 15px;
    }
    
    .feature-title {
        font-size: 22px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 10px;
    }
    
    .feature-desc {
        font-size: 15px;
        color: #64748b;
        line-height: 1.6;
    }
    
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 10px;
    }
    
    .stats-number {
        font-size: 36px;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .stats-label {
        font-size: 14px;
        opacity: 0.9;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 40px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: 600;
        border: none;
        cursor: pointer;
        transition: transform 0.3s ease;
        text-decoration: none;
        display: inline-block;
        margin: 10px;
    }
    
    .cta-button:hover {
        transform: scale(1.05);
    }
    
    .info-section {
        background: white;
        padding: 40px;
        border-radius: 15px;
        margin: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .section-title {
        font-size: 32px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 12px 30px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        transition: transform 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize MongoDB and auto-connect
mongo_handler = get_mongodb_handler()
render_sidebar()

# Auto-connect to MongoDB on startup
if 'mongodb_connected' not in st.session_state:
    st.session_state.mongodb_connected = False
    success, message = mongo_handler.connect()
    st.session_state.mongodb_connected = success
    st.session_state.mongodb_message = message

# Hero Section
st.markdown("""
    <div class='hero-section'>
        <div class='hero-title'>💧 Water Contamination Prediction System</div>
        <div class='hero-subtitle'>
            AI-Powered Water Quality Assessment using Machine Learning<br>
            Protecting Public Health Through Advanced Data Analysis
        </div>
    </div>
""", unsafe_allow_html=True)

# Statistics Section
st.markdown("<br>", unsafe_allow_html=True)

if mongo_handler.is_connected():
    stats = mongo_handler.get_statistics()
else:
    stats = {'total': 0, 'safe': 0, 'contaminated': 0}

# Supplement with CSV counts if MongoDB is missing records
import os, pandas as pd
if os.path.exists('water_samples_data.csv'):
    try:
        csv_df = pd.read_csv('water_samples_data.csv')
        if not csv_df.empty and 'prediction_result' in csv_df.columns:
            csv_total = len(csv_df)
            if csv_total > stats['total']:
                stats['total']        = csv_total
                stats['safe']         = len(csv_df[csv_df['prediction_result'] == 'Safe'])
                stats['contaminated'] = len(csv_df[csv_df['prediction_result'] == 'Contaminated'])
    except Exception:
        pass
    
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{stats['total']}</div>
            <div class='stats-label'>Total Samples Analyzed</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{stats['safe']}</div>
            <div class='stats-label'>Safe Water Samples</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{stats['contaminated']}</div>
            <div class='stats-label'>Contaminated Samples</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    accuracy = 95.5
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{accuracy}%</div>
            <div class='stats-label'>Model Accuracy</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Features Section
st.markdown("""
    <div class='info-section'>
        <div class='section-title'>🎯 Key Features</div>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🔬</div>
            <div class='feature-title'>ML-Powered Analysis</div>
            <div class='feature-desc'>
                Advanced Random Forest algorithm analyzes 9 water quality parameters 
                to predict contamination with high accuracy.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🌍</div>
            <div class='feature-title'>Automatic Geocoding</div>
            <div class='feature-desc'>
                Enter location names and get automatic coordinate detection 
                for precise geographical tracking.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🗄️</div>
            <div class='feature-title'>MongoDB Storage</div>
            <div class='feature-desc'>
                All predictions stored in MongoDB database for historical 
                analysis and trend monitoring.
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col4, col5, col6 = st.columns(3)

with col4:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📊</div>
            <div class='feature-title'>Real-Time Results</div>
            <div class='feature-desc'>
                Instant prediction results with confidence scores and 
                detailed parameter analysis.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>🗺️</div>
            <div class='feature-title'>Interactive Maps</div>
            <div class='feature-desc'>
                Visualize water quality across locations with color-coded 
                markers on interactive maps.
            </div>
        </div>
    """, unsafe_allow_html=True)

with col6:
    st.markdown("""
        <div class='feature-card'>
            <div class='feature-icon'>📜</div>
            <div class='feature-title'>Complete History</div>
            <div class='feature-desc'>
                Access full historical records with filtering and export 
                capabilities for analysis.
            </div>
        </div>
    """, unsafe_allow_html=True)

# How It Works Section
st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
    <div class='info-section'>
        <div class='section-title'>🚀 How It Works</div>
    </div>
""", unsafe_allow_html=True)

col_step1, col_step2, col_step3, col_step4 = st.columns(4)

with col_step1:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 48px; margin-bottom: 15px;'>1️⃣</div>
            <div style='font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px;'>
                Enter Parameters
            </div>
            <div style='font-size: 14px; color: #64748b;'>
                Input 9 water quality parameters
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_step2:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 48px; margin-bottom: 15px;'>2️⃣</div>
            <div style='font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px;'>
                Get Prediction
            </div>
            <div style='font-size: 14px; color: #64748b;'>
                AI analyzes and predicts safety
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_step3:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 48px; margin-bottom: 15px;'>3️⃣</div>
            <div style='font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px;'>
                Add Location
            </div>
            <div style='font-size: 14px; color: #64748b;'>
                Automatic coordinate detection
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_step4:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <div style='font-size: 48px; margin-bottom: 15px;'>4️⃣</div>
            <div style='font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 10px;'>
                View History
            </div>
            <div style='font-size: 14px; color: #64748b;'>
                Access all stored records
            </div>
        </div>
    """, unsafe_allow_html=True)

# Call to Action
st.markdown("<br><br>", unsafe_allow_html=True)

col_cta1, col_cta2, col_cta3 = st.columns([1, 2, 1])

with col_cta2:
    st.markdown("""
        <div style='text-align: center; padding: 30px; background: white; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <div style='font-size: 28px; font-weight: 700; color: #1e293b; margin-bottom: 15px;'>
                Ready to Analyze Water Quality?
            </div>
            <div style='font-size: 16px; color: #64748b; margin-bottom: 10px;'>
                Start predicting water contamination with our AI-powered system
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("🔬 Start Prediction", use_container_width=True):
        st.switch_page("pages/1_🔬_Prediction.py")

# Footer
st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown("""
    <div style='text-align: center; padding: 30px; color: white;'>
        <div style='font-size: 16px; font-weight: 600; margin-bottom: 10px;'>
            Water Contamination Prediction System
        </div>
        <div style='font-size: 14px; opacity: 0.8;'>
            Powered by Machine Learning & Random Forest Algorithm | Based on WHO & EPA Standards
        </div>
        <div style='font-size: 12px; opacity: 0.6; margin-top: 10px;'>
            © 2026 Water Quality Analysis System | For Professional Use
        </div>
    </div>
""", unsafe_allow_html=True)

render_nav_bar("Home.py")
