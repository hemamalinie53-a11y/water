"""
Water Contamination Prediction - Prediction Page
Enter water quality parameters and get AI-powered predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import pickle
import os
from datetime import datetime
from sidebar import render_sidebar
from sidebar import render_nav_bar

# Page configuration
st.set_page_config(
    page_title="Water Quality Prediction",
    page_icon="🔬",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .prediction-container {
        background: white; padding: 40px; border-radius: 15px;
        margin: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .page-title { font-size: 36px; font-weight: 700; color: #1e293b; margin-bottom: 10px; }
    .page-subtitle { font-size: 16px; color: #64748b; margin-bottom: 30px; }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; font-weight: 600; padding: 15px 40px;
        border-radius: 10px; border: none; font-size: 18px; width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Load model
@st.cache_resource
def load_model():
    if os.path.exists('model.pkl'):
        with open('model.pkl', 'rb') as f:
            return pickle.load(f)
    else:
        data = pd.read_csv("water_potability.csv")
        data = data.fillna(data.mean())
        X = data.drop("potability", axis=1)
        y = data["potability"]
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        with open('model.pkl', 'wb') as f:
            pickle.dump(model, f)
        return model

model = load_model()

render_sidebar()

# Header
st.markdown("""
    <div class='prediction-container'>
        <div class='page-title'>🔬 Water Quality Prediction</div>
        <div class='page-subtitle'>Choose the right mode for you below</div>
    </div>
""", unsafe_allow_html=True)

# ── MODE SELECTOR CARD ────────────────────────────────────────────────────────
st.markdown("""
    <div style='display:flex;gap:16px;margin:8px 0 20px 0;'>
        <div style='flex:1;background:#f0fdf4;border:2px solid #10b981;border-radius:14px;
                    padding:22px 24px;'>
            <div style='font-size:22px;margin-bottom:6px;'>👤 Regular Person?</div>
            <div style='font-size:15px;font-weight:700;color:#065f46;margin-bottom:8px;'>
                Use Quick Check
            </div>
            <div style='font-size:13px;color:#374151;line-height:1.6;'>
                You don't need any equipment or lab values.<br>
                Just answer simple questions about how your water
                <strong>looks, smells, and tastes</strong> — the AI does the rest.
            </div>
            <div style='margin-top:12px;font-size:12px;color:#6b7280;'>
                ✅ Homeowners &nbsp;·&nbsp; ✅ Well / borewell users &nbsp;·&nbsp; ✅ General public
            </div>
        </div>
        <div style='flex:1;background:#eff6ff;border:2px solid #667eea;border-radius:14px;
                    padding:22px 24px;'>
            <div style='font-size:22px;margin-bottom:6px;'>🔬 Lab / Professional?</div>
            <div style='font-size:15px;font-weight:700;color:#1e40af;margin-bottom:8px;'>
                Use Technical Mode
            </div>
            <div style='font-size:13px;color:#374151;line-height:1.6;'>
                You have <strong>actual measured values</strong> from a lab report,
                water testing kit, or instrument (pH meter, TDS meter, etc.).
            </div>
            <div style='margin-top:12px;font-size:12px;color:#6b7280;'>
                ✅ Lab technicians &nbsp;·&nbsp; ✅ Engineers &nbsp;·&nbsp; ✅ Researchers
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
_editing = any(k.startswith('adv_') for k in st.session_state)
_open_technical = _editing or st.session_state.pop('open_technical_mode', False)

tab_beginner, tab_advanced = st.tabs(["🟢 Quick Check  —  No equipment needed", "🔬 Technical Mode  —  Enter lab values"])

# Auto-click the Technical Mode tab via JS when needed
if _open_technical:
    st.markdown("""
        <script>
        (function() {
            const tabs = window.parent.document.querySelectorAll('[data-baseweb="tab"]');
            if (tabs.length >= 2) { tabs[1].click(); }
        })();
        </script>
    """, unsafe_allow_html=True)

# ── BEGINNER MODE ─────────────────────────────────────────────────────────────

