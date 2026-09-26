import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Exoplanet Characterisation Dashboard", layout="wide")

st.title("🌌 Dynamic Exoplanet Characterisation Engine")
st.write("An advanced analytical workspace where both stellar energy and planetary physics determine habitability.")

# --- SECTION 1: DYNAMIC INPUT CONTROLS ---
st.sidebar.header("⚙️ System Parameters")

# Stellar Properties
st.sidebar.subheader("🌟 Star Properties")
star_luminosity = st.sidebar.slider("Host Star Luminosity (Relative to Sun)", 0.01, 10.0, 1.0, step=0.1)

# Planetary Properties
st.sidebar.subheader("🪐 Planet Properties")
my_radius = st.sidebar.slider("Your Planet Radius (Earth Radii)", 0.1, 5.0, 1.0, step=0.1)
my_distance = st.sidebar.slider("Your Orbital Distance (Astronomical Units - AU)", 0.01, 3.0, 1.52, step=0.01)

# Atmosphere Greenhouse Multiplier Slider
st.sidebar.subheader("💨 Atmosphere Properties")
atmo_thickness = st.sidebar.slider(
    "Atmospheric Density Multiplier", 
    0.0, 5.0, 1.0, step=0.1,
    help="0.0 = No Atmosphere (Mars/Moon), 1.0 = Earth Equivalent, >2.0 = Heavy Super-Earth Greenhouse Blanket"
)

# --- SECTION 2: DYNAMIC HABITABLE ZONE CALCULATOR ---

# Base stellar boundaries (Standard Earth model)
base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)

# DYNAMIC MODIFIERS: How the planet alters its own survival boundaries
# 1. Size Factor: Larger planets (Super-Earths) hold more gas and volcanic heat
size_greenhouse_bonus = max(0.0, (my_radius - 1.0) * 0.15)

# 2. Total Atmosphere Greenhouse Effect
total_greenhouse_multiplier = 1.0 + (atmo_thickness * 0.2) + size_greenhouse_bonus

# Apply the dynamic extensions to the outer boundary
hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

# Categorise planetary size
if my_radius <= 0.8:
    size_class = "Sub-Earth"
elif 0.8 < my_radius <= 1.25:
    size_class = "Earth-sized Rocky World"
elif 1.25 < my_radius <= 2.0:
    size_class = "Super-Earth"
else:
    size_class = "Gas/Ice Giant"

# Evaluate Custom Habitability Status
if hz_inner <= my_distance <= hz_outer:
    if size_class in ["Earth-sized Rocky World", "Super-Earth"]:
        status_text = "🎯 INSIDE DYNAMIC GOLDILOCKS ZONE! (Habitable Candidate)"
        status_color = "green"
    else:
        status_text = "⚠️ Inside Zone, but planet is a gas giant (Not habitable)"
        status_color = "orange"
else:
    status_text = "❌ OUTSIDE DYNAMIC GOLDILOCKS ZONE (Too hot or too cold)"
    status_color = "red"

# --- SECTION 3: RENDER THE DASHBOARD INTERFACE ---

st.info(f"🧬 **Dynamic Environmental Readout:** Due to this planet's physical properties, its specific liquid-water envelope has shifted to **{hz_inner:.2f} AU – {hz_outer:.2f} AU** (Base Stellar Zone was {base_inner:.2f} – {base_outer:.2f} AU).")
st.markdown(f"### Current Planet Status: :{status_color}[{status_text}]")

col_metrics, col_chart = st.columns()

with col_metrics:
    st.markdown("#### System Telemetry")
    st.metric("Planet Type", size_class)
    st.metric("Target Distance", f"{my_distance:.2f} AU")
    st.metric("Total Greenhouse Insulation", f"{total_greenhouse_multiplier:.2f}x")

with col_chart:
    st.markdown("#### Dynamic Orbital Profile Map")
    
    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor('#0e1117') 
    ax.set_facecolor('#0e1117')
    
    # Host Star (0,0)
    star_size = 100 + (star_luminosity * 20)
    ax.scatter(0, 0, s=star_size, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    
    # Base Stellar Zone (Light grey line marker background)
    ax.axvspan(base_inner, base_outer, color='#ffffff', alpha=0.08, label='Base Star HZ')
    
    # Dynamic Habitable Zone (Green shaded region)
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Dynamic Planet HZ')
    
    # Target Planet Position
    planet_color = '#1f77b4' if size_class != "Gas/Ice Giant" else '#ff7f0e'
    ax.scatter(my_distance, 0, s=60, color=planet_color, edgecolors='white', label='Your Planet', zorder=6)
    
    # Formatting
    ax.set_xlim(-0.1, 3.5)
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

# --- SECTION 4: BACKGROUND TELESCOPE PIPELINE DATA ---
st.header("📋 Automated NASA Archive Detections")
try:
    df = pd.read_csv("habitable_candidates.csv")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.info("📊 Processing background telemetry matrix... Verify your automated GitHub pipeline action execution loop.")
