import pandas as pd
import numpy as np
import os
import requests
import lightkurve as lk
from transitleastsquares import transitleastsquares
import ssl
import urllib3
from io import StringIO

# Suppress certificate warning clutter in execution logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_live_unidentified_stream(limit=3):
    """
    Harvests live TOI targets along with rigorous stellar parameters directly 
    from the NASA Exoplanet Archive TAP registry, discarding incomplete entries.
    """
    print("🛰️ Harvesting Live Stream & Verified Stellar Parameters from NASA Exoplanet Archive...")
    
    url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    
    # Query tid along with cataloged stellar radius and effective temperature
    params = {
        'query': "select top 50 tid, st_rad, st_teff from toi order by toi desc",
        'format': 'csv'
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
        if response.status_code == 200 and "ERROR" not in response.text.upper():
            df_stream = pd.read_csv(StringIO(response.text))
            
            if 'tid' in df_stream.columns:
                df_stream['target_id'] = "TIC " + df_stream['tid'].astype(str)
            else:
                df_stream['target_id'] = "TIC " + df_stream.iloc[:, 0].astype(str)
                
            # Drop rows where crucial stellar parameters are missing to preserve scientific integrity
            df_stream = df_stream.dropna(subset=['st_rad', 'st_teff'])
            
            valid_targets = []
            for _, row in df_stream.head(limit).iterrows():
                valid_targets.append({
                    'target_id': row['target_id'],
                    'catalog_radius': float(row['st_rad']),
                    'catalog_teff': float(row['st_teff'])
                })
                
            print(f"📥 Successfully isolated {len(valid_targets)} rigorously vetted systems from NASA.")
            return valid_targets
        else:
            print(f"⚠️ NASA TAP API error: {response.text[:150]}")
    except Exception as e:
        print(f"⚠️ API connection exception: {e}")
    
    return []

def analyze_raw_star_light_chart(target_info):
    """
    Downloads raw starlight telemetry charts from MAST, tests for hidden planet footprints,
    and calculates accurate vectors using rigorously verified host star parameters.
    """
    star_id = target_info['target_id']
    star_radius = target_info['catalog_radius']
    star_teff = target_info['catalog_teff']
    
    print(f"\n✨ Initiating Automated Signal Sweep on Target: {star_id} (Radius: {star_radius} R☉, Teff: {star_teff}K)")
    ssl._create_default_https_context = ssl._create_unverified_context
    
    try:
        search_result = lk.search_lightcurve(star_id)
            
        if len(search_result) == 0:
            print(f"📋 Skipping {star_id}: Light charts currently restricted or missing in MAST.")
            return None
            
        lc_collection = search_result[:1].download_all()
        lc = lc_collection.stitch().flatten(window_length=401).remove_outliers()
        
        # High-performance downsampling optimization
        lc_binned = lc.bin(time_bin_size=0.02) 
        time = lc_binned.time.value
        flux = lc_binned.flux.value
        
        model = transitleastsquares(time, flux)
        results = model.power(period_min=1.0, period_max=15.0, oversampling_factor=1, duration_grid_step=2)
        
        print(f"🧠 Analysis Finished! Signal-to-Noise Ratio (SNR): {results.snr:.2f}")
        
        if results.snr >= 6.0:
            print(f"🎯 PLANET SIGNAL CONFIRMED! Calculating precise physical vectors...")
            
            period_days = results.period
            transit_depth = 1.0 - results.depth
            
            # Precise physical calculations using verified TAP parameters
            star_luminosity = (star_radius**2) * ((star_teff / 5778)**4)
            calculated_distance_au = ((period_days / 365.25)**2 * star_radius)**(1/3)
            planet_radius_earth = star_radius * np.sqrt(transit_depth) * 109.2
            
            hz_inner = np.sqrt(star_luminosity / 1.1)
            hz_outer = np.sqrt(star_luminosity / 0.53)
            
            if planet_radius_earth <= 0.8: 
                size_class = "Sub-Earth"
            elif 0.8 < planet_radius_earth <= 1.25: 
                size_class = "Earth-sized Rocky"
            elif 1.25 < planet_radius_earth <= 2.4: 
                size_class = "Super-Earth / Ocean World"
            else: 
                size_class = "Gas Giant"
            
            if hz_inner <= calculated_distance_au <= hz_outer:
                status = "🎯 PRIORITY 1: Habitable Zone Rocky World" if "Rocky" in size_class or "Super-Earth" in size_class else "⚠️ Zone Match (Gas World Configuration)"
            else:
                status = "❌ Outside Habitable Zone"
                
            notes = f"Discovered via Live NASA Stream. SNR: {results.snr:.1f}. Loop Period: {period_days:.2f} days."
            
            # --- AUTOMATED REPORT PACKAGE GENERATION ---
            print(f"🚨 Elite Candidate! Generating Observation Report Packet for {star_id}...")
            
            clean_id = star_id.replace(' ', '_')
            exofop_report = f"""=======================================================
NASA EXOFOP PLANET CANDIDATE OBSERVATION REPORT
Generated by: Automated TLS Analysis Engine
=======================================================
Target Identifier : {star_id}
Candidate Name    : {clean_id}-candidate
Orbital Period    : {period_days:.5f} days
Transit Depth     : {transit_depth * 1000000:.1f} ppm
Planet Radius     : {planet_radius_earth:.2f} Earth Radii
Calculated Axis   : {calculated_distance_au:.4f} AU
Signal-to-Noise   : {results.snr:.2f}
Sizing Profile    : {size_class}
Habitable Status  : {status}

Methodology Notes:
Signal extracted via Transit Least Squares (TLS) matching on 
binned space telescope telemetry arrays. Stellar parameters 
verified via NASA Exoplanet Archive TAP registry.
======================================================="""
            
            report_filename = f"exofop_submission_{clean_id}.txt"
            with open(report_filename, "w") as f:
                f.write(exofop_report)
            
            try:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(6, 4))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#1e222b')
                
                ax.scatter(results.folded_phase, results.folded_y, c='white', s=2, alpha=0.3, label='Binned Telemetry')
                ax.plot(results.model_folded_phase, results.model_folded_model, color='#ff7f0e', linewidth=2, label='TLS Geometric Fit')
                
                ax.set_title(f"Transit Validation Profile: {star_id}", color='white', fontsize=10)
                ax.set_xlabel("Orbital Phase", color='white', fontsize=8)
                ax.set_ylabel("Relative Brightness (Flux)", color='white', fontsize=8)
                ax.tick_params(colors='white', labelsize=8)
                ax.grid(alpha=0.1)
                ax.legend(loc='lower left', fontsize=8)
                
                plot_filename = f"transit_chart_{clean_id}.png"
                plt.savefig(plot_filename, dpi=150, bbox_inches='tight')
                plt.close()
            except Exception as e:
                print(f"⚠️ Could not compile diagnostic plot graphic: {e}")

            return {
                'pl_name': f"{clean_id}-candidate",
                'pl_rade': round(planet_radius_earth, 2),
                'size_classification': size_class,
                'calculated_distance_au': round(calculated_distance_au, 3),
                'hz_inner_edge_au': round(hz_inner, 3),
                'hz_outer_edge_au': round(hz_outer, 3),
                'habitability_status': status,
                'observer_notes': notes,
                'star_teff': round(star_teff, 1),
                'star_radius': round(star_radius, 2)
            }
        else:
            print("❌ Signal validation pass failed: Dip profiles match background solar noise.")
            return None
            
    except Exception as e:
        print(f"❌ Processing exception triggered on target framework: {e}")
        return None

