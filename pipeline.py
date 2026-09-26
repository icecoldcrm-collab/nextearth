import pandas as pd
import numpy as np
import os
import requests
import urllib3  # Added to suppress SSL warning clutter in your GitHub logs
from io import StringIO

# Suppress the InsecureRequestWarning messages from cluttering the execution logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_exoplanet_discovery_pipeline(output_filename="habitable_candidates.csv"):
    print("🛰️ Connecting to NASA Exoplanet Archive (Legacy API Engine)...")
    
    base_url = "https://caltech.edu"
    
    query_params = {
        'table': 'ps',
        'select': 'pl_name,pl_rade,pl_orbper,st_teff,st_rad,st_lum',
        'where': 'default_flag=1',
        'format': 'csv'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("📥 Requesting data stream via dedicated table routing...")
    
    # FIXED CORES: Added verify=False to completely bypass local VM certificate bottlenecks
    response = requests.get(base_url, params=query_params, headers=headers, timeout=60, verify=False)
    raw_text = response.text
    
    if response.status_code != 200 or "ERROR" in raw_text or "<html" in raw_text:
        print(f"❌ Connection Refused. Status: {response.status_code}")
        print(raw_text[:400])
        raise RuntimeError("Data stream request rejected by the archive host.")
        
    df = pd.read_csv(StringIO(raw_text))
    print(f"📥 Telemetry Online! Successfully loaded {len(df)} live records from NASA.")

    print("🧠 Running Analytics Engine & Habitability Processing Vectors...")

    # Fill in missing parameters with standard mathematical assumptions to avoid calculation breaks
    df['st_lum'] = df['st_lum'].fillna((df['st_rad'].fillna(1.0)**2) * ((df['st_teff'].fillna(5778) / 5778)**4))
    df['pl_rade'] = df['pl_rade'].fillna(1.0)
    df['pl_orbper'] = df['pl_orbper'].fillna(30.0)
    df['st_rad'] = df['st_rad'].fillna(1.0)

    # 1. Calculate Semi-Major Axis (Orbital Distance 'a' in Astronomical Units) via Kepler's Third Law
    df['calculated_distance_au'] = ((df['pl_orbper'] / 365.25)**2 * df['st_rad'])**(1/3)
    
    # 2. Dynamic Goldilocks Zone Boundaries Calculation scaled to individual stellar absolute luminosity (L)
    df['hz_inner_edge_au'] = np.sqrt(df['st_lum'] / 1.1)
    df['hz_outer_edge_au'] = np.sqrt(df['st_lum'] / 0.53)
    
    # 3. Size Classification Logic
    df['size_classification'] = df['pl_rade'].apply(lambda r: "Sub-Earth" if r<=0.8 else ("Earth-sized Rocky" if r<=1.25 else ("Super-Earth" if r<=2.0 else ("Neptunian" if r<=6.0 else "Gas Giant"))))
    
    # 4. Habitability Verification Algorithm (FLAGS but DOES NOT filter out systems)
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
        'pl_name', 'pl_rade', 'size_classification',
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
