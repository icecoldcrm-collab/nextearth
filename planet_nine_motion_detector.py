import pandas as pd
import numpy as np
import requests
from io import StringIO
from astropy.coordinates import SkyCoord
import astropy.units as u
import urllib3

# Suppress certificate warnings for secure TAP queries
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_epoch_data(catalog_table, max_rows=500):
    """
    Queries an infrared catalog table from the NASA IRSA TAP service.
    """
    print(f"🛰️ Querying NASA IRSA TAP for catalog: {catalog_table}...")
    url = "https://irsa.ipac.caltech.edu/TAP/sync"
    
    # Query coordinates and infrared magnitudes for faint cold targets
    query_str = f"""
    select top {max_rows} ra, dec, w1mpro, w2mpro 
    from {catalog_table} 
    where w1mpro > 14.0 and w2mpro > 13.0
    order by w1mpro asc
    """
    
    params = {'query': query_str, 'format': 'csv'}
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
        if response.status_code == 200 and "ERROR" not in response.text.upper():
            df = pd.read_csv(StringIO(response.text))
            print(f"📥 Retrieved {len(df)} records from {catalog_table}.")
            return df
        else:
            print(f"⚠️ API Error: {response.text[:150]}</h2>")
    except Exception as e:
        print(f"⚠️ Connection exception: {e}")
        
    return pd.DataFrame()

def detect_moving_candidates():
    """
    Cross-matches coordinates between epochs to find objects with significant sky drift.
    """
    # Epoch 1: AllWISE baseline (circa 2010)
    df_epoch1 = fetch_epoch_data('allwise_p3as_psd', max_rows=300)
    # Epoch 2: NEOWISE Reactivation baseline (later years)
    df_epoch2 = fetch_epoch_data('neowise_p1bs_psd', max_rows=300)
    
    if df_epoch1.empty or df_epoch2.empty:
        print("❌ Insufficient data returned from one or more epochs.")
        return
        
    print("\n🔍 Running Astropy Sky-Coord Cross-Match across epochs...")
    
    # Convert coordinates into Astropy SkyCoord objects
    coords1 = SkyCoord(ra=df_epoch1['ra'].values * u.deg, dec=df_epoch1['dec'].values * u.deg)
    coords2 = SkyCoord(ra=df_epoch2['ra'].values * u.deg, dec=df_epoch2['dec'].values * u.deg)
    
    # Find the nearest neighbor in Epoch 2 for every object in Epoch 1
    idx, separation, _ = coords1.match_to_catalog_sky(coords2)
    
    # Attach separation distances (converted to arcseconds) back to the dataframe
    df_epoch1['separation_arcsec'] = separation.arcsec
    
    # Filter for objects that moved more than a threshold (e.g., > 2.0 arcseconds), 
    # indicating a potential moving solar system source rather than a static star.
    motion_threshold = 2.0  # arcseconds
    moving_candidates = df_epoch1[df_epoch1['separation_arcsec'] > motion_threshold].copy()
    
    print(f"🎯 Analysis Complete! Isolated {len(moving_candidates)} objects exhibiting multi-epoch sky drift.")
    
    if not moving_candidates.empty:
        print(moving_candidates[['ra', 'dec', 'w1mpro', 'separation_arcsec']].head(10))
        moving_candidates.to_csv("planet_nine_moving_candidates.csv", index=False)
        print("\n💾 Saved moving candidates to 'planet_nine_moving_candidates.csv'.")
    else:
        print("📋 No significant motion detected above the threshold in this sample batch.")

if __name__ == "__main__":
    detect_moving_candidates()
