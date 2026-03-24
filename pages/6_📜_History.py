"""
Water Contamination Prediction - History Page
View all stored water quality records from MongoDB
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from mongodb_handler import get_mongodb_handler
from sidebar import render_sidebar
from sidebar import render_nav_bar

# Page configuration
st.set_page_config(
    page_title="History Records",
    page_icon="📜",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .history-container {
        background: white;
        padding: 40px;
        border-radius: 15px;
        margin: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .page-title {
        font-size: 36px;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 10px;
    }
    
    .page-subtitle {
        font-size: 16px;
        color: #64748b;
        margin-bottom: 30px;
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
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 12px 30px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize MongoDB and auto-connect
mongo_handler = get_mongodb_handler()
render_sidebar()
if 'mongodb_connected' not in st.session_state:
    st.session_state.mongodb_connected = False
    success, message = mongo_handler.connect()
    st.session_state.mongodb_connected = success

# Header
st.markdown("""
    <div class='history-container'>
        <div class='page-title'>📜 Water Quality History</div>
        <div class='page-subtitle'>View all stored water quality analysis records</div>
    </div>
""", unsafe_allow_html=True)

# Silently check MongoDB connection
if not mongo_handler.is_connected():
    mongo_handler.connect()

# ── Merged stats (MongoDB + CSV) ──────────────────────────────────────────────
import os, pandas as pd

def get_merged_stats():
    frames = []
    mongo_samples = mongo_handler.get_all_samples()
    if mongo_samples:
        mdf = pd.DataFrame(mongo_samples)
        if '_id' in mdf.columns:
            mdf = mdf.drop('_id', axis=1)
        frames.append(mdf)
    if os.path.exists('water_samples_data.csv'):
        try:
            frames.append(pd.read_csv('water_samples_data.csv'))
        except Exception:
            pass
    if not frames:
        return {'total': 0, 'safe': 0, 'contaminated': 0}
    combined = pd.concat(frames, ignore_index=True)
    if 'sample_id' in combined.columns:
        combined = combined.drop_duplicates(subset=['sample_id'], keep='first')
    else:
        combined = combined.drop_duplicates(subset=['timestamp', 'location_name'], keep='first')
    total = len(combined)
    safe  = int((combined['prediction_result'] == 'Safe').sum()) if 'prediction_result' in combined.columns else 0
    cont  = int((combined['prediction_result'] == 'Contaminated').sum()) if 'prediction_result' in combined.columns else 0
    return {'total': total, 'safe': safe, 'contaminated': cont}

stats = get_merged_stats()

# Statistics Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{stats['total']}</div>
            <div class='stats-label'>Total Samples</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class='stats-card' style='background: linear-gradient(135deg, #10b981 0%, #059669 100%);'>
            <div class='stats-number'>{stats['safe']}</div>
            <div class='stats-label'>Safe Samples</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class='stats-card' style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);'>
            <div class='stats-number'>{stats['contaminated']}</div>
            <div class='stats-label'>Contaminated</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    if stats['total'] > 0:
        safe_pct = (stats['safe'] / stats['total']) * 100
    else:
        safe_pct = 0
    
    st.markdown(f"""
        <div class='stats-card'>
            <div class='stats-number'>{safe_pct:.1f}%</div>
            <div class='stats-label'>Safe Percentage</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Display Records
st.markdown("<div class='history-container'>", unsafe_allow_html=True)

