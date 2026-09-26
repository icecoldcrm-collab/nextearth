import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Dynamic Exoplanet Characterisation Engine", layout="wide")

st.title("🌌 Dynamic Exoplanet Characterisation Engine")
st.write("An advanced analytical workspace mapped to live data arrays from the NASA Exoplanet Archive.")

# --- LOAD DATA ENGINE ---
try:
    df = pd.read_csv("habitable_candidates.csv")
    
    # Clean and split string data to find parent star name stems
    # Usually the star name is the planet name minus the last lowercase letter (e.g. 'Kepler-22b' -> 'Kepler-22')
    def get_parent_star(name):
        if isinstance(name, str) and len(name) > 2:
            if name[-1].islower() and name[-2] == ' ':
                return name[:-2]
            elif name[-1].islower() and name[-2] != ' ':
                return name[:-1]
        return "Unknown Star"

    df['parent_star_system'] = df['pl_name'].apply(get_parent_star)
    data_loaded = True
except FileNotFoundError:
    data_loaded = False
    df = pd.DataFrame(columns=['pl_name', 'tic_id', 'pl_rade', 'size_classification', 'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status'])

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("⚙️ Configuration Workspace")

# Default values if no planet is selected
init_lum, init_rad, init_dist, init_atmo = 1.0, 1.0, 1.0, 1.0
selected_planet_name = "Custom System"

if data_loaded and not df.empty:
    st.sidebar.subheader("🛸 Live Target Selector")
    
    # Feature 2: Parent Star Filter System
    unique_stars = sorted(df['parent_star_system'].dropna().unique().tolist())
    star_filter = st.sidebar.selectbox("1. Filter by Parent Star System:", ["All Stars"] + unique_stars)
    
    # Filter planet choices based on selected star
    if star_filter != "All Stars":
        planet_choices = df[df['parent_star_system'] == star_filter]['pl_name'].tolist()
    else:
        planet_choices = sorted(df['pl_name'].dropna().tolist())
        
    # Feature 1: Universal Planet Selection Dropdown
    selected_planet_name = st.sidebar.selectbox("2. Select Target Exoplanet:", ["Custom Parameters (Manual)"] + planet_choices)
    
    # If a real planet is picked, extract its exact physics profiles
    if selected_planet_name != "Custom Parameters (Manual)":
        p_row = df[df['pl_name'] == selected_planet_name].iloc[0]
        
        # Calculate dynamic luminosity estimate from its recorded boundaries
        init_dist = float(p_row['calculated_distance_au'])
        init_rad = float(p_row['pl_rade'])
        
        # Reconstruct stellar luminosity proxy based on internal boundary footprints
        init_lum = float((p_row['hz_inner_edge_au']**2) * 1.1)
        
        # Approximate atmosphere proxies based on size rules
        if "Gas" in str(p_row['size_classification']):
            init_atmo = 90.0
        elif "Neptunian" in str(p_row['size_classification']):
            init_atmo = 50.0
        elif "Venus" in str(p_row['pl_name']).lower():
            init_atmo = 92.0
        else:
            init_atmo = 1.0

# --- SLIDER MODULE ---
st.sidebar.subheader("🛠️ Fine-Tune Parameters")
star_luminosity = st.sidebar.slider("Host Star Luminosity (Relative to Sun)", 0.0001, 100.0, init_lum, step=0.01, format="%.4f")
my_radius = st.sidebar.slider("Your Planet Radius (Earth Radii)", 0.1, 25.0, init_rad, step=0.1)
my_distance = st.sidebar.slider("Your Orbital Distance (Astronomical Units - AU)", 0.005, 10.0, init_dist, step=0.005, format="%.3f")
atmo_thickness = st.sidebar.slider("Atmospheric Density / Pressure (Earth = 1.0)", 0.0, 100.0, init_atmo, step=0.5)

# --- PHYSICS ALGORITHMS ---
base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)

size_greenhouse_bonus = max(0.0, (my_radius - 1.0) * 0.1)
total_greenhouse_multiplier = 1.0 + (np.log1p(atmo_thickness) * 0.35) + size_greenhouse_bonus

hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

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

if hz_inner <= my_distance <= hz_outer:
    if size_class in ["Earth-sized Rocky World", "Super-Earth"] and atmo_thickness <= 10.0:
        status_text = "🎯 INSIDE DYNAMIC GOLDILOCKS ZONE! (Habitable Candidate)"
        status_color = "green"
    elif atmo_thickness > 10.0:
        status_text = "⚠️ Inside orbital zone, but greenhouse runaway has boiled the surface"
        status_color = "orange"
    else:
        status_text = "⚠️ Inside orbital zone, but planet lacks a solid surface"
        status_color = "orange"
else:
    status_text = "❌ OUTSIDE DYNAMIC GOLDILOCKS ZONE (Too hot or too cold)"
    status_color = "red"

# --- DISPLAY UI WORKSPACE ---
st.subheader(f"🔍 Analyzing System Profile: {selected_planet_name}")
st.info(f"🧬 **Dynamic Environmental Readout:** The liquid-water envelope has shifted to **{hz_inner:.3f} AU – {hz_outer:.3f} AU** (Base Stellar Star-Only Zone was {base_inner:.2f} – {base_outer:.2f} AU).")
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
    
    star_size = max(20, int(40 + np.log1p(star_luminosity) * 40))
    ax.scatter(0, 0, s=star_size, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    
    ax.axvspan(base_inner, base_outer, color='#ffffff', alpha=0.05, label='Base Star HZ')
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Dynamic Planet HZ')
    
    planet_color = '#1f77b4' if "Rocky" in size_class or "Super-Earth" in size_class else '#ff7f0e'
    ax.scatter(my_distance, 0, s=60, color=planet_color, edgecolors='white', label='Your Planet', zorder=6)
    
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
if data_loaded:
    st.subheader("📊 Planetary Composition Breakdown of the Universe")
    type_counts = df['size_classification'].value_counts()
    
    col_chart_left, col_chart_right = st.columns(2)
    with col_chart_left:
        if not type_counts.empty and type_counts.sum() > 0:
            fig2, ax2 = plt.subplots(figsize=(4, 4))
            fig2.patch.set_facecolor('#0e1117')
            colors = ['#ff7f0e', '#1f77b4', '#2ea44f', '#d62728', '#9467bd']
            ax2.pie(type_counts, labels=type_counts.index, colors=colors[:len(type_counts)], autopct='%1.1f%%', startangle=140, textprops={'color': 'white', 'fontsize': 10})
            ax2.axis('equal')  
            st.pyplot(fig2)
            
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
        available_statuses = df['habitability_status'].unique().tolist()
        selected_statuses = st.multiselect("🎯 Filter by Habitability Tag Status:", options=available_statuses, default=available_statuses)
        
    filtered_df = df[df['habitability_status'].isin(selected_statuses)]
    if search_query:
        filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_query, case=False, na=False)]
        
    st.markdown(f"**Showing {len(filtered_df)} matches matching your filters:**")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("📊 Processing background telemetry matrix... Verify your automated GitHub pipeline action execution loop has completed successfully.")
