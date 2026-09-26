import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Dynamic Exoplanet Characterisation Engine", layout="wide")

st.title("🌌 Dynamic Exoplanet Characterisation Engine")
st.write("An advanced analytical workspace calibrated to the true physical extremes of the explored universe.")

# --- SECTION 1: FAMOUS COSMIC ARCHETYPES PRESETS ---
st.sidebar.header("⚙️ Configuration Workspace")
st.sidebar.subheader("🚀 Quick-Select Archetypes")

preset_options = {
    "Custom Parameters (Manual Manual)": None,
    "Earth (The Baseline)": {"lum": 1.0, "rad": 1.0, "dist": 1.0, "atmo": 1.0},
    "Mars (Sub-Earth Reality)": {"lum": 1.0, "rad": 0.53, "dist": 1.52, "atmo": 0.0},
    "Venus (Blistering Greenhouse Extreme)": {"lum": 1.0, "rad": 0.95, "dist": 0.72, "atmo": 92.0},
    "TRAPPIST-1e (M-Dwarf Habitability)": {"lum": 0.0005, "rad": 0.92, "dist": 0.029, "atmo": 1.2},
    "Kepler-78b (Molten Lava USP World)": {"lum": 0.82, "rad": 1.2, "dist": 0.009, "atmo": 0.0},
    "Jupiter-Class Gas Giant (Massive Envelope)": {"lum": 1.0, "rad": 11.2, "dist": 5.2, "atmo": 500.0}
}

selected_preset = st.sidebar.selectbox("Choose a known planet configuration:", list(preset_options.keys()))
preset_data = preset_options[selected_preset]

# --- SECTION 2: SLIDERS CALIBRATED TO REAL ASTROPHYSICAL LIMITS ---
st.sidebar.subheader("🌟 Star Properties")
init_lum = preset_data["lum"] if preset_data else 1.0
star_luminosity = st.sidebar.slider(
    "Host Star Luminosity (Relative to Sun)", 
    0.0001, 100.0, init_lum, step=0.01, format="%.4f",
    help="Real Range: 0.00015x (Ultra-Cool M-Dwarfs) up to 100,000x+ (Massive Blue Supergiants)"
)

st.sidebar.subheader("🪐 Planet Properties")
init_rad = preset_data["rad"] if preset_data else 1.0
my_radius = st.sidebar.slider(
    "Your Planet Radius (Earth Radii)", 
    0.1, 25.0, init_rad, step=0.1,
    help="Real Range: 0.3x (Moon-sized chunks) up to 25.0x (Super-Jupiters / Brown Dwarf boundaries)"
)

init_dist = preset_data["dist"] if preset_data else 1.52
my_distance = st.sidebar.slider(
    "Your Orbital Distance (Astronomical Units - AU)", 
    0.005, 10.0, init_dist, step=0.005, format="%.3f",
    help="Real Range: 0.005 AU (Ultra-Short-Period lava worlds) up to thousands of AU in the dark"
)

st.sidebar.subheader("💨 Atmosphere Properties")
init_atmo = preset_data["atmo"] if preset_data else 1.0
atmo_thickness = st.sidebar.slider(
    "Atmospheric Density / Pressure (Earth = 1.0)", 
    0.0, 100.0, init_atmo, step=0.5,
    help="Real Range: 0.0 (Airless Mars/Moon), 1.0 (Earth), 92.0 (Venus surface crushing pressure), up to thousands on Gas Giants"
)

# --- SECTION 3: PHYSICS ALGORITHMS (CALIBRATED EXTREMES) ---
# Base stellar lines
base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)

# Logarithmic scaling for greenhouse effect to handle crushing thick atmospheres (like Venus/Gas Giants) without math explosion
size_greenhouse_bonus = max(0.0, (my_radius - 1.0) * 0.1)
total_greenhouse_multiplier = 1.0 + (np.log1p(atmo_thickness) * 0.35) + size_greenhouse_bonus

hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

# Classify size metrics extended up to Gas Giants
if my_radius <= 0.8:
    size_class = "Sub-Earth"
elif 0.8 < my_radius <= 1.25:
    size_class = "Earth-sized Rocky World"
elif 1.25 < my_radius <= 2.0:
    size_class = "Super-Earth"
elif 2.0 < my_radius <= 6.0:
    size_class = "Neptunian (Ice Giant)"
else:
    size_class = "Gas Giant / Jovian World"

