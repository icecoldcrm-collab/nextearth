import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def render_plots_and_tables(star_luminosity, my_radius, my_distance, atmo_thickness, active_df, feed_type):
    base_inner = np.sqrt(star_luminosity / 1.1)
    base_outer = np.sqrt(star_luminosity / 0.53)
    size_greenhouse_bonus = max(0.0, (my_radius - 1.0) * 0.1)
    total_greenhouse_multiplier = 1.0 + (np.log1p(atmo_thickness) * 0.35) + size_greenhouse_bonus
    hz_inner = base_inner / np.sqrt(total_greenhouse_multiplier * 0.95)
    hz_outer = base_outer * np.sqrt(total_greenhouse_multiplier)

    size_class = "Sub-Earth" if my_radius<=0.8 else ("Earth-sized Rocky World" if my_radius<=1.25 else ("Super-Earth" if my_radius<=2.0 else ("Neptunian" if my_radius<=6.0 else "Gas Giant")))
    if hz_inner <= my_distance <= hz_outer and size_class in ["Earth-sized Rocky World", "Super-Earth"] and atmo_thickness <= 10.0:
        status_text = "🎯 INSIDE DYNAMIC GOLDILOCKS ZONE!"; status_color = "green"
    else:
        status_text = "❌ OUTSIDE DYNAMIC GOLDILOCKS ZONE"; status_color = "red"

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
