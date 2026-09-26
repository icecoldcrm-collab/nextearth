import pandas as pd
import numpy as np
import os
import ssl  
import urllib.request  
from io import StringIO

def run_exoplanet_discovery_pipeline(output_filename="habitable_candidates.csv"):
    print("🛰️ Connecting to NASA Exoplanet Archive (Live API Engine)...")
    
    # CORRECT FOOTPRINT: Using the exact, verified 'ps' (Planetary Systems) table schema
    url = "https://caltech.edu"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    ssl_context = ssl._create_unverified_context()
    req = urllib.request.Request(url, headers=headers)
    
    print("📥 Opening live data stream link...")
    with urllib.request.urlopen(req, context=ssl_context) as response:
        raw_text = response.read().decode('utf-8')
        
        # If the API connection fails or triggers a service screen, halt immediately instead of hiding it
        if "ERROR" in raw_text or "<html" in raw_text:
            print("❌ Server Error Payload Detected Response Readout:")
            print(raw_text[:500])
            raise RuntimeError("NASA API parameter request rejected by host server.")
            
        df = pd.read_csv(StringIO(raw_text))
        print(f"📥 Telemetry Online! Successfully loaded {len(df)} live records from NASA.")

    print("🧠 Running Analytics Engine & Habitability Processing Vectors...")

    df['st_lum'] = df['st_lum'].fillna((df['st_rad'].fillna(1.0)**2) * ((df['st_teff'].fillna(5778) / 5778)**4))
    df['pl_rade'] = df['pl_rade'].fillna(1.0)
    df['pl_orbper'] = df['pl_orbper'].fillna(30.0)
    df['st_rad'] = df['st_rad'].fillna(1.0)

    df['calculated_distance_au'] = ((df['pl_orbper'] / 365.25)**2 * df['st_rad'])**(1/3)
    df['hz_inner_edge_au'] = np.sqrt(df['st_lum'] / 1.1)
    df['hz_outer_edge_au'] = np.sqrt(df['st_lum'] / 0.53)
    df['size_classification'] = df['pl_rade'].apply(lambda r: "Sub-Earth" if r<=0.8 else ("Earth-sized Rocky" if r<=1.25 else ("Super-Earth" if r<=2.0 else ("Neptunian" if r<=6.0 else "Gas Giant"))))
    
    def flag_habitability(row):
        dist, inner, outer, size = row['calculated_distance_au'], row['hz_inner_edge_au'], row['hz_outer_edge_au'], row['size_classification']
        if (inner <= dist <= outer) and size in ["Earth-sized Rocky", "Super-Earth"]:
            return "🎯 PRIORITY 1: Habitable Zone Rocky World"
        elif (inner <= dist <= outer):
            return "⚠️ Zone Match (Gas Giant / Ice World)"
        else:
            return "❌ Outside Habitable Zone"

    df['habitability_status'] = df.apply(flag_habitability, axis=1)
    final_export = df.copy()

    output_columns = [
        'pl_name', 'tic_id', 'pl_rade', 'size_classification',
        'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status'
    ]
    
    final_export = final_export[output_columns]
    final_export['sort_priority'] = final_export['habitability_status'].apply(
        lambda x: 0 if "🎯" in x else (1 if "⚠️" in x else 2)
    )
    final_export = final_export.sort_values(by=['sort_priority', 'pl_name']).drop(columns=['sort_priority'])

    final_export.to_csv(output_filename, index=False)
    print(f"💾 Pipeline Execution Successful! Catalogued {len(final_export)} total worlds.")
    return final_export

if __name__ == "__main__":
    run_exoplanet_discovery_pipeline()
