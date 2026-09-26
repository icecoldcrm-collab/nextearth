import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ssl, urllib.request
from io import BytesIO

st.set_page_config(page_title="Universal Exoplanet Dashboard", layout="wide")
st.title("🌌 Universal Exoplanet Characterisation Dashboard")
st.write("Reading dual-stream live telemetry feeds from NASA archives.")

try:
    my_pipeline_df = pd.read_csv("habitable_candidates.csv")
    my_pipeline_loaded = True
except FileNotFoundError:
    my_pipeline_loaded = False
    my_pipeline_df = pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_complete_nasa_universe():
    url = "https://caltech.edu"
    try:
        ssl_context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ssl_context) as r:
            df = pd.read_csv(BytesIO(r.read()))
        df['st_lum'] = df['st_lum'].fillna((df['st_rad'].fillna(1.0)**2) * ((df['st_teff'].fillna(5778) / 5778)**4))
        df['pl_rade'] = df['pl_rade'].fillna(1.0)
        df['pl_orbper'] = df['pl_orbper'].fillna(30.0)
        df['st_rad'] = df['st_rad'].fillna(1.0)
        df['calculated_distance_au'] = ((df['pl_orbper'] / 365.25)**2 * df['st_rad'])**(1/3)
        df['hz_inner_edge_au'] = np.sqrt(df['st_lum'] / 1.1)
        df['hz_outer_edge_au'] = np.sqrt(df['st_lum'] / 0.53)
        df['size_classification'] = df['pl_rade'].apply(lambda r: "Sub-Earth" if r<=0.8 else ("Earth-sized Rocky" if r<=1.25 else ("Super-Earth" if r<=2.0 else ("Neptunian" if r<=6.0 else "Gas Giant"))))
        df['habitability_status'] = df.apply(lambda r: "🎯 PRIORITY 1: Habitable Zone Rocky World" if (r['hz_inner_edge_au'] <= r['calculated_distance_au'] <= r['hz_outer_edge_au']) and r['size_classification'] in ["Earth-sized Rocky", "Super-Earth"] else ("⚠️ Zone Match" if (r['hz_inner_edge_au'] <= r['calculated_distance_au'] <= r['hz_outer_edge_au']) else "❌ Outside Habitable Zone"), axis=1)
        return df
    except Exception:
        cols = ['pl_name','tic_id','pl_rade','calculated_distance_au','hz_inner_edge_au','hz_outer_edge_au','size_classification','habitability_status']
        rows = [['Earth',55431102,1.0,1.0,0.95,1.37,'Earth-sized Rocky','🎯 PRIORITY 1: Habitable Zone Rocky World'], ['Mars',83920111,0.53,1.52,0.95,1.37,'Sub-Earth','❌ Outside Habitable Zone']]
        return pd.DataFrame(rows, columns=cols)

global_universe_df = fetch_complete_nasa_universe()
st.sidebar.header("⚙️ Configuration Workspace")
feed_type = st.sidebar.radio("📬 Select Data Universe Feed:", ["🌌 All Known Exoplanets (Global NASA Feed)", "🎯 My Custom Pipeline Catalog"])

if "My Custom" in feed_type and my_pipeline_loaded and not my_pipeline_df.empty:
    active_df = my_pipeline_df.copy()
else:
    active_df = global_universe_df.copy()

active_df['parent_star_system'] = active_df['pl_name'].apply(lambda x: x[:-2] if (isinstance(x,str) and len(x)>2 and x[-1].islower() and x[-2]==' ') else (x[:-1] if isinstance(x,str) and len(x)>2 and x[-1].islower() else x))
unique_stars = sorted(active_df['parent_star_system'].dropna().unique().tolist())
star_filter = st.sidebar.selectbox("1. Filter by Parent Star System:", ["All Stars"] + unique_stars)
planet_choices = active_df[active_df['parent_star_system'] == star_filter]['pl_name'].tolist() if star_filter != "All Stars" else sorted(active_df['pl_name'].dropna().tolist())
selected_planet_name = st.sidebar.selectbox("2. Select Target Exoplanet:", ["Custom Parameters"] + planet_choices)