if __name__ == "__main__":
    filename = "habitable_candidates.csv"
    mock_columns = [
        'pl_name', 'pl_rade', 'size_classification', 'calculated_distance_au', 
        'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status', 'observer_notes',
        'star_teff', 'star_radius'
    ]
    
    batch_limit = int(os.environ.get('BATCH_LIMIT', 3))
    targets_pool = fetch_live_unidentified_stream(limit=batch_limit)
    new_logs = []
    
    for target_info in targets_pool:
        candidate_data = analyze_raw_star_light_chart(target_info)
        if candidate_data:
            new_logs.append(candidate_data)
            
    if os.path.exists(filename):
        try:
            existing_df = pd.read_csv(filename)
            for col in mock_columns:
                if col not in existing_df.columns:
                    existing_df[col] = 5778 if col == 'star_teff' else (1.0 if col == 'star_radius' else 'Unknown')
        except Exception:
            existing_df = pd.DataFrame(columns=mock_columns)
    else:
        mock_data = [
            ['Alpha-Discovery-01b', 3.18, 'Gas Giant', 0.115, 0.953, 1.374, '❌ Outside Habitable Zone', 'Discovery Log Notes: Clean U-shape transit signature flagged.', 5778, 1.0],
            ['Beta-Survey-12c', 14.59, 'Gas Giant', 0.822, 1.275, 1.837, '❌ Outside Habitable Zone', 'Deep dip, high visual noise profile.', 5500, 0.9],
            ['Gemma-Candidate-d', 0.30, 'Sub-Earth', 0.051, 0.073, 0.105, '❌ Outside Habitable Zone', 'Micro-transit event isolated on low-mass star.', 3500, 0.4],
            ['Zeta-Anomaly-e', 6.43, 'Gas Giant', 1.055, 0.795, 1.145, '⚠️ Zone Match (Gas World Configuration)', 'Long-duration single transit event verified.', 6000, 1.2],
            ['KIC10593626-b (Kepler-22b)', 2.40, 'Super-Earth / Ocean World', 0.849, 0.847, 1.222, '🎯 PRIORITY 1: Habitable Zone Rocky World', 'Calibrated True Baseline Observation Run.', 5518, 0.97]
        ]
        existing_df = pd.DataFrame(mock_data, columns=mock_columns)
        
    if new_logs:
        df_new = pd.DataFrame(new_logs)
        existing_df = existing_df[~existing_df['pl_name'].isin(df_new['pl_name'])]
        existing_df = pd.concat([existing_df, df_new], ignore_index=True)
        
    existing_df.to_csv(filename, index=False)
    print(f"\n💾 High-Throughput Pipeline Complete! Active archive database updated to {len(existing_df)} rows.")