# Maps beginner answers → estimated parameter values fed into the real ML model
def beginner_to_params(color, smell, smell_type, taste, residue, slippery, source, foam, flooding):
    """Translate observable answers into estimated numeric parameters."""
    # Start from safe midpoints
    p = {
        'ph': 7.2, 'hardness': 150.0, 'tds': 250.0, 'chlorine': 2.0,
        'sulfate': 120.0, 'conductivity': 400.0, 'organic_carbon': 1.2,
        'trihalomethanes': 45.0, 'turbidity': 2.5
    }

    # Appearance
    if color == "Muddy / Cloudy":
        p['turbidity']       = 10.0
        p['tds']             = 480.0
        p['conductivity']    = 750.0
    elif color == "Yellowish / Brown":
        p['turbidity']       = 7.0
        p['organic_carbon']  = 6.0
        p['tds']             = 420.0

    # Smell
    if smell == "Yes — rotten / sewage":
        p['organic_carbon']  = 8.0
        p['trihalomethanes'] = 110.0
        p['turbidity']       = max(p['turbidity'], 6.0)
    elif smell == "Yes — chlorine / bleach":
        p['chlorine']        = 6.5
        p['trihalomethanes'] = 95.0
    elif smell == "Yes — earthy / musty":
        p['organic_carbon']  = 5.0
        p['trihalomethanes'] = 70.0

    # Taste
    if taste == "Salty":
        p['tds']             = 750.0
        p['conductivity']    = 1100.0
        p['sulfate']         = 280.0
    elif taste == "Bitter / Metallic":
        p['sulfate']         = 320.0
        p['hardness']        = 450.0
        p['ph']              = 5.8
    elif taste == "Chlorine-like":
        p['chlorine']        = 5.5
        p['trihalomethanes'] = 90.0

    # Scale / residue → hard water
    if residue == "Yes":
        p['hardness']        = 480.0
        p['tds']             = max(p['tds'], 400.0)
        p['conductivity']    = max(p['conductivity'], 700.0)

    # Slippery feel → high pH
    if slippery == "Yes":
        p['ph']              = 9.2

    # Source risk adjustment
    if source == "River / Lake":
        p['turbidity']       = max(p['turbidity'], 5.5)
        p['organic_carbon']  = max(p['organic_carbon'], 3.5)
    elif source == "Borewell":
        p['hardness']        = max(p['hardness'], 280.0)
        p['tds']             = max(p['tds'], 380.0)
        p['sulfate']         = max(p['sulfate'], 180.0)
    elif source == "Open Well":
        p['turbidity']       = max(p['turbidity'], 4.5)
        p['organic_carbon']  = max(p['organic_carbon'], 2.5)
    elif source == "Rainwater / Rooftop Harvesting":
        p['tds']             = max(p['tds'], 80.0)
        p['conductivity']    = max(p['conductivity'], 150.0)
        p['organic_carbon']  = max(p['organic_carbon'], 2.0)
        p['turbidity']       = max(p['turbidity'], 3.5)
    elif source == "Pond / Canal":
        p['turbidity']       = max(p['turbidity'], 9.0)
        p['organic_carbon']  = max(p['organic_carbon'], 5.0)
        p['tds']             = max(p['tds'], 500.0)
        p['conductivity']    = max(p['conductivity'], 800.0)
    elif source == "Spring / Mountain Water":
        p['hardness']        = max(p['hardness'], 200.0)
        p['tds']             = max(p['tds'], 180.0)
        p['conductivity']    = max(p['conductivity'], 300.0)
    elif source == "Tanker / Lorry Water":
        p['turbidity']       = max(p['turbidity'], 5.0)
        p['tds']             = max(p['tds'], 420.0)
        p['organic_carbon']  = max(p['organic_carbon'], 3.0)

    # Foam / bubbles → detergent / surfactant contamination
    if foam == "Yes":
        p['organic_carbon']  = max(p['organic_carbon'], 5.5)
        p['trihalomethanes'] = max(p['trihalomethanes'], 85.0)
        p['turbidity']       = max(p['turbidity'], 5.0)

    # Recent flooding → surface runoff contamination
    if flooding == "Yes":
        p['turbidity']       = max(p['turbidity'], 8.0)
        p['organic_carbon']  = max(p['organic_carbon'], 4.5)
        p['tds']             = max(p['tds'], 450.0)
        p['conductivity']    = max(p['conductivity'], 720.0)

    return p


