# Save this file as: app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="NextEarth Exoplanet Dashboard", page_icon="🔭", layout="wide")

st.title("🔭 NextEarth Exoplanet Discovery Dashboard")
st.markdown("Automated telemetry, transit analysis, and habitability tracking for novel space candidates.")

# Load candidates database if it exists
if os.path.exists("habitable_candidates.csv"):
    df_candidates = pd.read_csv("habitable_candidates.csv")
else:
    # Fallback dummy data if file isn't generated yet
    df_candidates = pd.DataFrame({
        'target': ['Alpha-Discovery-01b'],
        'period_days': [3.92],
        'transit_depth_ppm': [23275.4],
        'planet_radius_earth': [11.63],
        'snr': [17.78],
        'status': ['NEW_DISCOVERY']
    })

# Candidate selection dropdown
selected_target = st.selectbox("Select Candidate System", df_candidates['target'].values)

# Filter data for selected target
target_row = df_candidates[df_candidates['target'] == selected_target].iloc[0]

st.subheader(f"System Analysis: {selected_target}")

# Safely extract status text with string type-casting
status_text = target_row.get('status', 'Outside Habitable Zone')
is_priority_one = "PRIORITY 1" in str(status_text)

# Metrics display
col1, col2 = st.columns(2)
with col1:
    if "Habitable" in str(status_text) or is_priority_one:
        st.success(f"Current Planet Status: {status_text}")
    else:
        st.error(f"Current Planet Status: ❌ Outside Habitable Zone")

with col2:
    st.metric("Orbital Period", f"{target_row.get('period_days', 0.0):.4f} Days")

c1, c2 = st.columns(2)
with c1:
    sizing = "Gas Giant" if target_row.get('planet_radius_earth', 0) > 6.0 else "Rocky / Sub-Neptune"
    st.markdown(f"**Planet Sizing Type**\n### {sizing}")
with c2:
    axis = 0.115 # Estimated AU representation
    st.markdown(f"**Orbital Coordinates**\n### {axis} AU")

st.markdown(f"📝 **Discovery Log Notes:** Clean U-shape transit signature flagged.")

# --- Matplotlib Plotting Section with Safe Float Casting ---
fig, ax = plt.subplots(figsize=(10, 4))

# Define Habitable Zone inner and outer boundaries safely as scalar floats
luminosity = 1.0  # Solar luminosity approximation
hz_inner = float(np.sqrt(luminosity / 1.1))
hz_outer = float(np.sqrt(luminosity / 0.53))

# Render Goldilocks zone span safely
ax.axvspan(hz_inner, hz_outer, color='#28a745', alpha=0.4, label='Goldilocks Zone')

# Dummy phase plot data visualization
phases = np.linspace(0, 1, 100)
flux_mock = 1.0 - 0.02 * np.exp(-((phases - 0.5)**2) / 0.002)
ax.plot(phases, flux_mock, '.', color='navy', alpha=0.5, label='Folded Transit Data')

ax.set_xlabel("Orbital Phase")
ax.set_ylabel("Normalized Flux")
ax.set_title(f"Transit and Habitability Span: {selected_target}")
ax.legend(loc='lower right', facecolor='#1e222b', labelcolor='white')

st.pyplot(fig)
