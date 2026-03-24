"""
Water Quality Map — groups samples by location.
Each map marker represents one unique lat/lon.
Clicking a marker shows ALL samples collected at that location,
differentiated by sample_id and timestamp.
"""

import time
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
from mongodb_handler import get_mongodb_handler
from geocoder import geocode_location
from sidebar import render_sidebar
from sidebar import render_nav_bar

st.set_page_config(page_title="Water Quality Map", page_icon="🗺️", layout="wide")

st.markdown("""
    <style>
    .main { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
    .map-container {
        background: white; padding: 28px; border-radius: 15px;
        margin: 12px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stats-card {
        padding: 20px; border-radius: 12px; color: white;
        text-align: center; font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

mongo_handler = get_mongodb_handler()
render_sidebar()

if 'mongodb_connected' not in st.session_state:
    success, _ = mongo_handler.connect()
    st.session_state.mongodb_connected = success


# ── Data loader ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    """Merge MongoDB + CSV, deduplicate by sample_id when available."""
    frames = []

    if mongo_handler.is_connected():
        samples = mongo_handler.get_all_samples()
        if samples:
            df = pd.DataFrame(samples)
            if '_id' in df.columns:
                df = df.drop('_id', axis=1)
            frames.append(df)

    if os.path.exists('water_samples_data.csv'):
        try:
            csv_df = pd.read_csv('water_samples_data.csv')
            frames.append(csv_df)
        except Exception:
            pass

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)

    # Deduplicate: prefer sample_id if present, else timestamp+location
    if 'sample_id' in combined.columns:
        combined = combined.drop_duplicates(subset=['sample_id'], keep='first')
    else:
        combined = combined.drop_duplicates(subset=['timestamp', 'location_name'], keep='first')

    return combined.reset_index(drop=True)


# ── Cached geocoding ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def cached_geocode(location: str) -> dict:
    result = geocode_location(location)
    if not result['success']:
        time.sleep(2)
        result = geocode_location(location)
    return result


# ── Group samples by rounded coordinates ─────────────────────────────────────
def group_by_location(df: pd.DataFrame) -> list:
    """
    Group rows by (lat rounded to 4dp, lon rounded to 4dp).
    Returns list of dicts: {lat, lon, location_name, samples: [...]}.
    """
    df = df.copy()
    df['_lat_r'] = df['latitude'].round(4)
    df['_lon_r'] = df['longitude'].round(4)

    groups = []
    for (lat_r, lon_r), grp in df.groupby(['_lat_r', '_lon_r']):
        grp = grp.sort_values('timestamp', ascending=False)
        groups.append({
            'lat':           lat_r,
            'lon':           lon_r,
            'location_name': grp['location_name'].iloc[0],
            'samples':       grp.to_dict('records'),
        })
    return groups


# ── Build popup HTML for a location group ────────────────────────────────────
def build_popup_html(group: dict) -> str:
    samples   = group['samples']
    loc_name  = group['location_name']
    n         = len(samples)

    # Use city_name for header if available
    city_display = samples[0].get('city_name', loc_name) if samples else loc_name

    results   = [s.get('prediction_result', '') for s in samples]
    all_safe  = all(r == 'Safe' for r in results)
    any_cont  = any(r == 'Contaminated' for r in results)
    hdr_color = '#10b981' if all_safe else ('#ef4444' if any_cont else '#f59e0b')

    rows_html = ''
    for s in samples:
        sid    = s.get('sample_id', '—')
        ts     = str(s.get('timestamp', '—'))
        result = s.get('prediction_result', '—')
        conf   = s.get('confidence', 0)
        src    = s.get('water_source', '—')
        area   = s.get('area_name', '')
        r_color = '#10b981' if result == 'Safe' else '#ef4444'
        r_icon  = '✅' if result == 'Safe' else '🚫'

        params = [
            ('pH',    s.get('ph',    '—')),
            ('TDS',   s.get('tds',   '—')),
            ('Cl',    s.get('chlorine', '—')),
            ('Turb',  s.get('turbidity', '—')),
        ]
        param_cells = ''.join(
            f"<td style='padding:2px 6px;color:#374151;'>"
            f"<span style='color:#6b7280;font-size:10px;'>{k}</span><br>"
            f"<strong style='font-size:11px;'>{f'{v:.2f}' if isinstance(v, float) else v}</strong></td>"
            for k, v in params
        )

        area_row = (
            f"<div style='margin-bottom:4px;color:#374151;'>"
            f"<span style='color:#6b7280;'>🏘️</span> Area: <strong>{area}</strong></div>"
            if area else ""
        )

        rows_html += f"""
        <div style='border:1px solid #e5e7eb;border-radius:8px;margin-bottom:8px;overflow:hidden;'>
            <div style='background:{r_color};color:white;padding:7px 10px;
                        display:flex;justify-content:space-between;align-items:center;'>
                <span style='font-size:12px;font-weight:700;'>{r_icon} {result}</span>
                <span style='font-size:11px;opacity:0.9;background:rgba(0,0,0,0.15);
                             padding:2px 7px;border-radius:10px;'>{conf:.1f}%</span>
            </div>
            <div style='padding:8px 10px;background:#fafafa;font-size:12px;'>
                <div style='margin-bottom:4px;'>
                    <span style='color:#6b7280;'>🆔</span>
                    <strong style='color:#1e293b;margin-left:4px;font-family:monospace;'>{sid}</strong>
                </div>
                <div style='margin-bottom:4px;color:#374151;'>
                    <span style='color:#6b7280;'>🕐</span> {ts}
                </div>
                {area_row}
                <div style='margin-bottom:6px;color:#374151;'>
                    <span style='color:#6b7280;'>💧</span> {src}
                </div>
                <table style='border-collapse:collapse;width:100%;'><tr>{param_cells}</tr></table>
            </div>
        </div>"""

    summary_badge = (
        f"<span style='background:#10b981;color:white;padding:2px 8px;border-radius:10px;"
        f"font-size:11px;margin-right:4px;'>{results.count('Safe')} Safe</span>"
        if results.count('Safe') else ''
    ) + (
        f"<span style='background:#ef4444;color:white;padding:2px 8px;border-radius:10px;"
        f"font-size:11px;'>{results.count('Contaminated')} Contaminated</span>"
        if results.count('Contaminated') else ''
    )

    return f"""
    <div style='font-family:Arial;width:300px;max-height:420px;overflow-y:auto;'>
        <div style='background:{hdr_color};color:white;padding:12px 14px;
                    border-radius:8px 8px 0 0;position:sticky;top:0;z-index:1;'>
            <div style='font-size:15px;font-weight:700;'>🏙️ {city_display}</div>
            <div style='font-size:12px;margin-top:4px;opacity:0.9;'>
                {n} sample{'s' if n > 1 else ''} &nbsp;·&nbsp; {summary_badge}
            </div>
        </div>
        <div style='padding:10px;background:#f9fafb;border:1px solid #e5e7eb;
                    border-top:none;border-radius:0 0 8px 8px;'>
            {rows_html}
        </div>
    </div>"""


# ── Marker icon ───────────────────────────────────────────────────────────────
def make_marker_color(samples: list) -> str:
    """Return folium color string based on sample results."""
    results  = [s.get('prediction_result', '') for s in samples]
    all_safe = all(r == 'Safe' for r in results)
    any_cont = any(r == 'Contaminated' for r in results)
    if all_safe:
        return 'green'
    elif any_cont:
        return 'red'
    return 'orange'


# ── Search section ────────────────────────────────────────────────────────────
def render_search_section():
    st.markdown("<div class='map-container'>", unsafe_allow_html=True)
    st.markdown("#### 🔍 Search Any Location")

    col_inp, col_btn = st.columns([4, 1])
    with col_inp:
        search_input = st.text_input(
            "Location", placeholder="Chennai, India",
            label_visibility="collapsed", key="map_search_input",
            help="City, Country — e.g. Chennai, India · Dubai, UAE"
        )
    with col_btn:
        clicked = st.button("🗺️ Show", use_container_width=True, key="map_search_btn")

    if clicked:
        raw = search_input.strip()
        if not raw:
            st.warning("⚠️ Please enter a location.")
            for k in ['search_lat', 'search_lon', 'search_address', 'search_label']:
                st.session_state.pop(k, None)
        else:
            with st.spinner(f"Locating '{raw}'..."):
                geo = cached_geocode(raw)
            if geo['success']:
                st.session_state.update({
                    'search_lat':       geo['latitude'],
                    'search_lon':       geo['longitude'],
                    'search_address':   geo['address'],
                    'search_label':     geo.get('used_input', raw),
                    'search_corrected': geo.get('corrected'),
                })
            else:
                for k in ['search_lat', 'search_lon', 'search_address', 'search_label']:
                    st.session_state.pop(k, None)
                st.error("❌ Location not found. Use format: **City, Country**")

    if all(k in st.session_state for k in ['search_lat', 'search_lon', 'search_label']):
        if st.session_state.get('search_corrected'):
            st.info(f"✏️ Auto-corrected to: **{st.session_state['search_label']}**")
        else:
            st.success(f"✅ {st.session_state['search_label']}")
        st.text(f"📍 {st.session_state['search_address']}")
        c1, c2 = st.columns(2)
        c1.metric("Latitude",  f"{st.session_state['search_lat']:.6f}")
        c2.metric("Longitude", f"{st.session_state['search_lon']:.6f}")

    st.markdown("</div>", unsafe_allow_html=True)


# ── Folium map ────────────────────────────────────────────────────────────────
def render_folium_map(location_groups: list):
    """One marker per unique location; popup lists all samples at that location."""
    if not location_groups:
        st.warning("⚠️ No locations to display.")
        return

    # Center: searched location or mean of all
    if all(k in st.session_state for k in ['search_lat', 'search_lon']):
        center = [st.session_state['search_lat'], st.session_state['search_lon']]
        zoom   = 12
    else:
        lats = [g['lat'] for g in location_groups]
        lons = [g['lon'] for g in location_groups]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
        zoom   = 5

    m = folium.Map(location=center, zoom_start=zoom, tiles='CartoDB positron')
    Fullscreen(position='topright').add_to(m)

    # Search pin
    if all(k in st.session_state for k in ['search_lat', 'search_lon', 'search_label']):
        folium.Marker(
            location=[st.session_state['search_lat'], st.session_state['search_lon']],
            popup=folium.Popup(
                f"<b>🔍 {st.session_state['search_label']}</b><br>"
                f"<small>{st.session_state.get('search_address','')}</small>",
                max_width=240
            ),
            tooltip=f"🔍 {st.session_state['search_label']}",
            icon=folium.Icon(color='blue', icon='star', prefix='fa')
        ).add_to(m)

    # One marker per location group
    for grp in location_groups:
        n       = len(grp['samples'])
        results = [s.get('prediction_result', '') for s in grp['samples']]
        all_safe = all(r == 'Safe' for r in results)
        any_cont = any(r == 'Contaminated' for r in results)
        status   = '✅ All Safe' if all_safe else ('🚫 Contaminated' if any_cont else '⚠️ Mixed')
        tooltip  = f"{status} · {grp['location_name']} · {n} sample{'s' if n > 1 else ''}"
        color    = make_marker_color(grp['samples'])
        icon_sym = 'check' if color == 'green' else ('times' if color == 'red' else 'exclamation')

        folium.Marker(
            location=[grp['lat'], grp['lon']],
            popup=folium.Popup(build_popup_html(grp), max_width=320),
            tooltip=tooltip,
            icon=folium.Icon(color=color, icon=icon_sym, prefix='fa')
        ).add_to(m)

    # Legend
    m.get_root().html.add_child(folium.Element("""
    <div style='position:fixed;bottom:30px;left:30px;z-index:1000;background:white;
                padding:14px 18px;border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,0.2);
                font-family:Arial;font-size:13px;'>
        <div style='font-weight:700;margin-bottom:8px;color:#1e293b;'>🗺️ Legend</div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>
            <div style='width:14px;height:14px;border-radius:50%;background:#2ca02c;'></div>
            <span>All Safe</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>
            <div style='width:14px;height:14px;border-radius:50%;background:#d62728;'></div>
            <span>Contaminated</span>
        </div>
        <div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;'>
            <div style='width:14px;height:14px;border-radius:50%;background:#ff7f0e;'></div>
            <span>Mixed Results</span>
        </div>
        <div style='font-size:11px;color:#6b7280;margin-top:6px;'>
            Click marker to see all samples
        </div>
    </div>"""))

    folium.TileLayer('OpenStreetMap', name='Street Map').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Mode').add_to(m)
    folium.LayerControl(position='topright').add_to(m)

    st_folium(m, width=None, height=600, use_container_width=True)
    total_samples = sum(len(g['samples']) for g in location_groups)
    st.caption(
        f"📍 {len(location_groups)} location(s) · {total_samples} total sample(s). "
        "Click any marker to see all samples at that location."
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

data = load_data()

st.markdown("""
    <div class='map-container'>
        <div style='font-size:32px;font-weight:700;color:#1e293b;'>🗺️ Water Quality Map</div>
        <div style='font-size:15px;color:#64748b;margin-top:6px;'>
            Grouped by location — click a marker to see all samples collected there
        </div>
    </div>