if stats['total'] > 0:
    st.markdown("### 📊 All Water Quality Records")
    
    # Get all samples — merge MongoDB + CSV, deduplicate
    import os
    mongo_samples = mongo_handler.get_all_samples()
    csv_df = pd.DataFrame()

    if os.path.exists('water_samples_data.csv'):
        try:
            csv_df = pd.read_csv('water_samples_data.csv')
        except Exception:
            pass

    frames = []
    if mongo_samples:
        mdf = pd.DataFrame(mongo_samples)
        if '_id' in mdf.columns:
            mdf = mdf.drop('_id', axis=1)
        frames.append(mdf)
    if not csv_df.empty:
        frames.append(csv_df)

    if frames:
        mongo_df = pd.concat(frames, ignore_index=True)
        if 'sample_id' in mongo_df.columns:
            mongo_df = mongo_df.drop_duplicates(subset=['sample_id'], keep='first')
        elif 'timestamp' in mongo_df.columns and 'location_name' in mongo_df.columns:
            mongo_df = mongo_df.drop_duplicates(subset=['timestamp', 'location_name'], keep='first')
    else:
        mongo_df = pd.DataFrame()

    if mongo_df.empty:
        st.info("📊 No records found.")
    else:
        # Filters
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            filter_result = st.selectbox(
                "Filter by Result",
                ["All", "Safe", "Contaminated"]
            )
        
        with col_filter2:
            sort_by = st.selectbox(
                "Sort by",
                ["Newest First", "Oldest First", "Confidence (High to Low)", "Confidence (Low to High)"]
            )
        
        # Apply filters
        filtered_df = mongo_df.copy()
        
        if filter_result != "All":
            filtered_df = filtered_df[filtered_df['prediction_result'] == filter_result]
        
        # Apply sorting
        if sort_by == "Newest First":
            filtered_df = filtered_df.sort_values('timestamp', ascending=False)
        elif sort_by == "Oldest First":
            filtered_df = filtered_df.sort_values('timestamp', ascending=True)
        elif sort_by == "Confidence (High to Low)":
            filtered_df = filtered_df.sort_values('confidence', ascending=False)
        elif sort_by == "Confidence (Low to High)":
            filtered_df = filtered_df.sort_values('confidence', ascending=True)
        
        filtered_df = filtered_df.reset_index(drop=True)
        
        st.markdown(f"**Showing {len(filtered_df)} of {len(mongo_df)} records**")
        
        # Columns to display — include sample_id when present
        display_cols = ['sample_id', 'timestamp', 'city_name', 'area_name', 'location_name',
                        'water_source', 'prediction_result', 'confidence',
                        'ph', 'hardness', 'tds', 'chlorine', 'sulfate',
                        'conductivity', 'organic_carbon', 'trihalomethanes', 'turbidity']
        display_cols = [c for c in display_cols if c in filtered_df.columns]
        display_df = filtered_df[display_cols]
        
        column_names = {
            'sample_id': 'Sample ID',
            'timestamp': 'Timestamp',
            'city_name': 'City',
            'area_name': 'Area / Locality',
            'location_name': 'Full Location',
            'water_source': 'Water Source',
            'prediction_result': 'Result',
            'confidence': 'Confidence (%)',
            'ph': 'pH', 'hardness': 'Hardness', 'tds': 'TDS',
            'chlorine': 'Chlorine', 'sulfate': 'Sulfate',
            'conductivity': 'Conductivity', 'organic_carbon': 'Organic Carbon',
            'trihalomethanes': 'Trihalomethanes', 'turbidity': 'Turbidity'
        }
        display_df = display_df.rename(columns=column_names)
        
        st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config={
                    "Sample ID":        st.column_config.TextColumn("Sample ID"),
                    "City":             st.column_config.TextColumn("City"),
                    "Area / Locality":  st.column_config.TextColumn("Area / Locality"),
                    "Full Location":    st.column_config.TextColumn("Full Location"),
                    "Result":           st.column_config.TextColumn("Result"),
                    "Confidence (%)":   st.column_config.NumberColumn("Confidence (%)", format="%.1f%%"),
                    "pH":               st.column_config.NumberColumn("pH", format="%.2f"),
                    "Hardness":         st.column_config.NumberColumn("Hardness", format="%.1f"),
                    "TDS":              st.column_config.NumberColumn("TDS", format="%.1f"),
                    "Chlorine":         st.column_config.NumberColumn("Chlorine", format="%.2f"),
                    "Turbidity":        st.column_config.NumberColumn("Turbidity", format="%.2f"),
                }
            )
        
        # Download
        st.markdown("<br>", unsafe_allow_html=True)

        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            csv_data = display_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=f"water_quality_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # Database Management
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("🗑️ Database Management"):
            st.warning("⚠️ **Caution:** This will permanently delete all samples from MongoDB.")
            
            col_del1, col_del2, col_del3 = st.columns([1, 1, 1])
            
            with col_del2:
                if st.button("Clear All Records", type="secondary", use_container_width=True):
                    success, message = mongo_handler.delete_all_samples()
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

else:
    st.info("📊 No water quality records found. Start by analyzing water samples!")

st.markdown("</div>", unsafe_allow_html=True)

render_nav_bar("pages/6_\U0001f4dc_History.py")
