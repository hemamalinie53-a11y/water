"""
Shared sidebar component for all pages
"""
import streamlit as st

# Page order for next/prev navigation
_PAGES = [
    ("🏠 Home",        "Home.py"),
    ("🔬 Prediction",  "pages/1_\U0001f52c_Prediction.py"),
    ("📊 Results",     "pages/2_\U0001f4ca_Results.py"),
    ("\U0001f5fa\ufe0f Map",  "pages/5_\U0001f5fa\ufe0f_Map.py"),
    ("📜 History",     "pages/6_\U0001f4dc_History.py"),
]


def render_nav_bar(current: str):
    """
    Render a professional bottom navigation bar.
    """
    idx = next((i for i, (_, p) in enumerate(_PAGES) if p == current), None)
    if idx is None:
        return

    prev_label, prev_page = (_PAGES[idx - 1] if idx > 0 else (None, None))
    next_label, next_page = (_PAGES[idx + 1] if idx < len(_PAGES) - 1 else (None, None))
    cur_label = _PAGES[idx][0]

    # Dot indicators as HTML
    dots = ""
    for i, (lbl, _) in enumerate(_PAGES):
        if i == idx:
            dots += (
                f"<span title='{lbl}' style='display:inline-block;width:10px;height:10px;"
                f"border-radius:50%;background:#667eea;margin:0 4px;vertical-align:middle;'></span>"
            )
        else:
            dots += (
                f"<span title='{lbl}' style='display:inline-block;width:7px;height:7px;"
                f"border-radius:50%;background:#cbd5e1;margin:0 4px;vertical-align:middle;'></span>"
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<hr style='border:none;border-top:1px solid #e2e8f0;margin:4px 0 12px 0;'>",
        unsafe_allow_html=True
    )

    col_prev, col_mid, col_next = st.columns([3, 4, 3])

    with col_prev:
        if prev_page:
            if st.button(
                f"← {prev_label}",
                use_container_width=True,
                key=f"nav_prev_{idx}",
                help=f"Go to {prev_label}"
            ):
                st.switch_page(prev_page)

    with col_mid:
        st.markdown(
            f"<div style='text-align:center;padding:6px 0 2px 0;'>"
            f"{dots}<br>"
            f"<span style='font-size:11px;color:#94a3b8;font-weight:500;letter-spacing:0.5px;'>"
            f"{cur_label}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    with col_next:
        if next_page:
            if st.button(
                f"{next_label} →",
                use_container_width=True,
                key=f"nav_next_{idx}",
                help=f"Go to {next_label}"
            ):
                st.switch_page(next_page)


def render_sidebar():
    with st.sidebar:
        # App branding
        st.markdown("""
            <div style='text-align: center; padding: 10px 0 20px 0;'>
                <div style='font-size: 42px;'>💧</div>
                <div style='font-size: 17px; font-weight: 700; color: #1e293b; margin-top: 6px;'>
                    Water Quality AI
                </div>
                <div style='font-size: 12px; color: #94a3b8; margin-top: 2px;'>
                    Powered by Random Forest ML
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Guide section
        st.markdown("#### 📖 Guide")

        st.markdown("""
            <div style='background: #f0fdf4; border-left: 4px solid #10b981;
                        padding: 12px 14px; border-radius: 8px; margin-bottom: 10px;'>
                <div style='font-weight: 600; color: #065f46; font-size: 14px;'>
                    🟢 Beginner Mode
                </div>
                <div style='color: #374151; font-size: 13px; margin-top: 4px; line-height: 1.5;'>
                    Use this if you don't know the exact water values.
                    Answer simple questions about color, smell, and taste.
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div style='background: #eff6ff; border-left: 4px solid #667eea;
                        padding: 12px 14px; border-radius: 8px; margin-bottom: 10px;'>
                <div style='font-weight: 600; color: #1e40af; font-size: 14px;'>
                    🔬 Advanced Mode
                </div>
                <div style='color: #374151; font-size: 13px; margin-top: 4px; line-height: 1.5;'>
                    Use this for accurate AI prediction. Enter all 9 lab-measured
                    water quality parameters.
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Safe ranges quick reference
        st.markdown("#### 📏 Safe Ranges (WHO/EPA)")

        ranges = [
            ("🧪", "pH",              "6.5 – 8.5"),
            ("💧", "TDS",             "< 350 mg/L"),
            ("⚗️", "Chlorine",        "< 4 mg/L"),
            ("🌊", "Turbidity",       "< 5 NTU"),
            ("🔬", "Sulfate",         "< 250 mg/L"),
            ("⚡", "Conductivity",    "< 800 μS/cm"),
            ("🌿", "Organic Carbon",  "< 2 mg/L"),
            ("☣️", "Trihalomethanes", "< 80 μg/L"),
        ]

        for icon, name, safe in ranges:
            st.markdown(f"""
                <div style='display: flex; justify-content: space-between;
                            padding: 5px 2px; border-bottom: 1px solid #f1f5f9;
                            font-size: 13px;'>
                    <span style='color: #374151;'>{icon} {name}</span>
                    <span style='color: #6366f1; font-weight: 600;'>{safe}</span>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # Footer
        st.markdown("""
            <div style='text-align: center; font-size: 11px; color: #94a3b8; padding: 8px 0;'>
                © 2026 Water Quality AI System<br>
                Based on WHO & EPA Standards
            </div>
        """, unsafe_allow_html=True)
