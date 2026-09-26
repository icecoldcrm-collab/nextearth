import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Universal Exoplanet Dashboard", layout="wide")
st.title("🌌 Dual-Stream Exoplanet Characterisation Terminal")
st.write("Cross-analyzing confirmed stellar archives alongside custom transit graph discoveries.")

# --- DATA STREAM A: KNOWN PLANET REPOSITORY REFERENCE (EMBEDDED) ---
known_universe_data = [
    ['Earth', 1.0, 'Earth-sized Rocky', 1.0, 0.95, 1.37, '🎯 PRIORITY 1: Habitable Zone Rocky World', 'Our baseline system.'],
    ['Mars', 0.53, 'Sub-Earth', 1.52, 0.95, 1.37, '❌ Outside Habitable Zone', 'Frozen outer desert.'],
    ['Venus', 0.95, 'Earth-sized Rocky', 0.72, 0.95, 1.37, '❌ Outside Habitable Zone', 'Runaway greenhouse envelope.'],
    ['TRAPPIST-1 e', 0.92, 'Earth-sized Rocky', 0.029, 0.021, 0.030, '🎯 PRIORITY 1: Habitable Zone Rocky World', 'Confirmed M-Dwarf rocky priority.'],
    ['Kepler-22 b', 2.40, 'Gas Giant', 0.849, 0.847, 1.22, '⚠️ Zone Match (Gas World Configuration)', 'First Kepler habitable zone target.']
]
cols = ['pl_name', 'pl_rade', 'size_classification', 'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status', 'observer_notes']
global_archive_df = pd.DataFrame(known_universe_data, columns=cols)

# --- DATA STREAM B: YOUR CUSTOM PIPELINE ENGINE DISCOVERIES ---
try:
    my_discoveries_df = pd.read_csv("habitable_candidates.csv")
    my_pipeline_loaded = True
except FileNotFoundError:
    my_pipeline_loaded = False
    my_discoveries_df = pd.DataFrame()

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.header("📬 Data Universe Stream")
feed_selector = st.sidebar.radio(
    "Select Telemetry Source:",
    ["🌌 Confirmed Exoplanet Repository", "🎯 My Custom Transit Graph Discoveries"]
)

# Core workflow toggle override switch logic
if "My Custom" in feed_selector and my_pipeline_loaded and not my_discoveries_df.empty:
    active_df = my_discoveries_df.copy()
    st.sidebar.success("🔗 Now displaying targets processed by your transit discovery code!")
else:
    active_df = global_archive_df.copy()
    if "My Custom" in feed_selector:
        st.sidebar.warning("📊 Pipeline spreadsheet compiling... showing baseline references.")

# Dropdown Target Selector
planet_choices = sorted(active_df['pl_name'].dropna().tolist())
selected_planet = st.sidebar.selectbox("Select Target Planet for Profile Mapping:", ["Custom Parameters (Manual)"] + planet_choices)

# Fine-tuning slider hooks
init_lum, init_rad, init_dist = 1.0, 1.0, 1.0
if selected_planet != "Custom Parameters (Manual)" and not active_df.empty:
    p_row = active_df[active_df['pl_name'] == selected_planet].iloc[0]
    init_dist = float(p_row['calculated_distance_au'])
    init_rad = float(p_row['pl_rade'])
    init_lum = float((p_row['hz_inner_edge_au']**2) * 1.1)

st.sidebar.subheader("🛠️ Fine-Tune Parameters")
star_luminosity = st.sidebar.slider("Host Star Luminosity (Relative to Sun)", 0.0001, 10.0, init_lum, step=0.01)
my_radius = st.sidebar.slider("Your Planet Radius (Earth Radii)", 0.1, 25.0, init_rad, step=0.1)
my_distance = st.sidebar.slider("Your Orbital Distance (AU)", 0.005, 5.0, init_dist, step=0.005)

# --- RE-CALCULATING ENVIRONMENT PROFILE ---
base_inner = np.sqrt(star_luminosity / 1.1)
base_outer = np.sqrt(star_luminosity / 0.53)
hz_inner, hz_outer = base_inner, base_outer

size_class = "Sub-Earth" if my_radius<=0.8 else ("Earth-sized Rocky World" if my_radius<=1.25 else ("Super-Earth" if my_radius<=2.0 else "Gas Giant"))
status_text = "🎯 INSIDE GOLDILOCKS ZONE!" if (hz_inner <= my_distance <= hz_outer) and size_class in ["Earth-sized Rocky World", "Super-Earth"] else "❌ OUTSIDE GOLDILOCKS ZONE"
status_color = "green" if "INSIDE" in status_text else "red"

st.subheader(f"🔍 System Analysis: {selected_planet}")
st.markdown(f"### Current Planet Status: :{status_color}[{status_text}]")

col_metrics, col_chart = st.columns(2)
with col_metrics:
    st.metric("Planet Sizing Type", size_class)
    st.metric("Orbital Coordinates", f"{my_distance:.3f} AU")
    if selected_planet != "Custom Parameters (Manual)":
        st.caption(f"📝 **Discovery Log Notes:** {p_row['observer_notes']}")

with col_chart:
    fig, ax = plt.subplots(figsize=(6, 2.3))
    fig.patch.set_facecolor('#0e1117'); ax.set_facecolor('#0e1117')
    ax.scatter(0, 0, s=100, color='#f9d71c', edgecolors='#ffaa00', label='Host Star', zorder=5)
    ax.axvspan(hz_inner, hz_outer, color='#2ea44f', alpha=0.35, label='Goldilocks HZ')
    ax.scatter(my_distance, 0, s=60, color='#1f77b4', edgecolors='white', label='Planet Core', zorder=6)
    max_b = max(3.0, hz_outer * 1.3, my_distance * 1.2)
    ax.set_xlim(-0.02 * max_b, max_b); ax.set_ylim(-0.5, 0.5); ax.get_yaxis().set_visible(False)
    ax.spines['bottom'].set_color('#ffffff'); ax.tick_params(colors='white')
    for s in ['top','left','right']: ax.spines[s].set_visible(False)
    st.pyplot(fig)

st.markdown("---")
st.header("📋 Target Catalog Data Archive")
st.dataframe(active_df, use_container_width=True)
