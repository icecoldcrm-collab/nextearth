# Save this file as: planet_nine_scanner.py

import pandas as pd
import numpy as np
import requests
from io import StringIO
from astropy.coordinates import SkyCoord
import astropy.units as u
import urllib3
import matplotlib.pyplot as plt
import time
import os

# Suppress certificate warnings for secure TAP queries
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_epoch_data(catalog_table, max_rows=300):
    """
    Queries an infrared catalog table from the NASA IRSA TAP service 
    using a spatial box constraint to prevent server-side read timeouts.
    """
    print(f"🛰️ Querying NASA IRSA TAP for catalog: {catalog_table}...")
    url = "https://irsa.ipac.caltech.edu/TAP/sync"
    
    # Constrain the search using a spatial BOX search (RA, Dec, Width, Height) 
    # and broader magnitude bounds to capture faint outer-system candidates.
    query_str = f"""
    select top {max_rows} ra, dec, w1mpro, w2mpro 
    from {catalog_table} 
    where CONTAINS(POINT(ra, dec), BOX(150.0, 10.0, 3.0, 3.0)) = 1
      and w1mpro > 15.0 
      and w2mpro > 14.0
    """
    
    params = {'query': query_str, 'format': 'csv'}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Retry loop to handle public server throttling or transient drops
    for attempt in range(3):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=60, verify=False)
            if response.status_code == 200 and "ERROR" not in response.text.upper() and "<html" not in response.text.lower() and "<votable" not in response.text.lower():
                df = pd.read_csv(StringIO(response.text))
                print(f"📥 Retrieved {len(df)} records from {catalog_table}.")
                return df
            else:
                print(f"⚠️ API Error response (Attempt {attempt+1}/3): {response.text[:150]}")
        except Exception as e:
            print(f"⚠️ Connection exception on {catalog_table} (Attempt {attempt+1}/3): {e}")
            time.sleep(5)
            
    print(f"❌ Failed to fetch data from {catalog_table} after 3 attempts.")
    return pd.DataFrame()

def filter_planetary_candidates(df):
    """
    Applies W1-W2 color cuts and an estimated outer-system luminosity/size profile 
    to screen out normal background stars and foreground noise.
    """
    print("🔬 Applying infrared color and size-proxy profile filters...")
    
    # Calculate W1 - W2 infrared color index
    df['w1_w2'] = df['w1mpro'] - df['w2mpro']
    
    # 1. Color filter: Target cool sub-stellar/planetary color space (-0.3 < W1-W2 < 0.4)
    color_filtered = df[(df['w1_w2'] > -0.3) & (df['w1_w2'] < 0.4)].copy()
    
    # 2. Size / Absolute Magnitude Proxy:
    # Assuming Planet Nine is a 5-10 Earth-mass body located between 400 and 800 AU,
    # we estimate its absolute magnitude constraint based on expected albedo and thermal emission.
    assumed_distance_au = 600.0
    color_filtered['estimated_abs_mag'] = color_filtered['w1mpro'] - (5 * np.log10(assumed_distance_au) - 5)
    
    # Filter for objects matching the expected absolute magnitude range of a distant ice giant
    size_profile_matched = color_filtered[
        (color_filtered['estimated_abs_mag'] >= -5.0) & 
        (color_filtered['estimated_abs_mag'] <= 2.0)
    ].copy()
    
    print(f"✨ Filtered down to {len(size_profile_matched)} candidates matching planetary color and size profiles.")
    return size_profile_matched

def plot_solar_system_candidate(candidate_row):
    """
    Plots a top-down polar view of the solar system, mapping known outer planets
    and positioning the candidate object based on its sky angle and estimated distance.
    """
    print("🗺️ Generating Top-Down Solar System Mapping Visualization...")
    
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}, figsize=(8, 8))
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

    # Map candidate RA to polar angle
    ra_deg = candidate_row.get('ra', 180.0)
    candidate_angle = np.deg2rad(ra_deg % 360)
    
    # Estimated outer-system distance (AU) based on profile
    estimated_distance_au = 600.0 
    
    ax.scatter(
        candidate_angle, estimated_distance_au, 
        c='#ff4b4b', s=150, marker='*', 
        label='Planet Nine Candidate Profile', edgecolors='yellow', linewidths=1.5
    )
    
    # Styling the polar plot for deep-space aesthetics
    ax.set_rmax(800)
    ax.tick_params(colors='white', labelsize=8)
    ax.grid(color='gray', alpha=0.3, linestyle='--')
    ax.set_title("Outer Solar System Candidate Mapping", color='white', pad=20, fontsize=11)
    
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), facecolor='#1e222b', edgecolor='none', labelcolor='white', fontsize=8)
    
    plot_filename = "planet_nine_solar_system_map.png"
    plt.savefig(plot_filename, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"💾 Solar system map successfully saved as '{plot_filename}'!")

def detect_moving_candidates():
    """
    Cross-matches coordinates between epochs, applies color/size filters, 
    and generates telemetry output and maps.
    """
    df_epoch1 = fetch_epoch_data('allwise_p3as_psd', max_rows=300)
    df_epoch2 = fetch_epoch_data('neowiser_p1bs_psd', max_rows=300)
    
    if df_epoch1.empty or df_epoch2.empty:
        print("❌ Insufficient data returned from one or more epochs.")
        return
        
    print("\n🔍 Running Astropy Sky-Coord Cross-Match across epochs...")
    
    coords1 = SkyCoord(ra=df_epoch1['ra'].values * u.deg, dec=df_epoch1['dec'].values * u.deg)
    coords2 = SkyCoord(ra=df_epoch2['ra'].values * u.deg, dec=df_epoch2['dec'].values * u.deg)
    
    idx, separation, _ = coords1.match_to_catalog_sky(coords2)
    df_epoch1['separation_arcsec'] = separation.arcsec
    
    # Filter for motion threshold (> 2.0 arcseconds of sky drift)
    motion_threshold = 2.0
    moving_candidates = df_epoch1[df_epoch1['separation_arcsec'] > motion_threshold].copy()
    
    # Apply infrared color and planetary size-proxy filters
    refined_candidates = filter_planetary_candidates(moving_candidates)
    
    print(f"🎯 Analysis Complete! Isolated {len(refined_candidates)} high-priority planetary candidates.")
    
    if not refined_candidates.empty:
        print(refined_candidates[['ra', 'dec', 'w1mpro', 'w1_w2', 'separation_arcsec']].head(10))
        refined_candidates.to_csv("planet_nine_moving_candidates.csv", index=False)
        print("\n💾 Saved refined candidates to 'planet_nine_moving_candidates.csv'.")
        
        # Plot top candidate on the solar system map
        plot_solar_system_candidate(refined_candidates.iloc[0])
    else:
        print("📋 No candidates matched the combined motion, color, and size criteria in this batch.")

if __name__ == "__main__":
    detect_moving_candidates()
