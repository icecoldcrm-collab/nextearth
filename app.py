import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Universal Exoplanet Dashboard", layout="wide")
st.title("🌌 Universal Exoplanet Characterisation Dashboard")
st.write("Reading processed telescope telemetry arrays directly from your local repository database.")

# Instantly loads your compiled master catalog file
try:
    global_universe_df = pd.read_csv("habitable_candidates.csv")
    data_loaded = True
except FileNotFoundError:
    data_loaded = False
    global_universe_df = pd.DataFrame()

if data_loaded and not global_universe_df.empty:
    def extract_parent_star(name):
        if isinstance(name, str) and len(name) > 2:
            return name[:-2] if (name[-1].islower() and name[-2] == ' ') else (name[:-1] if name[-1].islower() else name)
        return "Unknown Star"
    global_universe_df['parent_star_system'] = global_universe_df['pl_name'].apply(extract_parent_star)

    st.sidebar.header("⚙️ Configuration Workspace")
    unique_stars = sorted(global_universe_df['parent_star_system'].dropna().unique().tolist())
    star_filter = st.sidebar.selectbox("1. Filter by Parent Star System:", ["All Stars"] + unique_stars)

    planet_choices = global_universe_df[global_universe_df['parent_star_system'] == star_filter]['pl_name'].tolist() if star_filter != "All Stars" else sorted(global_universe_df['pl_name'].dropna().tolist())
    selected_planet_name = st.sidebar.selectbox("2. Select Target Exoplanet:", ["Custom Parameters"] + planet_choices)

    init_lum, init_rad, init_dist, init_atmo = 1.0, 1.0, 1.0, 1.0
    if selected_planet_name != "Custom Parameters":
        p_row = global_universe_df[global_universe_df['pl_name'] == selected_planet_name].iloc[0]
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
    type_counts = global_universe_df['size_classification'].value_counts()

    col_l, col_r = st.columns(2)
    with col_l:
        if not type_counts.empty:
            fig2, ax2 = plt.subplots(figsize=(3, 3))
            fig2.patch.set_facecolor('#0e1117')
            ax2.pie(type_counts, labels=type_counts.index, autopct='%1.1f%%', startangle=140, textprops={'color': 'white', 'fontsize': 8})
            ax2.axis('equal'); st.pyplot(fig2)
    with col_r:
        st.write(f"**Total Active Row Count:** {len(global_universe_df)}")

    st.markdown("---")
    search_query = st.text_input("✍️ Search Planet by Designation Name:", "")
    available_statuses = global_universe_df['habitability_status'].unique().tolist()
    selected_statuses = st.multiselect("🎯 Filter by Habitability Tag Status:", options=available_statuses, default=available_statuses)

    filtered_df = global_universe_df[global_universe_df['habitability_status'].isin(selected_statuses)]
    if search_query: 
        filtered_df = filtered_df[filtered_df['pl_name'].str.contains(search_query, case=False, na=False)]
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("📊 Processing background telemetry matrix... Make sure your GitHub Actions pipeline workflow runs once successfully to generate your database file!")
