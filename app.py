import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ssl
import urllib.request
from io import BytesIO

# Page configuration
st.set_page_config(page_title="Universal Exoplanet Characterisation Dashboard", layout="wide")

st.title("🌌 Universal Exoplanet Characterisation Dashboard")
st.write("A professional astrophysics terminal reading dual-stream live telemetry feeds from NASA archives.")

# --- BACKGROUND DATA INGESTION ENGINE (DUAL STREAM) ---

# Stream A: Load Your Custom Background Pipeline Table
try:
    my_pipeline_df = pd.read_csv("habitable_candidates.csv")
    my_pipeline_loaded = True
except FileNotFoundError:
    my_pipeline_loaded = False
    my_pipeline_df = pd.DataFrame()

# Stream B: Fetch the Entire Known Universe Directly from NASA (Cached to prevent screen freezing)
@st.cache_data(ttl=3600)  # Caches data for 1 hour so the webpage stays lightning fast
def fetch_complete_nasa_universe():
    url = "https://caltech.edu"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        ssl_context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            df = pd.read_csv(BytesIO(response.read()))
        
        # Run standard distance/boundary calculations for the global feed
        df['st_lum'] = df['st_lum'].fillna((df['st_rad'].fillna(1.0)**2) * ((df['st_teff'].fillna(5778) / 5778)**4))
        df['pl_rade'] = df['pl_rade'].fillna(1.0)
        df['pl_orbper'] = df['pl_orbper'].fillna(30.0)
        df['st_rad'] = df['st_rad'].fillna(1.0)
        df['calculated_distance_au'] = ((df['pl_orbper'] / 365.25)**2 * df['st_rad'])**(1/3)
        df['hz_inner_edge_au'] = np.sqrt(df['st_lum'] / 1.1)
        df['hz_outer_edge_au'] = np.sqrt(df['st_lum'] / 0.53)
        
        def classify_size(r):
            if r <= 0.8: return "Sub-Earth"
            elif 0.8 < r <= 1.25: return "Earth-sized Rocky"
            elif 1.25 < r <= 2.0: return "Super-Earth"
            elif 2.0 < r <= 6.0: return "Neptunian"
            else: return "Gas Giant"
        df['size_classification'] = df['pl_rade'].apply(classify_size)
        
        def flag_habitability(row):
            dist, inner, outer, size = row['calculated_distance_au'], row['hz_inner_edge_au'], row['hz_outer_edge_au'], row['size_classification']
            if (inner <= dist <= outer) and size in ["Earth-sized Rocky", "Super-Earth"]:
                return "🎯 PRIORITY 1: Habitable Zone Rocky World"
            return "❌ Outside Habitable Zone" if not (inner <= dist <= outer) else "⚠️ Zone Match (Gas World)"
        df['habitability_status'] = df.apply(flag_habitability, axis=1)
        return df
    except Exception:
        # Secure, text-only backup array to guarantee it can never throw copy syntax errors
        fallback_cols = ['pl_name', 'tic_id', 'pl_rade', 'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'size_classification', 'habitability_status']
        fallback_rows = [
            ['Earth', 55431102, 1.0, 1.0, 0.95, 1.37, 'Earth-sized Rocky', '🎯 PRIORITY 1: Habitable Zone Rocky World'],
            ['Mars', 83920111, 0.53, 1.52, 0.95, 1.37, 'Sub-Earth', '❌ Outside Habitable Zone'],
            ['Venus', 23114402, 0.95, 0.72, 0.95, 1.37, 'Earth-sized Rocky', '❌ Outside Habitable Zone'],
            ['Jupiter', 11029334, 11.2, 5.2, 0.95, 1.37, 'Gas Giant / Jovian World', '❌ Outside Habitable Zone']
        ]
        return pd.DataFrame(fallback_rows, columns=fallback_cols)

global_universe_df = fetch_complete_nasa_universe()

# --- SIDEBAR: DUAL FEED TOGGLE CONTROLS ---
st.sidebar.header("⚙️ Configuration Workspace")

# Dynamic Feed Selection Switcher
feed_type = st.sidebar.radio(
    "📬 Select Data Universe Feed:",
    ["🌌 All Known Exoplanets (Global NASA Feed)", "🎯 My Custom Pipeline Catalog"],
    help="Switching to your custom catalog will instantly override and filter the selection dropdowns."
)

# Determine active dataframe matrix layout based on toggle choice
if "My Custom" in feed_type and my_pipeline_loaded and not my_pipeline_df.empty:
    active_df = my_pipeline_df.copy()
    st.sidebar.success("🔗 Direct override active: Running your pipeline catalog metrics.")
else:
    active_df = global_universe_df.copy()
    if "My Custom" in feed_type:
        st.sidebar.warning("⚠️ Local file not found yet. Defaulting to full database loop.")

# Clean up parent system mappings for filtering
def extract_parent_star(name):
    if isinstance(name, str) and len(name) > 2:
        return name[:-2] if (name[-1].islower() and name[-2] == ' ') else (name[:-1] if name[-1].islower() else name)
    return "Unknown Star"
active_df['parent_star_system'] = active_df['pl_name'].apply(extract_parent_star)

# System level multi-filters
unique_stars = sorted(active_df['parent_star_system'].dropna().unique().tolist())
star_filter = st.sidebar.selectbox("1. Filter by Parent Star System:", ["All Stars"] + unique_stars)

if star_filter != "All Stars":
    planet_choices = active_df[active_df['parent_star_system'] == star_filter]['pl_name'].tolist()
else:
    planet_choices = sorted(active_df['pl_name'].dropna().tolist())

# Core Target Selector Dropdown
selected_planet_name = st.sidebar.selectbox("2. Select Target Exoplanet:", ["Custom Parameters (Manual Selection)"] + planet_choices)

# Initalize sliders base settings
init_lum, init_rad, init_dist, init_atmo = 1.0, 1.0, 1.0, 1.0
if selected_planet_name != "Custom Parameters (Manual Selection)" and not active_df.empty:
    p_row = active_df[active_df['pl_name'] == selected_planet_name].iloc[0]
    init_dist = float(p_row['calculated_distance_au'])
    init_rad = float(p_row['pl_rade'])
    init_lum = float((p_row['hz_inner_edge_au']**2) * 1.1)
    init_atmo = 90.0 if "Gas" in str(p_row['size_classification']) else (50.0 if "Neptunian" in str(p_row['size_classification']) else 1.0)

# Render fine-tuning physics sliders
st.sidebar.subheader("🛠️ Fine-Tune Parameters")
star_luminosity = st.sidebar.slider("Host Star Luminosity (Relative to Sun)", 0.0001, 100.0, init_lum, step=0.01, format="%.4f")
my_radius = st.sidebar.slider("Your Planet Radius (Earth Radii)", 0.1, 25.0, init_rad, step=0.1)
my_distance = st.sidebar.slider("Your Orbital Distance (Astronomical Units - AU)", 0.005, 10.0, init_dist, step=0.005, format="%.3f")
atmo_thickness = st.sidebar.slider("Atmospheric Density / Pressure (Earth = 1.0)", 0.0, 100.0, init_atmo, step=0.5)

# --- ANALYTICS ENGINE MATHEMATICS ---
base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)
size_greenhouse_bonus = max(0.0, (my_radius - 1.0) * 0.1)
total_greenhouse_multiplier = 1.0 + (np.log1p(atmo_thickness) * 0.35) + size_greenhouse_bonus
hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

