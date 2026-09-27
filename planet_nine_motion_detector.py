import matplotlib.pyplot as plt
import numpy as np

def plot_solar_system_candidate(candidate_row):
    """
    Plots a top-down polar view of the solar system, mapping known outer planets
    and positioning the candidate object based on its sky angle and estimated distance.
    """
    print("🗺️ Generating Top-Down Solar System Mapping Visualization...")
    
    # Setup polar coordinates (Angle in radians, Radius in Astronomical Units - AU)
    fig, ax = plt.subplots(subplot_projection='polar', figsize=(8, 8))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1e222b')
    
    # Known Planet Orbits (Approximate average distances in AU)
    planets = {
        'Earth': (1.0, 0.0, 'cyan', 3),
        'Jupiter': (5.2, 1.2, 'orange', 6),
        'Saturn': (9.5, 2.4, 'gold', 5),
        'Uranus': (19.2, 3.5, 'lightblue', 7),
        'Neptune': (30.1, 4.8, 'blue', 7)
    }
    
    # Plot known planets for scale
    for name, (dist, angle, color, size) in planets.items():
        ax.scatter(angle, dist, c=color, s=size*10, label=name, edgecolors='white', linewidths=0.5)
        ax.text(angle, dist + 2, name, color='white', fontsize=8, ha='center')

    # Approximate candidate position (Using RA converted to angle, and an estimated outer-system distance, e.g., 500 AU)
    ra_deg = candidate_row.get('ra', 180.0)
    candidate_angle = np.deg2rad(ra_deg % 360) # Map RA to orbital angle
    
    # Estimate distance based on brightness profile (faint cold objects mapped further out)
    estimated_distance_au = 500.0 
    
    # Relative sizing: Scale marker based on infrared magnitude / estimated radius 
    # (Planet Nine is theorized to be ~3 to 5 Earth radii - an Ice Giant)
    marker_size = 150 
    
    ax.scatter(
        candidate_angle, estimated_distance_au, 
        c='#ff4b4b', s=marker_size, marker='*', 
        label='Planet Nine Candidate', edgecolors='yellow', linewidths=1.5
    )
    
    # Styling the polar plot for deep-space aesthetics
    ax.set_rmax(700) # View out to 700 AU
    ax.tick_params(colors='white', labelsize=8)
    ax.grid(color='gray', alpha=0.3, linestyle='--')
    ax.set_title("Outer Solar System Candidate Mapping (Top-Down View)", color='white', pad=20, fontsize=11)
    
    # Legend and layout
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), facecolor='#1e222b', edgecolor='none', labelcolor='white', fontsize=8)
    
    plot_filename = "planet_nine_solar_system_map.png"
    plt.savefig(plot_filename, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"💾 Solar system map successfully saved as '{plot_filename}'!")

# Example integration call:
# if not moving_candidates.empty:
#     plot_solar_system_candidate(moving_candidates.iloc[0])
