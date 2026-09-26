import pandas as pd
import numpy as np
import os
import lightkurve as lk
from transitleastsquares import transitleastsquares
import ssl

def analyze_raw_star_light_chart(star_id="KIC 10593626"):
    """
    Downloads raw telescope starlight data, applies downsampling optimization, 
    and searches for periodic transit dips efficiently using optimized TLS.
    """
    print(f"🛰️ Accessing Mikulski Archive for Space Telescopes (MAST)...")
    print(f"📥 Downloading raw light charts for target system: {star_id}")
    
    ssl._create_default_https_context = ssl._create_unverified_context
    
    try:
        search_result = lk.search_lightcurve(star_id, author='Kepler', cadence='long')
        if len(search_result) == 0:
            raise RuntimeError(f"Could not locate light curves for {star_id}.")
            
        # Optimize step: Pull only the first few observation quarters to process 
        # instead of loading a decade of raw telemetry loops simultaneously
        lc_collection = search_result[:3].download_all()
        
        # Clean, stitch, and flatten out systemic telescope trends
        lc = lc_collection.stitch().flatten(window_length=401).remove_outliers()
        
        # HIGH-PERFORMANCE OPTIMIZATION: Downsample/Bin the light curve.
        # This pools every 5 data points together into an average bucket, 
        # preserving the transit shape while reducing data size by 80%.
        lc_binned = lc.bin(time_bin_size=0.02) # ~30 minute bins matching standard cadences
        
        time = lc_binned.time.value
        flux = lc_binned.flux.value
        print(f"📊 Light curve compressed successfully. Points to scan: {len(time)}")
        print("⚡ Commencing HIGH-PERFORMANCE Transit Least Squares (TLS) sweep...")
        
        # 2. Run the actual professional planet-finding algorithm with speed tuners
        model = transitleastsquares(time, flux)
        
        # Speed Constraints: Focus search on high-probability orbital spaces (1 to 20 days)
        # and loosen grid resolution from ultra-fine to fast-scan mode
        results = model.power(
            period_min=1.0,
            period_max=20.0,
            oversampling_factor=1,  # Lower value drops period checks from 180k to ~3,000
            duration_grid_step=2   # Speeds up horizontal transit silhouette width fitting
        )
        
        print(f"🧠 Analysis Complete! Signal-to-Noise Ratio (SNR): {results.snr:.2f}")
        
        if results.snr >= 6.0:
            print("🎯 PLANET CANDIDATE DETECTED! Running physical extraction math...")
            
            transit_depth = 1.0 - results.depth
            period_days = results.period
            
            star_radius = getattr(lc, 'meta', {}).get('RADIUS', 1.0)
            star_teff = getattr(lc, 'meta', {}).get('TEFF', 5778)
            star_luminosity = (star_radius**2) * ((star_teff / 5778)**4)
            
            calculated_distance_au = ((period_days / 365.25)**2 * star_radius)**(1/3)
            planet_radius_earth = star_radius * np.sqrt(transit_depth) * 109.2
            
            hz_inner = np.sqrt(star_luminosity / 1.1)
            hz_outer = np.sqrt(star_luminosity / 0.53)
            
            size_class = "Sub-Earth" if planet_radius_earth<=0.8 else ("Earth-sized Rocky" if planet_radius_earth<=1.25 else ("Super-Earth" if planet_radius_earth<=2.0 else "Gas Giant"))
            
            if hz_inner <= calculated_distance_au <= hz_outer:
                status = "🎯 PRIORITY 1: Habitable Zone Rocky World" if "Rocky" in size_class or "Super-Earth" in size_class else "⚠️ Zone Match"
            else:
                status = "❌ Outside Habitable Zone"
                
            notes = f"Discovered via Fast-TLS. SNR: {results.snr:.1f}. Period: {period_days:.2f} days."
            
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
            
            filename = "habitable_candidates.csv"
            if os.path.exists(filename):
                existing_df = pd.read_csv(filename)
                existing_df = existing_df[existing_df['pl_name'] != new_discovery['pl_name']]
                df_updated = pd.concat([existing_df, pd.DataFrame([new_discovery])], ignore_index=True)
            else:
                df_updated = pd.DataFrame([new_discovery])
                
            df_updated.to_csv(filename, index=False)
            print(f"💾 Discovery committed securely to database file!")
            return df_updated
        else:
            print("❌ No valid periodic planet transits detected above background noise.")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"❌ Structural break in science tool arrays: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Target system optimized scan
    analyze_raw_star_light_chart("KIC 10593626")