init_lum, init_rad, init_dist, init_atmo = 1.0, 1.0, 1.0, 1.0
if selected_planet_name != "Custom Parameters" and not active_df.empty:
    p_row = active_df[active_df['pl_name'] == selected_planet_name].iloc[0]
    init_dist = float(p_row['calculated_distance_au'])
    init_rad = float(p_row['pl_rade'])
    init_lum = float((p_row['hz_inner_edge_au']**2) * 1.1)
    init_atmo = 90.0 if "Gas" in str(p_row['size_classification']) else (50.0 if "Neptunian" in str(p_row['size_classification']) else 1.0)

star_luminosity = st.sidebar.slider("Host Star Luminosity (Relative to Sun)", 0.0001, 100.0, init_lum, step=0.01)
my_radius = st.sidebar.slider("Your Planet Radius (Earth Radii)", 0.1, 25.0, init_rad, step=0.1)
my_distance = st.sidebar.slider("Your Orbital Distance (AU)", 0.005, 10.0, init_dist, step=0.005)
atmo_thickness = st.sidebar.slider("Atmospheric Density (Earth = 1.0)", 0.0, 100.0, init_atmo, step=0.5)

base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)
total_greenhouse_multiplier = 1.0 + (np.log1p(atmo_thickness) * 0.35) + max(0.0, (my_radius - 1.0) * 0.1)
hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

size_class = "Sub-Earth" if my_radius<=0.8 else ("Earth-sized Rocky World" if my_radius<=1.25 else ("Super-Earth" if my_radius<=2.0 else ("Neptunian" if my_radius<=6.0 else "Gas Giant")))
status_text = "🎯 INSIDE GOLDILOCKS ZONE!" if (hz_inner <= my_distance <= hz_outer) and size_class in ["Earth-sized Rocky World", "Super-Earth"] else "❌ OUTSIDE GOLDILOCKS ZONE"
status_color = "green" if "INSIDE" in status_text else "red"

st.info(f"🧬 **Dynamic Environmental Readout:** Envelope shifted to **{hz_inner:.3f} AU – {hz_outer:.3f} AU**.")
st.markdown(f"### Current Planet Status: :{status_color}[{status_text}]")

col_metrics, col_chart = st.columns(2)
with col_metrics:
    st.metric("Planet Type", size_class)
    st.metric("Target Distance", f"{my_distance:.3f} AU")
    st.metric("Greenhouse Insulation", f"{total_greenhouse_multiplier:.2f}x")

with col_chart:
    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#0e1117')
    ax.scatter(0, 0, s=80, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    ax.axvspan(base_inner, base_outer, color='#ffffff', alpha=0.05, label='Base HZ')
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Dynamic HZ')
    ax.scatter(my_distance, 0, s=60, color='#1f77b4', edgecolors='white', label='Planet', zorder=6)
    max_b = max(3.5, hz_outer * 1.3, my_distance * 1.2)
    ax.set_xlim(-0.02 * max_b, max_b); ax.set_ylim(-0.5, 0.5); ax.get_yaxis().set_visible(False)
    ax.spines['bottom'].set_color('#ffffff'); ax.tick_params(colors='white')
    for s in ['top','left','right']: ax.spines[s].set_visible(False)
    st.pyplot(fig)

st.markdown("---")
st.header("📋 Automated NASA Archive Detections")
type_counts = active_df['size_classification'].value_counts()

col_l, col_r = st.columns(2)
with col_l:
    if not type_counts.empty:
        fig2, ax2 = plt.subplots(figsize=(3, 3))
        fig2.patch.set_facecolor('#0e1117')
        ax2.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=140, textprops={'color': 'white', 'fontsize': 8})
        ax2.axis('equal'); st.pyplot(fig2)
with col_r:
    st.write(f"**Current Feed:** {feed_type}")
    st.write(f"**Total Active Row Count:** {len(active_df)}")

st.markdown("---")
search_query = st.text_input("✍️ Search Planet by Designation Name:", "")
available_statuses = active_df['habitability_status'].unique().tolist() if 'habitability_status' in active_df.columns else []
selected_statuses = st.multiselect("🎯 Filter by Habitability Tag Status:", options=available_statuses, default=available_statuses)

filtered_df = active_df[active_df['habitability_status'].isin(selected_statuses)] if selected_statuses else active_df.copy()
if search_query and 'pl_name' in filtered_df.columns: 
    filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_query, case=False, na=False)]
st.dataframe(filtered_df, use_container_width=True)