""", unsafe_allow_html=True)

if data.empty:
    st.info("📍 No water samples yet. Analyze a sample and save its location to see it here.")
    st.stop()

# ── Stats ─────────────────────────────────────────────────────────────────────
total_count        = len(data)
safe_count         = len(data[data['prediction_result'] == 'Safe'])
contaminated_count = len(data[data['prediction_result'] == 'Contaminated'])
safe_pct           = (safe_count / total_count * 100) if total_count > 0 else 0
valid_coords       = data.dropna(subset=['latitude', 'longitude'])
unique_locations   = valid_coords.groupby(
    [valid_coords['latitude'].round(4), valid_coords['longitude'].round(4)]
).ngroups

c1, c2, c3, c4, c5 = st.columns(5)
for col, val, label, grad in [
    (c1, total_count,        "Total Samples",     "#667eea,#764ba2"),
    (c2, unique_locations,   "📍 Locations",      "#3b82f6,#1d4ed8"),
    (c3, safe_count,         "✅ Safe",            "#10b981,#059669"),
    (c4, contaminated_count, "🚫 Contaminated",   "#ef4444,#dc2626"),
    (c5, f"{safe_pct:.1f}%", "Safe Rate",         "#f59e0b,#d97706"),
]:
    col.markdown(
        f"<div class='stats-card' style='background:linear-gradient(135deg,{grad});'>"
        f"<div style='font-size:28px;'>{val}</div>"
        f"<div style='font-size:12px;opacity:.9;'>{label}</div></div>",
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Search ────────────────────────────────────────────────────────────────────
render_search_section()
st.markdown("<br>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown("<div class='map-container'>", unsafe_allow_html=True)
st.markdown("#### 🔽 Filter")
cf1, cf2 = st.columns(2)
with cf1:
    filter_result = st.radio(
        "Show samples", ["All", "Safe only", "Contaminated only"], horizontal=True
    )
with cf2:
    st.caption("Each marker = one location. Badge shows sample count.")
st.markdown("</div>", unsafe_allow_html=True)

filtered = valid_coords.copy()
if filter_result == "Safe only":
    filtered = valid_coords[valid_coords['prediction_result'] == 'Safe']
elif filter_result == "Contaminated only":
    filtered = valid_coords[valid_coords['prediction_result'] == 'Contaminated']

# ── Map ───────────────────────────────────────────────────────────────────────
st.markdown("<div class='map-container'>", unsafe_allow_html=True)
st.markdown("#### 🗺️ Interactive Map")
if filtered.empty:
    st.warning("⚠️ No locations match the current filter.")
else:
    location_groups = group_by_location(filtered)
    render_folium_map(location_groups)
st.markdown("</div>", unsafe_allow_html=True)

# ── Location detail expanders ─────────────────────────────────────────────────
if not filtered.empty:
    st.markdown("<div class='map-container'>", unsafe_allow_html=True)
    st.markdown("#### 📋 Samples by Location")
    st.caption("Expand a location to see all samples collected there.")

    location_groups = group_by_location(filtered)
    for grp in location_groups:
        samples  = grp['samples']
        results  = [s.get('prediction_result', '') for s in samples]
        all_safe = all(r == 'Safe' for r in results)
        any_cont = any(r == 'Contaminated' for r in results)
        icon     = '✅' if all_safe else ('🚫' if any_cont else '⚠️')

        with st.expander(
            f"{icon} {grp['location_name']}  —  {len(samples)} sample(s)  "
            f"·  {grp['lat']:.4f}, {grp['lon']:.4f}"
        ):
            display_cols = [c for c in [
                'sample_id', 'timestamp', 'city_name', 'area_name',
                'water_source', 'prediction_result', 'confidence',
                'ph', 'hardness', 'tds', 'chlorine', 'sulfate',
                'conductivity', 'organic_carbon', 'trihalomethanes', 'turbidity'
            ] if c in pd.DataFrame(samples).columns]

            df_loc = pd.DataFrame(samples)[display_cols].sort_values(
                'timestamp', ascending=False
            ).reset_index(drop=True)

            st.dataframe(
                df_loc,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'sample_id':         st.column_config.TextColumn("Sample ID"),
                    'timestamp':         st.column_config.TextColumn("Timestamp"),
                    'city_name':         st.column_config.TextColumn("City"),
                    'area_name':         st.column_config.TextColumn("Area / Locality"),
                    'water_source':      st.column_config.TextColumn("Source"),
                    'prediction_result': st.column_config.TextColumn("Result"),
                    'confidence':        st.column_config.NumberColumn("Confidence", format="%.2f%%"),
                    'ph':                st.column_config.NumberColumn("pH",   format="%.2f"),
                    'tds':               st.column_config.NumberColumn("TDS",  format="%.2f"),
                    'chlorine':          st.column_config.NumberColumn("Cl",   format="%.2f"),
                    'turbidity':         st.column_config.NumberColumn("Turb", format="%.2f"),
                }
            )

    st.markdown("</div>", unsafe_allow_html=True)

# ── Full data table + download ────────────────────────────────────────────────
st.markdown("<div class='map-container'>", unsafe_allow_html=True)
st.markdown("#### 📥 All Records")

display_cols = [c for c in [
    'sample_id', 'timestamp', 'location_name', 'water_source',
    'prediction_result', 'confidence', 'latitude', 'longitude'
] if c in data.columns]

display_df = (
    data[display_cols].copy()
    .rename(columns={
        'sample_id': 'Sample ID', 'timestamp': 'Date & Time',
        'location_name': 'Location', 'water_source': 'Water Source',
        'prediction_result': 'Result', 'confidence': 'Confidence (%)',
        'latitude': 'Lat', 'longitude': 'Lon'
    })
    .sort_values('Date & Time', ascending=False)
    .reset_index(drop=True)
)

st.dataframe(display_df, use_container_width=True, hide_index=True, height=320,
    column_config={
        "Confidence (%)": st.column_config.NumberColumn(format="%.2f%%"),
        "Lat": st.column_config.NumberColumn(format="%.4f"),
        "Lon": st.column_config.NumberColumn(format="%.4f"),
    })

cd1, cd2 = st.columns([2, 1])
with cd1:
    st.download_button(
        "📥 Download CSV", data=display_df.to_csv(index=False),
        file_name=f"water_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv", use_container_width=True
    )
with cd2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

render_nav_bar("pages/5_\U0001f5fa\ufe0f_Map.py")
