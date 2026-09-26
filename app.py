import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page configuration
st.set_page_config(page_title="Exoplanet Characterisation Dashboard", layout="wide")

st.title("🌌 Exoplanet Characterisation & Discovery Engine")
st.write("An automated analytical pipeline classifying live space telescope data for habitable candidate detection.")

# --- SECTION 1: CUSTOM PLANET POSITION CYCLER (SIMULATOR) ---
st.header("🪐 Orbit Position & Boundary Cycler")
st.write("Slide through the parameters below to position your own planet and see where it falls compared to the automated pipeline's metrics.")

# Columns for interactive planet inputs
col_input1, col_input2, col_input3 = st.columns(3)

with col_input1:
    my_radius = st.slider("Your Planet Radius (Earth Radii)", 0.1, 5.0, 1.0, step=0.1)
with col_input2:
    my_distance = st.slider("Your Orbital Distance (Astronomical Units - AU)", 0.01, 3.0, 1.0, step=0.01)
with col_input3:
    star_luminosity = st.slider("Host Star Luminosity (Relative to Sun)", 0.01, 10.0, 1.0, step=0.1)

# Dynamic physics boundaries calculation based on your inputs
hz_inner = np.sqrt(star_luminosity / 1.1)
hz_outer = np.sqrt(star_luminosity / 0.53)

# Categorise size
if my_radius <= 0.8:
    size_class = "Sub-Earth"
elif 0.8 < my_radius <= 1.25:
    size_class = "Earth-sized Rocky World"
elif 1.25 < my_radius <= 2.0:
    size_class = "Super-Earth"
else:
    size_class = "Gas/Ice Giant"

# Evaluate Habitability status
if hz_inner <= my_distance <= hz_outer:
    if size_class in ["Earth-sized Rocky World", "Super-Earth"]:
        status_text = "🎯 INSIDE GOLDILOCKS ZONE! (Habitable Candidate)"
        status_color = "green"
    else:
        status_text = "⚠️ Inside Zone, but planet is a gas giant (Not habitable)"
        status_color = "orange"
else:
    status_text = "❌ OUTSIDE GOLDILOCKS ZONE (Too hot or too cold)"
    status_color = "red"

# Render the dynamic feedback panel
st.info(f"**Boundary Readout:** For a star with {star_luminosity}x Sun's luminosity, the Habitable Zone sits between **{hz_inner:.2f} AU** and **{hz_outer:.2f} AU**.")
st.markdown(f"### Current Planet Status: :{status_color}[{status_text}]")

# Layout with Text metrics on the left, Visual chart on the right
col_metrics, col_chart = st.columns([1, 2])

with col_metrics:
    st.markdown("#### System Telemetry")
    st.metric("Planet Type", size_class)
    st.metric("Your Chosen Distance", f"{my_distance:.2f} AU")
    st.metric("Zone Placement", "Habitable" if (hz_inner <= my_distance <= hz_outer) else "Inhabitable")

with col_chart:
    st.markdown("#### Orbital Profile Map")
    
    # Generate the Matplotlib Visualisation
    fig, ax = plt.subplots(figsize=(6, 2.5))
    fig.patch.set_facecolor('#0e1117') # Match Streamlit dark background
    ax.set_facecolor('#0e1117')
    
    # Draw the Host Star at coordinate (0,0)
    # Star size scales slightly with luminosity input
    star_size = 100 + (star_luminosity * 20)
    ax.scatter(0, 0, s=star_size, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    
    # Draw the Habitable Zone boundary ring shaded region
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.3, label='Habitable Zone')
    
    # Plot your user-controlled planet position
    planet_color = '#1f77b4' if size_class != "Gas/Ice Giant" else '#ff7f0e'
    ax.scatter(my_distance, 0, s=60, color=planet_color, edgecolors='white', label='Your Planet', zorder=6)
    
    # Format the chart axis structure
    ax.set_xlim(-0.1, 3.2)
    ax.set_ylim(-0.5, 0.5)
    ax.get_yaxis().set_visible(False) # Hide y-axis since it's a 1D distance cross-section
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#ffffff')
    ax.tick_params(colors='white')
    ax.set_xlabel('Distance from Star (Astronomical Units - AU)', color='white', fontsize=9)
    ax.legend(loc='upper right', facecolor='#1e222b', edgecolor='none', labelcolor='white', fontsize=8)
    
    st.pyplot(fig)

st.markdown("---")

# --- SECTION 2: LIVE ARCHIVE DATA TABLE ---
st.header("📋 Automated NASA Archive Detections")
st.write("These are the high-priority habitable candidates successfully extracted from NASA telemetry via your automated background pipeline:")

try:
    df = pd.read_csv("habitable_candidates.csv")
    st.dataframe(df, use_container_width=True)
except FileNotFoundError:
    st.info("📊 Gathering live telemetry... Make sure to run your GitHub action to generate the `habitable_candidates.csv` database file!")