with tab_beginner:
    st.markdown("<div class='prediction-container'>", unsafe_allow_html=True)
    st.markdown("### 👤 Quick Check")
    st.info("💡 Answer simple questions about your water — no lab equipment needed. "
            "Your answers are mapped to water quality parameters and analyzed by the same AI model.")

    # ── Step 0: Water familiarity ─────────────────────────────────────────────
    st.markdown("#### ❓ Is this water you already use regularly?")
    water_familiarity = st.radio(
        "Water familiarity",
        ["Yes — I already use this water daily (tap, borewell, well, etc.)",
         "No — This is an unknown or new water source"],
        horizontal=False,
        help="This helps us ask the right questions and give you the right advice"
    )
    is_known_water = water_familiarity.startswith("Yes")

    # ── Unknown water warning ─────────────────────────────────────────────────
    if not is_known_water:
        st.markdown("""
            <div style='background:#fff7ed;border:2px solid #f59e0b;border-radius:12px;
                        padding:18px 20px;margin:12px 0;'>
                <div style='font-size:20px;font-weight:700;color:#92400e;margin-bottom:8px;'>
                    ⚠️ Unknown Water Source — Safety Warning
                </div>
                <div style='font-size:14px;color:#374151;line-height:1.7;'>
                    <strong>Do NOT taste or smell unknown water directly.</strong><br>
                    It may contain harmful chemicals, heavy metals, or bacteria that are
                    undetectable by sight alone.<br><br>
                    <strong>🧪 Recommended action:</strong> Send the sample to a certified water testing lab
                    for a full chemical and microbiological analysis.<br><br>
                    We can still do a <strong>basic visual analysis</strong> based on what you can safely observe.
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── Observable questions (both flows) ─────────────────────────────────────
    st.markdown("#### 👁️ What does the water look like?")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        water_color = st.radio(
            "Water appearance",
            ["Clear", "Muddy / Cloudy", "Yellowish / Brown"],
            help="Hold a glass up to light and observe — safe to do",
            horizontal=True
        )
    with col_b2:
        foam = st.radio(
            "Does it have foam or bubbles when still?",
            ["No", "Yes"],
            horizontal=True,
            help="Persistent foam (not from pouring) may indicate detergent or surfactant contamination"
        )

    st.markdown("#### 💧 Water source")
    source = st.radio(
        "Where does this water come from?",
        [
            "Tap / Municipal",
            "Borewell",
            "River / Lake",
            "Open Well",
            "Rainwater / Rooftop Harvesting",
            "Pond / Canal",
            "Spring / Mountain Water",
            "Tanker / Lorry Water",
            "Packaged / Filtered",
        ],
        horizontal=True
    )

    st.markdown("#### 🌧️ Recent flooding or heavy rain in your area?")
    flooding = st.radio(
        "Flooding / heavy rain",
        ["No", "Yes"],
        horizontal=True,
        help="Flooding can cause surface runoff to enter water sources"
    )

    # ── Known water only questions ────────────────────────────────────────────
    if is_known_water:
        st.markdown("#### 👃 Does it smell?")
        smell = st.radio(
            "Smell",
            ["No smell", "Yes — rotten / sewage", "Yes — chlorine / bleach", "Yes — earthy / musty"],
            horizontal=True
        )

        st.markdown("#### 👅 How does it taste?")
        col_b3, col_b4 = st.columns(2)
        with col_b3:
            taste = st.radio(
                "Taste",
                ["Normal", "Salty", "Bitter / Metallic", "Chlorine-like"],
                horizontal=True
            )
        with col_b4:
            slippery = st.radio(
                "Does it feel slippery or soapy on your hands?",
                ["No", "Yes"],
                help="Slippery feel = high pH (alkaline water)",
                horizontal=True
            )

        st.markdown("#### 🪨 Does it leave white scale/residue on pots or kettles?")
        residue = st.radio(
            "Scale / residue",
            ["No", "Yes"],
            help="White deposits = high mineral content (hardness)",
            horizontal=True
        )

        st.markdown("#### 🤒 Health symptoms")
        illness = st.radio(
            "Has anyone in your household had stomach illness, diarrhea, or vomiting after drinking this water?",
            ["No", "Yes"],
            horizontal=True,
            help="This is a strong indicator of possible bacterial contamination"
        )
    else:
        # Safe defaults for unknown water (no taste/smell/residue/illness questions)
        smell    = "No smell"
        taste    = "Normal"
        slippery = "No"
        residue  = "No"
        illness  = "No"

    st.markdown("<br>", unsafe_allow_html=True)
    col_bb1, col_bb2, col_bb3 = st.columns([1, 2, 1])
    with col_bb2:
        btn_label = "🔍 Analyze Water Quality" if is_known_water else "🔍 Analyze (Visual Only)"
        check_button = st.button(btn_label, use_container_width=True, key="beginner_check")

    if check_button:
        # ── Bacterial risk override ───────────────────────────────────────────
        if illness == "Yes":
            st.markdown("""
                <div style='background:linear-gradient(135deg,#7f1d1d,#991b1b);
                            padding:28px;border-radius:14px;text-align:center;color:white;
                            box-shadow:0 6px 20px rgba(153,27,27,0.4);margin-bottom:16px;'>
                    <div style='font-size:52px;'>🦠</div>
                    <div style='font-size:28px;font-weight:800;margin-top:8px;'>HIGH RISK — DO NOT DRINK</div>
                    <div style='font-size:16px;margin-top:8px;opacity:0.95;'>
                        Reported illness strongly suggests possible bacterial contamination
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.error("""
**⚠️ Immediate Action Required**

Reported stomach illness after drinking this water is a serious warning sign of **bacterial contamination** (E. coli, coliform, or other pathogens).

**Do this now:**
- 🚫 Stop drinking this water immediately
- 🔥 Boil all water before use (rolling boil for 1 minute)
- 🏥 Consult a doctor if symptoms are severe
- 🧪 Get a microbiological lab test done — chemical analysis alone cannot detect bacteria
            """)
            st.markdown("""
                <div style='background:#fef2f2;border:1px solid #fca5a5;padding:14px 16px;
                            border-radius:8px;font-size:13px;color:#7f1d1d;margin-top:8px;'>
                    🔬 <strong>Note:</strong> This app analyzes chemical parameters only (pH, TDS, turbidity, etc.).
                    Bacterial contamination <strong>cannot be detected</strong> without a certified microbiological lab test.
                    Even water that looks clear and smells normal can contain harmful bacteria.
                </div>
            """, unsafe_allow_html=True)
            st.stop()

        estimated = beginner_to_params(water_color, smell, smell, taste, residue, slippery, source, foam, flooding)
        features  = list(estimated.values())
        prediction_b  = model.predict([features])[0]
        probability_b = model.predict_proba([features])[0]
        confidence_b  = max(probability_b) * 100
        is_safe_b     = prediction_b == 1

        st.markdown("<br>", unsafe_allow_html=True)

        # Result banner
        if is_safe_b:
            st.markdown(f"""
                <div style='background:linear-gradient(135deg,#10b981,#059669);
                            padding:28px;border-radius:14px;text-align:center;color:white;
                            box-shadow:0 6px 20px rgba(16,185,129,0.3);margin-bottom:16px;'>
                    <div style='font-size:52px;'>✅</div>
                    <div style='font-size:28px;font-weight:800;margin-top:8px;'>LIKELY SAFE</div>
                    <div style='font-size:16px;margin-top:6px;opacity:0.9;'>
                        AI Confidence: <strong>{confidence_b:.1f}%</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background:linear-gradient(135deg,#ef4444,#dc2626);
                            padding:28px;border-radius:14px;text-align:center;color:white;
                            box-shadow:0 6px 20px rgba(239,68,68,0.3);margin-bottom:16px;'>
                    <div style='font-size:52px;'>🚫</div>
                    <div style='font-size:28px;font-weight:800;margin-top:8px;'>LIKELY CONTAMINATED</div>
                    <div style='font-size:16px;margin-top:6px;opacity:0.9;'>
                        AI Confidence: <strong>{confidence_b:.1f}%</strong>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # What triggered the estimate
        st.markdown("#### 🔍 What your answers suggest")
        flags = []
        if water_color != "Clear":
            flags.append(("🌊", "Appearance", f"{water_color} → elevated turbidity & dissolved solids"))
        if smell != "No smell":
            flags.append(("👃", "Smell", f"{smell} → elevated organic carbon / chlorine byproducts"))
        if taste != "Normal":
            flags.append(("👅", "Taste", f"{taste} → elevated sulfate / minerals / chlorine"))
        if residue == "Yes":
            flags.append(("🪨", "Scale residue", "High mineral hardness detected"))
        if slippery == "Yes":
            flags.append(("🧼", "Slippery feel", "High pH (alkaline) water"))
        if source in ["River / Lake", "Open Well"]:
            flags.append(("🏞️", "Source risk", f"{source} — higher contamination exposure"))
        if foam == "Yes":
            flags.append(("🫧", "Foam / bubbles", "Possible detergent or surfactant contamination"))
        if flooding == "Yes":
            flags.append(("🌧️", "Recent flooding", "Surface runoff may have entered water source — elevated turbidity & organics"))

        # Lab referral for unknown water
        if not is_known_water:
            st.markdown("""
                <div style='background:#eff6ff;border:2px solid #667eea;border-radius:12px;
                            padding:18px 20px;margin:16px 0;'>
                    <div style='font-size:18px;font-weight:700;color:#1e40af;margin-bottom:8px;'>
                        🧪 Send This Sample to a Certified Lab
                    </div>
                    <div style='font-size:14px;color:#374151;line-height:1.7;'>
                        This result is based on <strong>visual observation only</strong> — taste, smell,
                        and health data were not included since this is an unknown source.<br><br>
                        For a confirmed and safe analysis, send the water sample to a certified lab for:<br>
                        &nbsp;&nbsp;✅ Full chemical analysis (pH, TDS, heavy metals, etc.)<br>
                        &nbsp;&nbsp;✅ Microbiological testing (E. coli, coliform bacteria)<br>
                        &nbsp;&nbsp;✅ Official safety certification<br><br>
                        Once you have the lab report, use <strong>Technical Mode</strong> to enter the exact values
                        for a precise AI prediction.
                    </div>
                </div>
            """, unsafe_allow_html=True)

        if flags:
            for icon, label, detail in flags:
                st.markdown(f"""
                    <div style='background:#fef9c3;border-left:4px solid #f59e0b;
                                padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:14px;'>
                        <strong>{icon} {label}:</strong> {detail}
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No warning signs detected from your answers.")

        # Estimated parameters used
        with st.expander("📊 Estimated parameters used for AI analysis"):
            import pandas as pd
            param_labels = {
                'ph': 'pH', 'hardness': 'Hardness (mg/L)', 'tds': 'TDS (mg/L)',
                'chlorine': 'Chlorine (mg/L)', 'sulfate': 'Sulfate (mg/L)',
                'conductivity': 'Conductivity (μS/cm)', 'organic_carbon': 'Organic Carbon (mg/L)',
                'trihalomethanes': 'Trihalomethanes (μg/L)', 'turbidity': 'Turbidity (NTU)'
            }
            safe_max = {
                'ph': (6.5, 8.5), 'hardness': (0, 400), 'tds': (0, 350),
                'chlorine': (0, 4), 'sulfate': (0, 250), 'conductivity': (0, 800),
                'organic_carbon': (0, 2), 'trihalomethanes': (0, 80), 'turbidity': (0, 5)
            }
            rows = []
            for k, label in param_labels.items():
                v = estimated[k]
                lo, hi = safe_max[k]
                status = "✅ Normal" if lo <= v <= hi else ("⬆️ High" if v > hi else "⬇️ Low")
                rows.append({'Parameter': label, 'Estimated Value': f"{v:.2f}", 'Safe Range': f"{lo} – {hi}", 'Status': status})
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Disclaimer + upgrade prompt
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
            <div style='background:#fef2f2;border:1px solid #fca5a5;padding:14px 16px;
                        border-radius:8px;font-size:13px;color:#7f1d1d;margin-bottom:10px;'>
                🦠 <strong>Bacterial contamination is not covered by this analysis.</strong>
                This app checks chemical parameters only (pH, TDS, turbidity, chlorine, etc.).
                Water can look clear and test chemically safe but still contain harmful bacteria like E. coli.
                If your water is from a <strong>borewell, open well, or river</strong> — always get a
                certified microbiological lab test done periodically.
            </div>
        """, unsafe_allow_html=True)
        st.warning(
            "⚠️ **This is an estimate based on visual observations.** "
            "For a confirmed result, use Technical Mode with actual lab-measured values."
        )
        col_up1, col_up2, col_up3 = st.columns([1, 2, 1])
        with col_up2:
            if st.button("🔬 Switch to Technical Mode with these estimates", use_container_width=True, key="upgrade_btn"):
                for k, v in estimated.items():
                    st.session_state[f"adv_{k}"] = v
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ── ADVANCED MODE ─────────────────────────────────────────────────────────────

# Sample data defaults
SAMPLE_DATA = {
    'ph': 7.2, 'hardness': 150.0, 'tds': 250.0, 'chlorine': 2.0,
    'sulfate': 120.0, 'conductivity': 400.0, 'organic_carbon': 1.2,
    'trihalomethanes': 45.0, 'turbidity': 2.5
}

with tab_advanced:
    st.markdown("<div class='prediction-container'>", unsafe_allow_html=True)

    # Show edit notice if returning from Results page
    if _editing:
        st.info("✏️ **Editing previous values** — update any parameters below and re-analyze.")

    # Header row with title and Sample Data button
    col_title, col_sample = st.columns([3, 1])
    with col_title:
        st.markdown("### 🔬 Technical Mode")
        st.caption("Enter the 9 lab-measured values from your water test report or instruments. Hover ℹ️ on each field for guidance.")
    with col_sample:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📋 Use Sample Data", use_container_width=True, key="sample_data_btn",
                     help="Autofill with realistic safe water values for testing"):
            for key, val in SAMPLE_DATA.items():
                st.session_state[f"adv_{key}"] = val
            st.rerun()

    st.divider()

    with st.form("prediction_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("##### 🧪 Physical Properties")
            ph = st.number_input("pH Level *", min_value=1.0, max_value=14.0,
                value=st.session_state.get("adv_ph", None),
                step=0.1, format="%.2f",
                help="Normal range: 6.5 – 8.5 | Measure with a pH meter or test strips",
                placeholder="e.g. 7.2")
            hardness = st.number_input("Hardness (mg/L) *", min_value=0.0, max_value=1000.0,
                value=st.session_state.get("adv_hardness", None),
                step=10.0, format="%.1f",
                help="Normal range: 0 – 400 mg/L | Caused by calcium & magnesium minerals",
                placeholder="e.g. 150")
            tds = st.number_input("TDS – Total Dissolved Solids (mg/L) *", min_value=0.0,
                max_value=2000.0, value=st.session_state.get("adv_tds", None),
                step=10.0, format="%.1f",
                help="Normal range: 0 – 350 mg/L | Use a TDS meter to measure",
                placeholder="e.g. 250")

        with col2:
            st.markdown("##### ⚗️ Chemical Properties")
            chlorine = st.number_input("Chlorine (mg/L) *", min_value=0.0, max_value=10.0,
                value=st.session_state.get("adv_chlorine", None),
                step=0.1, format="%.2f",
                help="Normal range: 0 – 4 mg/L | Added for disinfection; too much is harmful",
                placeholder="e.g. 2.0")
            sulfate = st.number_input("Sulfate (mg/L) *", min_value=0.0, max_value=1000.0,
                value=st.session_state.get("adv_sulfate", None),
                step=10.0, format="%.1f",
                help="Normal range: 0 – 250 mg/L | High levels cause a bitter taste",
                placeholder="e.g. 120")
            conductivity = st.number_input("Conductivity (μS/cm) *", min_value=0.0,
                max_value=2000.0, value=st.session_state.get("adv_conductivity", None),
                step=10.0, format="%.1f",
                help="Normal range: 0 – 800 μS/cm | Measures dissolved ion concentration",
                placeholder="e.g. 400")

        with col3:
            st.markdown("##### 🌿 Organic & Clarity")
            organic_carbon = st.number_input("Organic Carbon (mg/L) *", min_value=0.0,
                max_value=50.0, value=st.session_state.get("adv_organic_carbon", None),
                step=0.1, format="%.2f",
                help="Normal range: 0 – 2 mg/L | High levels indicate organic pollution",
                placeholder="e.g. 1.2")
            trihalomethanes = st.number_input("Trihalomethanes (μg/L) *", min_value=0.0,
                max_value=200.0, value=st.session_state.get("adv_trihalomethanes", None),
                step=5.0, format="%.1f",
                help="Normal range: 0 – 80 μg/L | Byproduct of chlorine disinfection",
                placeholder="e.g. 45")
            turbidity = st.number_input("Turbidity (NTU) *", min_value=0.0, max_value=20.0,
                value=st.session_state.get("adv_turbidity", None),
                step=0.1, format="%.2f",
                help="Normal range: 0 – 5 NTU | Measures water cloudiness",
                placeholder="e.g. 2.5")

        st.markdown("<br>", unsafe_allow_html=True)
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            submit_button = st.form_submit_button("🔬 Analyze Water Sample")

    # Process prediction (outside form, inside tab)
    if submit_button:
        all_params = {
            'pH': ph, 'Hardness': hardness, 'TDS': tds, 'Chlorine': chlorine,
            'Sulfate': sulfate, 'Conductivity': conductivity,
            'Organic Carbon': organic_carbon, 'Trihalomethanes': trihalomethanes,
            'Turbidity': turbidity
        }
        missing_params = [name for name, value in all_params.items() if value is None]

        if missing_params:
            st.error(f"⚠️ **Please enter all water quality parameters before prediction.**\n\nMissing: {', '.join(missing_params)}")
            st.stop()

        features_dict = {
            'ph': ph, 'hardness': hardness, 'tds': tds, 'chlorine': chlorine,
            'sulfate': sulfate, 'conductivity': conductivity,
            'organic_carbon': organic_carbon, 'trihalomethanes': trihalomethanes,
            'turbidity': turbidity
        }
        features = list(features_dict.values())
        prediction = model.predict([features])[0]
        probability = model.predict_proba([features])[0]
        confidence = max(probability) * 100

        st.session_state.last_prediction = {
            'features_dict': features_dict,
            'prediction': prediction,
            'confidence': confidence,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        # Clear cached form values so next visit starts fresh
        for key in list(st.session_state.keys()):
            if key.startswith('adv_'):
                del st.session_state[key]
        st.switch_page("pages/2_📊_Results.py")

    # Reference Table
    with st.expander("📋 View Safe Range Reference Table"):
        st.markdown("### WHO & EPA Safe Drinking Water Standards")
        reference_data = {
            "Parameter": ["pH Level", "Hardness", "TDS", "Chlorine", "Sulfate",
                          "Conductivity", "Organic Carbon", "Trihalomethanes", "Turbidity"],
            "Safe Range": ["6.0 - 8.5", "0 - 400 mg/L", "0 - 350 mg/L", "0 - 4 mg/L",
                           "0 - 250 mg/L", "0 - 800 μS/cm", "0 - 2 mg/L", "0 - 80 μg/L", "0 - 5 NTU"],
            "Unit": ["pH units", "mg/L", "mg/L", "mg/L", "mg/L", "μS/cm", "mg/L", "μg/L", "NTU"]
        }
        st.dataframe(pd.DataFrame(reference_data), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

render_nav_bar("pages/1_🔬_Prediction.py")