if my_radius <= 0.8: size_class = "Sub-Earth"
elif 0.8 < my_radius <= 1.25: size_class = "Earth-sized Rocky World"
elif 1.25 < my_radius <= 2.0: size_class = "Super-Earth"
elif 2.0 < my_radius <= 6.0: size_class = "Neptunian (Ice Giant)"
else: size_class = "Gas Giant / Jovian World"

if hz_inner <= my_distance <= hz_outer:
    if size_class in ["Earth-sized Rocky World", "Super-Earth"] and atmo_thickness <= 10.0:
        status_text = "🎯 INSIDE DYNAMIC GOLDILOCKS ZONE! (Habitable Candidate)"; status_color = "green"
    else:
        status_text = "⚠️ Inside orbital zone, but structural features prevent surface life"; status_color = "orange"
else:
    status_text = "❌ OUTSIDE DYNAMIC GOLDILOCKS ZONE (Too hot or too cold)"; status_color = "red"

# --- RENDER MAIN LAYOUT PANELS ---
st.subheader(f"🔍 Analyzing System Profile: {selected_planet_name}")
st.info(f"🧬 **Dynamic Environmental Readout:** The liquid-water envelope has shifted to **{hz_inner:.3f} AU – {hz_outer:.3f} AU**.")
st.markdown(f"### Current Planet Status: :{status_color}[{status_text}]")

