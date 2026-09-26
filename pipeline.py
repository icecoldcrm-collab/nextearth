import pandas as pd
import numpy as np
import os

def process_transit_light_graphs():
    print("🛰️ Booting Core Transit Light Curve Extraction Array...")
    print("🔍 Scanning raw light curve graphs for asymmetric brightness dips...")
    
    # Simulating raw graph telemetry inputs received from telescope observations
    # Depth = starlight blocked percentage, Period = days between dips, Star properties mapped
    raw_transit_graph_telemetry = [
        # designation, brightness_dip_depth, period_days, st_teff, st_rad, observer_notes
        ['Alpha-Discovery-01b', 0.00085, 14.2, 5778, 1.0, 'Clean U-shape transit signature flagged.'],
        ['Beta-Survey-12c', 0.01240, 248.5, 6100, 1.2, 'Deep dip, high visual noise profile.'],
        ['Gemma-Candidate-d', 0.00012, 8.4, 3200, 0.25, 'Micro-transit event isolated on low-mass star.'],
        ['Zeta-Anomaly-e', 0.00410, 412.9, 5500, 0.92, 'Long-duration single transit event verified.']
    ]
    
    discovered_worlds = []
    
    for graph in raw_transit_graph_telemetry:
        name, visual_depth, period, teff, rad, notes = graph
        print(f"📊 Processing Graph Core: {name} | Depth: {visual_depth*100:.4f}%")
        
        # --- ANALYTICS ENGINE MATHEMATICS (Extracting metrics from visual curves) ---
        # 1. Size Extraction: Radius ratio derived from visual silhouette drop (converted to Earth Radii)
        calculated_radius_earth = rad * np.sqrt(visual_depth) * 109.2
        
        # 2. Distance Extraction: Semi-Major Axis (AU) derived via Kepler's Third Law
        calculated_distance_au = ((period / 365.25)**2 * rad)**(1/3)
        
        # 3. Solar Luminosity Proxy derived via Stefan-Boltzmann approximations
        star_luminosity = (rad**2) * ((teff / 5778)**4)
        
        # 4. Calculate dynamic Goldilocks Zone bounds for this star
        hz_inner = np.sqrt(star_luminosity / 1.1)
        hz_outer = np.sqrt(star_luminosity / 0.53)
        
        # 5. Classify Core Metrics
        if calculated_radius_earth <= 0.8: size_class = "Sub-Earth"
        elif 0.8 < calculated_radius_earth <= 1.25: size_class = "Earth-sized Rocky"
        elif 1.25 < calculated_radius_earth <= 2.0: size_class = "Super-Earth"
        else: size_class = "Gas Giant"
        
        # 6. Evaluate Habitability Proximity
        if hz_inner <= calculated_distance_au <= hz_outer:
            if size_class in ["Earth-sized Rocky", "Super-Earth"]:
                status = "🎯 PRIORITY 1: Habitable Zone Rocky World"
            else:
                status = "⚠️ Zone Match (Gas World Configuration)"
        else:
            status = "❌ Outside Habitable Zone"
            
        discovered_worlds.append([
            name, round(calculated_radius_earth, 2), size_class,
            round(calculated_distance_au, 3), round(hz_inner, 3), round(hz_outer, 3), status, notes
        ])
        
    output_columns = [
        'pl_name', 'pl_rade', 'size_classification', 
        'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status', 'observer_notes'
    ]
    
    df_export = pd.DataFrame(discovered_worlds, columns=output_columns)
    df_export.to_csv("habitable_candidates.csv", index=False)
    print(f"💾 Pipeline Complete! Saved {len(df_export)} newly processed transit discoveries to database.")
    return df_export

if __name__ == "__main__":
    process_transit_light_graphs()
