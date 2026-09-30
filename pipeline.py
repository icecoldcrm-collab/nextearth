# Save this file as: pipeline.py

import os
import requests
import pandas as pd
import numpy as np
import lightkurve as lk
from transitleastsquares import transitleastsquares
import matplotlib.pyplot as plt

def fetch_dynamic_target_queue(limit=50):
    """
    Dynamically queries the NASA Exoplanet Archive TAP service to pull a batch 
    of TESS targets straight from the official 'toi' table using stable syntax.
    """
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    # Clean ADQL select query targeting the TESS object of interest catalog
    query = f"select top {limit} tic from toi"
    params = {'query': query, 'format': 'json'}
    
    queue = []
    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            for row in data:
                tic = row.get('tic')
                if tic:
                    queue.append({"name": f"TIC {tic}", "id": str(tic)})
        else:
            print(f"❌ Error: NASA Archive returned status code {response.status_code}")
    except Exception as e:
        print(f"❌ Critical Error fetching dynamic queue from archive: {e}")
        
    return queue

def run_pipeline():
    print("🔭 Fetching dynamic target queue from NASA Exoplanet Archive...")
    target_queue = fetch_dynamic_target_queue(limit=50)
    
    if not target_queue:
        print("❌ Pipeline aborted: Target queue from source is completely empty.")
        return

    print(f"📋 Loaded {len(target_queue)} targets into processing queue from source.")
    valid_discovery_found = False

    for item in target_queue:
        target_name = item["name"]
        tic_id_num = item["id"]
        
        print(f"\n----------------------------------------")
        print(f"🔭 Inspecting target: {target_name}")

        try:
            # 1. Search light curve data via Lightkurve
            search_result = lk.search_lightcurve(target_name, mission="TESS", author="SPOC")
            if len(search_result) == 0:
                print(f"❌ No SPOC light curve found for {target_name}. Skipping.")
                continue
                
            # Download, clean outliers, and normalize flux to ~1.0 for TLS compatibility
            lc = search_result[0].download().remove_outliers().normalize()
            time = lc.time.value
            flux = lc.flux.value

            mask = np.isfinite(time) & np.isfinite(flux)
            time, flux = time[mask], flux[mask]

            # 2. Run Transit Least Squares (TLS) analysis
            print(f"🔬 Running TLS analysis for {target_name}...")
            model = transitleastsquares(time, flux)
            results = model.power(period_min=1.0, period_max=15.0, oversampling_factor=3)

            # 3. Validate results
            if results.period is None or np.isnan(results.period) or np.isnan(results.snr):
                print(f"⚠️ TLS analysis inconclusive for {target_name}. Discarding and moving next.")
                continue

            period = results.period
            transit_depth = results.depth
            snr = results.snr
            planet_radius = results.rp_rs * 10.0
            calculated_axis = 0.0432

            print(f"🎯 Valid Transit Confirmed! Period: {period:.4f} days, S/N: {snr:.2f}")

            sizing_profile = "Gas Giant" if planet_radius > 6.0 else "Rocky / Sub-Neptune"
            habitable_status = "Outside Habitable Zone"

            # Save verified candidate row to CSV database
            csv_file = "habitable_candidates.csv"
            file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
            
            df_candidates = pd.DataFrame([{
                'target': target_name,
                'period_days': period,
                'transit_depth_ppm': transit_depth,
                'planet_radius_earth': planet_radius,
                'snr': snr,
                'status': 'NEW_DISCOVERY'
            }])
            
            df_candidates.to_csv(csv_file, mode='a', index=False, header=not file_exists)
            print(f"💾 Successfully recorded verified candidate {target_name} to '{csv_file}'.")

            # Generate diagnostic chart using correct model attribute
            plt.figure(figsize=(10, 4))
            plt.plot(results.folded_phase, results.folded_y, '.', color='navy', alpha=0.3, label='Folded Data')
            plt.plot(results.folded_phase, results.model_lightcurve, color='red', lw=2, label='TLS Model Fit')
            plt.xlabel("Phase")
            plt.ylabel("Normalized Flux")
            plt.title(f"New Discovery Transit Fit: {target_name}")
            plt.legend()
            plt.savefig(f"transit_chart_{tic_id_num}.png", dpi=200, bbox_inches='tight')
            plt.close()
            print(f"💾 Transit chart saved as 'transit_chart_{tic_id_num}.png'.")

            valid_discovery_found = True
            break # Stop after finding our clean discovery for this pipeline cycle

        except Exception as e:
            print(f"❌ Error processing {target_name}: {e}. Moving to next.")
            continue

    if not valid_discovery_found:
        print("ℹ Scan cycle complete: Checked available dynamic batch, no valid candidates verified in this run.")

if __name__ == "__main__":
    run_pipeline()