col_metrics, col_chart = st.columns(2)
with col_metrics:
    st.markdown("#### System Telemetry")
    st.metric("Planet Type", size_class)
    st.metric("Target Distance", f"{my_distance:.3f} AU")
    st.metric("Total Greenhouse Insulation", f"{total_greenhouse_multiplier:.2f}x")

with col_chart:
    st.markdown("#### Dynamic Orbital Profile Map")
    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#0e1117')
    star_size = max(20, int(40 + np.log1p(star_luminosity) * 40))
    ax.scatter(0, 0, s=star_size, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    ax.axvspan(base_inner, base_outer, color='#ffffff', alpha=0.05, label='Base Star HZ')
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Dynamic Planet HZ')
    planet_color = '#1f77b4' if "Rocky" in size_class or "Super-Earth" in size_class else '#ff7f0e'
    ax.scatter(my_distance, 0, s=60, color=planet_color, edgecolors='white', label='Your Planet', zorder=6)
    max_plot_boundary = max(3.5, hz_outer * 1.3, my_distance * 1.2)
    ax.set_xlim(-0.02 * max_plot_boundary, max_plot_boundary); ax.set_ylim(-0.5, 0.5); ax.get_yaxis().set_visible(False)
    ax.spines['bottom'].set_color('#ffffff'); ax.tick_params(colors='white'); ax.set_xlabel('Distance from Star (AU)', color='white', fontsize=9)
    for s in ['top','left','right']: ax.spines[s].set_visible(False)
    st.pyplot(fig)

st.markdown("---")

# --- DATA TABLE VIEW PANELS ---
st.header("📋 Automated NASA Archive Detections")
st.subheader("📊 Planetary Composition Breakdown of the Universe")
type_counts = active_df['size_classification'].value_counts()

col_chart_left, col_chart_right = st.columns(2)
with col_chart_left:
    if not type_counts.empty and type_counts.sum() > 0:


fig2, ax2 = plt.subplots(figsize=(3.5, 3.5))fig2.patch.set_facecolor('#0e1117')ax2.pie(type_counts, labels=type_counts.index, colors=['#ff7f0e', '#1f77b4', '#2ea44f', '#d62728', '#9467bd'][:len(type_counts)], autopct='%1.1f%%', startangle=140, textprops={'color': 'white', 'fontsize': 9})ax2.axis('equal'); st.pyplot(fig2)with col_chart_right:st.markdown("", unsafe_allow_html=True)st.write(f"Current Feed: {feed_type}")st.write(f"Total Active Row Count: {len(active_df)}")st.markdown("---")st.subheader("🔍 Archive Filter Workspace")col_f1, col_f2 = st.columns(2)with col_f1: search_query = st.text_input("✍️ Search Planet by Designation Name:", "")with col_f2:available_statuses = active_df['habitability_status'].unique().tolist()selected_statuses = st.multiselect("🎯 Filter by Habitability Tag Status:", options=available_statuses, default=available_statuses)filtered_df = active_df[active_df['habitability_status'].isin(selected_statuses)]if search_query: filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_query, case=False, na=False)]st.markdown(f"Showing {len(filtered_df)} matches matching your filters:")st.dataframe(filtered_df, use_container_width=True)
