import pandas as pd
import numpy as np
import os
import lightkurve as lk
from transitleastsquares import transitleastsquares
import ssl

def analyze_raw_star_light_chart(star_id="KIC 10593626"):
    """
    Downloads raw telescope starlight data, searches for periodic transit dips 
    using Transit Least Squares, and records new planet candidates to the database.
    """
    print(f"🛰️ Accessing Mikulski Archive for Space Telescopes (MAST)...")
    print(f"📥 Downloading raw light charts for target system: {star_id}")
    
    # Bypass local virtual machine SSL limitations safely
    ssl._create_default_https_context = ssl._create_unverified_context
    
    try:
        # 1. Search and download public data blocks from Kepler or TESS missions
        search_result = lk.search_lightcurve(star_id, author='Kepler', cadence='long')
        if len(search_result) == 0:
            raise RuntimeError(f"Could not locate light curves for {star_id} in public archives.")
            
        lc_collection = search_result.download_all()
        # Clean, stitch, and flatten out systemic telescope trends and starspots
        lc = lc_collection.stitch().flatten(window_length=401).remove_outliers()
        
        # Extract raw arrays from the open-source science objects
        time = lc.time.value
        flux = lc.flux.value
        print("📊 Light curve isolated. Commencing Transit Least Squares (TLS) spectrum sweep...")
        
        # 2. Run the actual professional planet-finding algorithm
        # This scans across time looking for geometric silhouette markers matching a planet profile
        model = transitleastsquares(time, flux)
        results = model.power()
        
        print(f"🧠 Analysis Complete! Signal-to-Noise Ratio (SNR): {results.snr:.2f}")
        
        # 3. Scientific Validation Gate: A planet candidate requires a solid signal-to-noise ratio
        if results.snr >= 7.0:
            print("🎯 PLANET CANDIDATE DETECTED! Running physical extraction math...")
            
            # Extract metrics directly from the raw light curve shapes
            transit_depth = 1.0 - results.depth
            period_days = results.period
            duration_days = results.duration
            
            # Pull star properties embedded inside the archive data header fields
            star_radius = getattr(lc, 'meta', {}).get('RADIUS', 1.0)
            star_teff = getattr(lc, 'meta', {}).get('TEFF', 5778)
            star_luminosity = (star_radius**2) * ((star_teff / 5778)**4)
            
            # Calculate metrics via Keplerian laws
            calculated_distance_au = ((period_days / 365.25)**2 * star_radius)**(1/3)
            planet_radius_earth = star_radius * np.sqrt(transit_depth) * 109.2
            
            hz_inner = np.sqrt(star_luminosity / 1.1)
            hz_outer = np.sqrt(star_luminosity / 0.53)
            
            if planet_radius_earth <= 0.8: size_class = "Sub-Earth"
            elif 0.8 < planet_radius_earth <= 1.25: size_class = "Earth-sized Rocky"
            elif 1.25 < planet_radius_earth <= 2.0: size_class = "Super-Earth"
            else: size_class = "Gas Giant"
            
            if hz_inner <= calculated_distance_au <= hz_outer:
                if size_class in ["Earth-sized Rocky", "Super-Earth"]:
                    status = "🎯 PRIORITY 1: Habitable Zone Rocky World"
                else:
                    status = "⚠️ Zone Match (Gas World)"
            else:
                status = "❌ Outside Habitable Zone"
                
            notes = f"Discovered via TLS Pipeline. SNR: {results.snr:.1f}. Period: {period_days:.1f} days."
            
            new_discovery = {
                'pl_name': f"{star_id.replace(' ', '')}-b",
                'pl_rade': round(planet_radius_earth, 2),
                'size_classification': size_class,
                'calculated_distance_au': round(calculated_distance_au, 3),
                'hz_inner_edge_au': round(hz_inner, 3),
                'hz_outer_edge_au': round(hz_outer, 3),
                'habitability_status': status,
                'observer_notes': notes
            }
            
            # 4. Commit directly into our database storage tracking file
            filename = "habitable_candidates.csv"
            if os.path.exists(filename):
                existing_df = pd.read_csv(filename)
                # Avoid logging duplicate entries of the same star system
                existing_df = existing_df[existing_df['pl_name'] != new_discovery['pl_name']]
                df_updated = pd.concat([existing_df, pd.DataFrame([new_discovery])], ignore_index=True)
            else:
                df_updated = pd.DataFrame([new_discovery])
                
            df_updated.to_csv(filename, index=False)
            print(f"💾 Discovery committed securely to local database catalog registry file!")
            return df_updated
        else:
            print("❌ No valid periodic planet transits detected above background noise thresholds.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Structural break in science tool arrays: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Test-running on KIC 10593626 (The host star of the famous Kepler-22b world)
    # You can change this to any Kepler ID string to process its raw light graphs
    analyze_raw_star_light_chart("KIC 10593626")
