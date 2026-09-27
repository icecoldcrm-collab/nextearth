import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load active catalog database
df = pd.read_csv("habitable_candidates.csv")

# Select a target from dropdown or sidebar
selected_target = st.selectbox("Select Candidate System", df['pl_name'].unique())
row = df[df['pl_name'] == selected_target].iloc[0]

st.markdown(f"### 🔭 System Analysis: {row['pl_name']}")

# Read exact status from database
status_text = row['habitability_status']

if "PRIORITY 1" in status_text:
    st.success(f"### Current Planet Status: {status_text}")
elif "Zone Match" in status_text or "⚠️" in status_text:
    st.warning(f"### Current Planet Status: {status_text}")
else:
    st.error(f"### Current Planet Status: {status_text}")

# Display metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Planet Sizing Type", row['size_classification'])
with col2:
    st.metric("Orbital Coordinates", f"{row['calculated_distance_au']} AU")

st.markdown(f"📝 **Discovery Log Notes:** {row['observer_notes']}")

# --- Stellar Color Mapping Function based on Effective Temperature (Teff) ---
def get_star_color(teff):
    if teff >= 10000:
        return '#9bb0ff'  # O/B-type: Blue-white
    elif teff >= 7500:
        return '#cad7ff'  # A-type: White
    elif teff >= 6000:
        return '#f8f7ff'  # F-type: Yellow-white
    elif teff >= 5200:
        return '#ffe4b5'  # G-type: Yellow (Sun-like, ~5778K)
    elif teff >= 3700:
        return '#ffad5b'  # K-type: Orange
    else:
        return '#ff4500'  # M-type: Red Dwarf

# Fetch star properties safely (with defaults if old mock data is loaded)
star_teff = row.get('star_teff', 5778)
star_radius = row.get('star_radius', 1.0)
star_color = get_star_color(star_teff)

# --- Habitable Zone Visualizer Chart with Scaled Colored Star ---
fig, ax = plt.subplots(figsize=(8, 1.8))
fig.patch.set_facecolor('#0e1117')
ax.set_facecolor('#1e222b')

# 1. Plot the Host Star (Scaled by radius and colored by temperature type)
# Note: Radius is exaggerated slightly for visual clarity on an AU scale
star_marker_size = max(80, float(star_radius) * 120)
ax.scatter([0.0], [0], color=star_color, s=star_marker_size, zorder=6, label=f'Host Star ({star_teff}K)')

# 2. Draw the Habitable Zone (Green Shaded Region)
hz_inner = row['hz_inner_edge_au']
hz_outer = row['hz_outer_edge_au']
ax.axvspan(hz_inner, hz_outer, color='#28a745', alpha=0.4, label='Goldilocks Zone')

# 3. Plot the Planet's Orbit
planet_dist = row['calculated_distance_au']
ax.scatter([planet_dist], [0], color='#1f77b4', s=150, zorder=5, edgecolors='white', label='Candidate Orbit')

# Chart formatting
ax.set_xlim(-0.1, max(3.0, planet_dist + 0.5))
ax.set_ylim(-0.5, 0.5)
ax.set_yticks([])
ax.set_xlabel("Orbital Distance from Star (AU)", color='white', fontsize=9)
ax.tick_params(colors='white', labelsize=8)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_color('white')
ax.legend(loc='upper right', fontsize=8, facecolor='#1e222b', edgecolor='none', labelcolor='white')

st.pyplot(fig)
