"""
Water Contamination Prediction - Results Page
"""

import streamlit as st
import pandas as pd
import pickle
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sidebar import render_sidebar
from sidebar import render_nav_bar
from pdf_report import generate_pdf
from geocoder import geocode_location

st.set_page_config(page_title="Prediction Results", page_icon="📊", layout="wide")

render_sidebar()

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .result-container {
        background: white; padding: 35px; border-radius: 15px;
        margin: 15px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; font-weight: 600; padding: 12px 30px;
        border-radius: 10px; border: none; font-size: 16px; width: 100%;
    }
    .edit-btn > button {
        background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    }
    .param-badge-normal {
        background: #d1fae5; color: #065f46; padding: 4px 12px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
    }
    .param-badge-high {
        background: #fee2e2; color: #991b1b; padding: 4px 12px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
    }
    .param-badge-low {
        background: #fef3c7; color: #92400e; padding: 4px 12px;
        border-radius: 20px; font-size: 13px; font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ── Guard ──────────────────────────────────────────────────────────────────────
if 'last_prediction' not in st.session_state:
    st.warning("⚠️ No prediction found. Please make a prediction first.")
    if st.button("🔬 Go to Prediction Page"):
        st.switch_page("pages/1_🔬_Prediction.py")
    st.stop()

recent       = st.session_state.last_prediction
prediction   = recent['prediction']
confidence   = recent['confidence']
features_dict = recent['features_dict']

# ── Edit Parameters button ─────────────────────────────────────────────────────
with st.container():
    col_edit1, col_edit2, col_edit3 = st.columns([3, 1, 3])
    with col_edit2:
        if st.button("✏️ Edit Parameters", use_container_width=True,
                     help="Go back and change the input values — your current values will be pre-filled"):
            # Load current values back into the form session state
            fd = recent['features_dict']
            st.session_state['adv_ph']               = fd['ph']
            st.session_state['adv_hardness']         = fd['hardness']
            st.session_state['adv_tds']              = fd['tds']
            st.session_state['adv_chlorine']         = fd['chlorine']
            st.session_state['adv_sulfate']          = fd['sulfate']
            st.session_state['adv_conductivity']     = fd['conductivity']
            st.session_state['adv_organic_carbon']   = fd['organic_carbon']
            st.session_state['adv_trihalomethanes']  = fd['trihalomethanes']
            st.session_state['adv_turbidity']        = fd['turbidity']
            st.switch_page("pages/1_🔬_Prediction.py")

# ── Safe ranges ────────────────────────────────────────────────────────────────
SAFE_RANGES = {
    'pH':               {'min': 6.0,  'max': 8.5,  'unit': '',      'key': 'ph'},
    'Hardness':         {'min': 0,    'max': 400,   'unit': 'mg/L',  'key': 'hardness'},
    'TDS':              {'min': 0,    'max': 350,   'unit': 'mg/L',  'key': 'tds'},
    'Chlorine':         {'min': 0,    'max': 4,     'unit': 'mg/L',  'key': 'chlorine'},
    'Sulfate':          {'min': 0,    'max': 250,   'unit': 'mg/L',  'key': 'sulfate'},
    'Conductivity':     {'min': 0,    'max': 800,   'unit': 'μS/cm', 'key': 'conductivity'},
    'Organic Carbon':   {'min': 0,    'max': 2,     'unit': 'mg/L',  'key': 'organic_carbon'},
    'Trihalomethanes':  {'min': 0,    'max': 80,    'unit': 'μg/L',  'key': 'trihalomethanes'},
    'Turbidity':        {'min': 0,    'max': 5,     'unit': 'NTU',   'key': 'turbidity'},
}

# Build violation list
violations = []   # (label, value, unit, direction)
normal_params = []

for param, cfg in SAFE_RANGES.items():
    val = features_dict[cfg['key']]
    unit = cfg['unit']
    if val < cfg['min']:
        violations.append((param, val, unit, 'Low', cfg['min'], cfg['max']))
    elif val > cfg['max']:
        violations.append((param, val, unit, 'High', cfg['min'], cfg['max']))
    else:
        normal_params.append((param, val, unit))

# Determine severity level for moderate case
is_safe        = prediction == 1
is_contaminated = prediction == 0
is_moderate    = is_contaminated and len(violations) == 0  # model says bad but params look ok

# ── 1. MAIN RESULT BANNER ─────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

if is_safe:
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #10b981, #059669);
                    padding: 40px; border-radius: 16px; text-align: center;
                    color: white; box-shadow: 0 8px 25px rgba(16,185,129,0.35); margin-bottom: 20px;'>
            <div style='font-size: 72px; margin-bottom: 12px;'>✅</div>
            <div style='font-size: 40px; font-weight: 800; letter-spacing: 1px;'>SAFE WATER</div>
            <div style='font-size: 20px; margin-top: 10px; opacity: 0.92;'>
                This water is safe for consumption
            </div>
            <div style='font-size: 18px; margin-top: 8px; opacity: 0.85;'>
                Confidence: <strong>{confidence:.2f}%</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.success(f"✅ Safe Water (Confidence: {confidence:.2f}%) — All parameters are within WHO/EPA safe drinking water limits.")

elif is_moderate:
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f59e0b, #d97706);
                    padding: 40px; border-radius: 16px; text-align: center;
                    color: white; box-shadow: 0 8px 25px rgba(245,158,11,0.35); margin-bottom: 20px;'>
            <div style='font-size: 72px; margin-bottom: 12px;'>⚠️</div>
            <div style='font-size: 40px; font-weight: 800; letter-spacing: 1px;'>MODERATE RISK</div>
            <div style='font-size: 20px; margin-top: 10px; opacity: 0.92;'>
                Water quality is uncertain — use with caution
            </div>
            <div style='font-size: 18px; margin-top: 8px; opacity: 0.85;'>
                Confidence: <strong>{confidence:.2f}%</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.warning(f"⚠️ Contaminated Water (Confidence: {confidence:.2f}%) — Individual parameters appear within range, but combined effects may pose a risk. Consider professional testing.")

else:  # Contaminated
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #ef4444, #dc2626);
                    padding: 40px; border-radius: 16px; text-align: center;
                    color: white; box-shadow: 0 8px 25px rgba(239,68,68,0.35); margin-bottom: 20px;'>
            <div style='font-size: 72px; margin-bottom: 12px;'>🚫</div>
            <div style='font-size: 40px; font-weight: 800; letter-spacing: 1px;'>CONTAMINATED WATER</div>
            <div style='font-size: 20px; margin-top: 10px; opacity: 0.92;'>
                This water is NOT safe for consumption
            </div>
            <div style='font-size: 18px; margin-top: 8px; opacity: 0.85;'>
                Confidence: <strong>{confidence:.2f}%</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.error(f"🚫 Contaminated Water (Confidence: {confidence:.2f}%) — Do not use for drinking without treatment.")

# ── 2. REASONS SECTION ────────────────────────────────────────────────────────
st.markdown("<div class='result-container'>", unsafe_allow_html=True)
st.markdown("### 🔍 Parameter Analysis & Reasons")

if violations:
    st.markdown(f"**{len(violations)} parameter(s) outside safe limits:**")
    st.markdown("<br>", unsafe_allow_html=True)

    for param, val, unit, direction, safe_min, safe_max in violations:
        icon  = "🔴" if direction == "High" else "🟡"
        color = "#fee2e2" if direction == "High" else "#fef3c7"
        text_color = "#991b1b" if direction == "High" else "#92400e"
        badge_text = f"{'Too High' if direction == 'High' else 'Too Low'}"

        st.markdown(f"""
            <div style='background: {color}; border-left: 5px solid {text_color};
                        padding: 14px 18px; border-radius: 8px; margin-bottom: 10px;
                        display: flex; align-items: center; gap: 12px;'>
                <span style='font-size: 22px;'>{icon}</span>
                <div>
                    <span style='font-weight: 700; font-size: 16px; color: {text_color};'>
                        {param}
                    </span>
                    <span style='background: {text_color}; color: white; padding: 2px 10px;
                                 border-radius: 12px; font-size: 12px; margin-left: 8px;'>
                        {badge_text}
                    </span>
                    <div style='font-size: 14px; color: #374151; margin-top: 4px;'>
                        Measured: <strong>{val:.2f} {unit}</strong> &nbsp;|&nbsp;
                        Safe range: <strong>{safe_min} – {safe_max} {unit}</strong>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.warning("""
**⚠️ Health Advisory**

Water with these violations may pose health risks. Recommended actions:
- Do not use this water for drinking or cooking without treatment
- Install appropriate filtration or purification systems
- Consult a water quality expert or local authority
- Retest after treatment to confirm safety
    """)

elif is_safe:
    if violations:
        # Safe prediction but some parameters exceed WHO limits
        st.warning(f"⚠️ AI predicts **Safe**, but {len(violations)} parameter(s) slightly exceed WHO/EPA limits. Consider retesting.")
        st.markdown("<br>", unsafe_allow_html=True)
        for param, val, unit, direction, safe_min, safe_max in violations:
            st.markdown(f"""
                <div style='background: #fff7ed; border-left: 5px solid #f59e0b;
                            padding: 14px 18px; border-radius: 8px; margin-bottom: 10px;'>
                    <span style='font-size: 20px;'>⚠️</span>
                    <span style='font-weight: 700; font-size: 15px; color: #92400e; margin-left: 8px;'>{param}</span>
                    <span style='background: #f59e0b; color: white; padding: 2px 10px;
                                 border-radius: 12px; font-size: 12px; margin-left: 8px;'>
                        Slightly {'Above' if direction == 'High' else 'Below'} WHO Limit
                    </span>
                    <div style='font-size: 14px; color: #374151; margin-top: 6px;'>
                        Your value: <strong>{val:.2f} {unit}</strong> &nbsp;|&nbsp;
                        WHO safe limit: <strong>{safe_min} – {safe_max} {unit}</strong>
                    </div>
                    <div style='font-size: 13px; color: #6b7280; margin-top: 4px;'>
                        The AI model predicted Safe based on the overall pattern of all 9 parameters,
                        but this value exceeds the WHO regulatory limit. Consider retesting or consulting a water quality expert.
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.success("✅ All 9 parameters are within safe limits. No contamination detected.")

    # Show a clean summary of all normal values
    st.markdown("<br>", unsafe_allow_html=True)
    for param, val, unit in normal_params:
        st.markdown(f"""
            <div style='background: #d1fae5; border-left: 5px solid #059669;
                        padding: 10px 16px; border-radius: 8px; margin-bottom: 8px;'>
                <span style='font-size: 16px;'>🟢</span>
                <span style='font-weight: 600; color: #065f46; margin-left: 8px;'>{param}</span>
                <span style='color: #374151; margin-left: 8px;'>{val:.2f} {unit} — Normal</span>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("ℹ️ Individual parameters appear within range. The model detected contamination based on combined parameter patterns.")

st.markdown("</div>", unsafe_allow_html=True)

# ── 3. FULL PARAMETER TABLE ───────────────────────────────────────────────────
st.markdown("<div class='result-container'>", unsafe_allow_html=True)
st.markdown("### 📋 Full Parameter Summary")

table_data = []
for param, cfg in SAFE_RANGES.items():
    val = features_dict[cfg['key']]
    unit = cfg['unit']
    if val < cfg['min']:
        status = "⬇️ Low"
    elif val > cfg['max']:
        status = "⬆️ High"
    else:
        status = "✅ Normal"
    table_data.append({
        'Parameter': param,
        'Your Value': f"{val:.2f} {unit}",
        'Safe Range': f"{cfg['min']} – {cfg['max']} {unit}",
        'Status': status
    })

st.dataframe(
    pd.DataFrame(table_data).reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Parameter": st.column_config.TextColumn("Parameter"),
        "Your Value": st.column_config.TextColumn("Your Value"),
        "Safe Range": st.column_config.TextColumn("Safe Range (WHO/EPA)"),
        "Status": st.column_config.TextColumn("Status"),
    }
)

st.markdown("</div>", unsafe_allow_html=True)

# ── 4. FEATURE IMPORTANCE ─────────────────────────────────────────────────────
st.markdown("<div class='result-container'>", unsafe_allow_html=True)
st.markdown("### 📊 Feature Importance in Water Quality Prediction")
st.caption("Shows which parameters the Random Forest model relies on most when making predictions.")

@st.cache_resource
def load_model_for_importance():
    if os.path.exists('model.pkl'):
        with open('model.pkl', 'rb') as f:
            return pickle.load(f)
    return None

_model = load_model_for_importance()

if _model is not None:
    feature_names = ['pH', 'Hardness', 'TDS', 'Chlorine', 'Sulfate',
                     'Conductivity', 'Organic Carbon', 'Trihalomethanes', 'Turbidity']
    importances = _model.feature_importances_

    # Sort descending
    sorted_idx = importances.argsort()[::-1]
    sorted_names = [feature_names[i] for i in sorted_idx]
    sorted_vals  = [importances[i] for i in sorted_idx]

    # Color: highlight the top feature in deep purple, rest in gradient blue
    colors = ['#7c3aed' if i == 0 else '#818cf8' for i in range(len(sorted_names))]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    bars = ax.barh(sorted_names[::-1], sorted_vals[::-1], color=colors[::-1],
                   edgecolor='white', height=0.6)

    # Value labels on bars
    for bar, val in zip(bars, sorted_vals[::-1]):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f'{val:.3f}', va='center', ha='left', fontsize=10, color='#374151')

    ax.set_xlabel('Importance Score', fontsize=11, color='#374151')
    ax.set_title('Feature Importance in Water Quality Prediction',
                 fontsize=13, fontweight='bold', color='#1e293b', pad=12)
    ax.set_xlim(0, max(sorted_vals) * 1.18)
    ax.tick_params(axis='y', labelsize=11, colors='#374151')
    ax.tick_params(axis='x', labelsize=10, colors='#6b7280')
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax.set_axisbelow(True)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close(fig)

    # Top 3 insight callout
    st.markdown("<br>", unsafe_allow_html=True)
    top3 = sorted_names[:3]
    st.info(f"💡 The top 3 most influential parameters are: **{top3[0]}**, **{top3[1]}**, and **{top3[2]}**. "
            f"These have the greatest impact on whether water is predicted as safe or contaminated.")
else:
    st.warning("⚠️ Model file not found. Feature importance unavailable.")

st.markdown("</div>", unsafe_allow_html=True)

# ── 5. DOWNLOAD PDF REPORT ────────────────────────────────────────────────────
st.markdown("<div class='result-container'>", unsafe_allow_html=True)
st.markdown("### 📄 Download Report")
st.caption("Generate a clean PDF report with all input values, prediction result, reasons, and date/time.")

col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])
with col_pdf2:
    # Build report data (include location/source if already saved in session)
    report_data = {
        **recent,
        'location_name': st.session_state.get('last_location', 'Not specified'),
        'water_source':  st.session_state.get('last_water_source', 'Not specified'),
    }
    try:
        pdf_bytes = generate_pdf(report_data)
        st.download_button(
            label="📥 Download Report as PDF",
            data=pdf_bytes,
            file_name=f"water_quality_report_{recent.get('timestamp','').replace(' ','_').replace(':','-')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as e:
        st.error(f"❌ Could not generate PDF: {e}")

st.markdown("</div>", unsafe_allow_html=True)

# ── 6. WATER SAMPLE DETAILS ───────────────────────────────────────────────────
from geocoder import COMMON_LOCATIONS

st.markdown("<div class='result-container'>", unsafe_allow_html=True)
st.markdown("### 📍 Water Sample Details")

st.markdown("""
    <div style='background:#eff6ff; border-left:4px solid #667eea; padding:12px 16px;
                border-radius:8px; margin-bottom:16px; font-size:14px; color:#1e40af;'>
        📌 <strong>How location fields work:</strong><br><br>
        <table style='font-size:13px; border-collapse:collapse; width:100%;'>
            <tr>
                <td style='padding:4px 8px;'>🏙️ <strong>City / Town</strong></td>
                <td style='padding:4px 8px;color:#374151;'>Used for map pin — enter city + country for accuracy<br>
                    <code style='background:#dbeafe;padding:2px 6px;border-radius:4px;'>Salem, Tamil Nadu, India</code> &nbsp;
                    <code style='background:#dbeafe;padding:2px 6px;border-radius:4px;'>Dubai, UAE</code>
                </td>
            </tr>
            <tr>
                <td style='padding:4px 8px;'>🏘️ <strong>Area / Locality</strong></td>
                <td style='padding:4px 8px;color:#374151;'>Stored for reference only — not used for geocoding<br>
                    <code style='background:#dbeafe;padding:2px 6px;border-radius:4px;'>Anna Nagar</code> &nbsp;
                    <code style='background:#dbeafe;padding:2px 6px;border-radius:4px;'>Gandhi Road</code>
                </td>
            </tr>
        </table>
    </div>
""", unsafe_allow_html=True)

# City suggestion dropdown (outside form)
city_suggestion = st.selectbox(
    "📋 Quick-pick a city (optional)",
    options=COMMON_LOCATIONS,
    index=0,
    help="Select a common city to auto-fill below, or type your own."
)

with st.form("sample_details_form"):
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        city_prefill = "" if city_suggestion == "-- Type your own --" else city_suggestion
        city_name = st.text_input(
            "🏙️ City / Town *",
            value=city_prefill,
            placeholder="e.g., Salem, Tamil Nadu, India",
            help="Used for map pin — City, State, Country format gives best accuracy"
        )
    with col_d2:
        area_name = st.text_input(
            "🏘️ Area / Locality (optional)",
            placeholder="e.g., Anna Nagar, Gandhi Road",
            help="Stored for reference only — not used for geocoding or map plotting"
        )

    col_d3, col_d4 = st.columns(2)
    with col_d3:
        water_source = st.selectbox(
            "💧 Water Source *",
            [
                "Select source...",
                "Tap / Municipal",
                "Borewell",
                "River",
                "Lake",
                "Open Well",
                "Pond / Canal",
                "Spring / Mountain Water",
                "Rainwater / Rooftop Harvesting",
                "Tanker / Lorry Water",
                "Tank Water",
                "Packaged / Filtered",
                "Other"
            ]
        )

    st.markdown("<br>", unsafe_allow_html=True)
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        save_button = st.form_submit_button("💾 Save Water Sample Details")

if save_button:
    # ── Validate ───────────────────────────────────────────────────────────────
    if not city_name or not city_name.strip():
        st.error("⚠️ Please enter a city name — e.g., 'Salem, Tamil Nadu, India'")
        st.stop()
    if water_source == "Select source...":
        st.error("⚠️ Please select a water source")
        st.stop()

    from mongodb_handler import get_mongodb_handler, generate_sample_id
    from datetime import datetime
    import os

    # ── Geocode using CITY only — never area name ──────────────────────────────
    with st.spinner(f"🔍 Getting coordinates for: {city_name.strip()}"):
        geo_result = geocode_location(city_name.strip())

    if not geo_result['success']:
        st.error(
            f"❌ **City not found:** '{city_name}'\n\n"
            "Use format **City, State, Country** — e.g. `Salem, Tamil Nadu, India` · `Dubai, UAE`"
        )
        st.stop()

    latitude         = geo_result['latitude']
    longitude        = geo_result['longitude']
    geocoded_address = geo_result['address']
    area_clean       = area_name.strip() if area_name and area_name.strip() else ""

    # Display label: "Anna Nagar, Salem" if area given, else just "Salem"
    display_location = f"{area_clean}, {city_name.strip()}" if area_clean else city_name.strip()

    # ── Save data ──────────────────────────────────────────────────────────────
    sample_data = {
        'sample_id':        generate_sample_id(),
        'timestamp':        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'city_name':        city_name.strip(),
        'area_name':        area_clean,
        'location_name':    display_location,   # "Area, City" for display
        'water_source':     water_source,
        'latitude':         latitude,            # from city geocoding only
        'longitude':        longitude,
        **{k: features_dict[k] for k in features_dict},
        'prediction_result': 'Safe' if prediction == 1 else 'Contaminated',
        'confidence':       confidence
    }

    mongo_handler = get_mongodb_handler()
    if not mongo_handler.is_connected():
        mongo_handler.connect()

    success_mongo = False
    if mongo_handler.is_connected():
        success_mongo, _, __ = mongo_handler.insert_water_sample(sample_data)

    success_csv = False
    try:
        new_df = pd.DataFrame([sample_data])
        if os.path.exists('water_samples_data.csv'):
            combined = pd.concat([pd.read_csv('water_samples_data.csv'), new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_csv('water_samples_data.csv', index=False)
        success_csv = True
    except Exception:
        pass

    if success_mongo or success_csv:
        st.session_state['last_location']     = display_location
        st.session_state['last_water_source'] = water_source

        st.markdown(f"""
            <div style='background:#f0fdf4; border:1px solid #10b981; padding:14px 16px;
                        border-radius:8px; font-size:13px; color:#065f46; margin-bottom:10px;'>
                ✅ <strong>Saved successfully</strong><br><br>
                🆔 <strong>Sample ID:</strong> {sample_data['sample_id']}<br>
                🏙️ <strong>City:</strong> {city_name.strip()}<br>
                {'🏘️ <strong>Area:</strong> ' + area_clean + '<br>' if area_clean else ''}
                📍 <strong>Geocoded as:</strong> {geocoded_address}<br>
                🌐 <strong>Coordinates:</strong> Lat {latitude:.6f}, Lon {longitude:.6f}
            </div>
        """, unsafe_allow_html=True)
        st.success(
            f"✅ **Saved!**  🆔 `{sample_data['sample_id']}`  |  "
            f"💧 {water_source}  |  "
            f"{'✅ Safe' if prediction == 1 else '🚫 Contaminated'}  |  "
            f"{confidence:.2f}%"
        )
    else:
        st.error("❌ Failed to save. Please try again.")

st.markdown("</div>", unsafe_allow_html=True)

render_nav_bar("pages/2_📊_Results.py")