# Evaluate Habitability status
if hz_inner <= my_distance <= hz_outer:
    if size_class in ["Earth-sized Rocky World", "Super-Earth"] and atmo_thickness <= 10.0:
        status_text = "🎯 INSIDE DYNAMIC GOLDILOCKS ZONE! (Habitable Candidate)"
        status_color = "green"
    elif atmo_thickness > 10.0:
        status_text = "⚠️ Inside orbital zone, but greenhouse runaway has boiled the surface (Venus-like Choke)"
        status_color = "orange"
    else:
        status_text = "⚠️ Inside orbital zone, but planet is a gas giant without a solid surface"
        status_color = "orange"
else:
    status_text = "❌ OUTSIDE DYNAMIC GOLDILOCKS ZONE (Too hot or too cold)"
    status_color = "red"

# --- SECTION 4: DISPLAY WORKSPACE ---
st.info(f"🧬 **Dynamic Environmental Readout:** Due to system parameters, the liquid-water envelope has shifted to **{hz_inner:.3f} AU – {hz_outer:.3f} AU** (Base Stellar Star-Only Zone was {base_inner:.3f} – {base_outer:.3f} AU).")
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
    fig.patch.set_facecolor('#0e1117') 
    ax.set_facecolor('#0e1117')
    
    # Host Star (0,0) - scales with luminosity logs
    star_size = max(20, int(40 + np.log1p(star_luminosity) * 40))
    ax.scatter(0, 0, s=star_size, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    
    # Shade structural zones
    ax.axvspan(base_inner, base_outer, color='#ffffff', alpha=0.05, label='Base Star HZ')
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Dynamic Planet HZ')
    
    # Plot target planet
    planet_color = '#1f77b4' if "Rocky" in size_class or "Super-Earth" in size_class else '#ff7f0e'
    ax.scatter(my_distance, 0, s=60, color=planet_color, edgecolors='white', label='Your Planet', zorder=6)
    
    # Logarithmic-style clipping layout for visual map mapping to handle tight ultra-short orbits vs wide ones smoothly
    max_plot_boundary = max(3.5, hz_outer * 1.3, my_distance * 1.2)
    ax.set_xlim(-0.02 * max_plot_boundary, max_plot_boundary)
    ax.set_ylim(-0.5, 0.5)
    ax.get_yaxis().set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#ffffff')
    ax.tick_params(colors='white')
    ax.set_xlabel('Distance from Star (Astronomical Units - AU)', color='white', fontsize=9)
    ax.legend(loc='upper right', facecolor='#1e222b', edgecolor='none', labelcolor='white', fontsize=8)
    st.pyplot(fig)

st.markdown("---")

# --- SECTION 5: LIVE NASA DATABASE VIEW ---
st.header("📋 Automated NASA Archive Detections")
try:
    df = pd.read_csv("habitable_candidates.csv")
    st.subheader("📊 Planetary Composition Breakdown of the Universe")
    type_counts = df['size_classification'].value_counts() if 'size_classification' in df.columns else pd.Series()
    
    col_chart_left, col_chart_right = st.columns(2)
    with col_chart_left:
        if not type_counts.empty and type_counts.sum() > 0:
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            fig2.patch.set_facecolor('#0e1117')
            colors = ['#ff7f0e', '#1f77b4', '#2ea44f', '#d62728', '#9467bd']
            ax2.pie(type_counts, labels=type_counts.index, colors=colors[:len(type_counts)], autopct='%1.1f%%', startangle=140, textprops={'color': 'white', 'fontsize': 10})
            ax2.axis('equal')  
            st.pyplot(fig2)
        else:
            st.info("📡 Calibrating statistical data engines... Run your GitHub Actions pipeline workflow to populate live analytics charts.")
            
    with col_chart_right:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.write("This dynamic breakdown illustrates the relative abundance of cosmic archetypes derived from telescope telemetry.")
        st.write(f"**Total Planets Currently Catalogued:** {len(df)}")
        
    st.markdown("---")
    st.subheader("🔍 Archive Filter Workspace")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        search_query = st.text_input("✍️ Search Planet by Designation Name (e.g., 'Kepler-186' or 'TOI-700'):", "")
    with col_f2:
        available_statuses = df['habitability_status'].unique().tolist() if 'habitability_status' in df.columns else []
        selected_statuses = st.multiselect("🎯 Filter by Habitability Tag Status:", options=available_statuses, default=available_statuses)
        
    if 'habitability_status' in df.columns and selected_statuses:
        filtered_df = df[df['habitability_status'].isin(selected_statuses)]
    else:
        filtered_df = df.copy()
        
    if search_query and 'pl_name' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_query, case=False, na=False)]
        
    st.markdown(f"**Showing {len(filtered_df)} matches matching your filters:**")
    st.dataframe(filtered_df, use_container_width=True)
    
except FileNotFoundError:
    st.info("📊 Processing background telemetry matrix... Verify your automated GitHub pipeline action execution loop has completed successfully.")
