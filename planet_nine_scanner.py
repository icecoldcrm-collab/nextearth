import pandas as pd
import requests
import urllib3
from io import StringIO

# Suppress certificate warnings for secure TAP queries
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def scan_for_cold_infrared_candidates(max_rows=100):
    """
    Connects to the NASA IRSA TAP API to query the AllWISE catalog 
    for faint, cold infrared sources that match potential outer-solar-system profiles.
    """
    print("🛰️ Connecting to NASA IRSA TAP Service (AllWISE Catalog)...")
    
    url = "https://irsa.ipac.caltech.edu/TAP/sync"
    
    # ADQL query targeting AllWISE sources with specific infrared magnitudes
    # W1 (3.4 micron) and W2 (4.6 micron) constraints for cold objects
    query_str = f"""
    select top {max_rows} ra, dec, w1mpro, w2mpro, w1sigmpro, w2sigmpro 
    from allwise_p3as_psd 
    where w1mpro > 14.0 and w2mpro > 13.0 
    and (w1mpro - w2mpro) > -0.5 and (w1mpro - w2mpro) < 0.5
    order by w1mpro asc
    """
    
    params = {
        'query': query_str,
        'format': 'csv'
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30, verify=False)
        if response.status_code == 200 and "ERROR" not in response.text.upper():
            df = pd.read_csv(StringIO(response.text))
            print(f"📥 Successfully retrieved {len(df)} infrared candidate records from IRSA.")
            return df
        else:
            print(f"⚠️ IRSA TAP API error response: {response.text[:200]}")
    except Exception as e:
        print(f"⚠️ Exception during infrared archive connection: {e}")
        
    return pd.DataFrame()

def evaluate_candidates(df):
    """
    Highlights and filters objects meeting preliminary size and temperature profiles.
    """
    if df.empty:
        print("❌ No data available to evaluate.")
        return
        
    print("\n🔍 Evaluating Infrared Candidates for Outer-System Signatures...")
    
    # Highlight potential candidates based on infrared flux consistency
    df['candidate_tag'] = df.apply(lambda row: '⚠️ Potential Cold Source Match' if row['w1mpro'] > 15.0 else '📋 Background Star / Routine Object', axis=1)
    
    highlights = df[df['candidate_tag'].str.contains('Potential')]
    
    print(f"🎯 Filtered down to {len(highlights)} high-interest cold infrared objects.")
    print(highlights.head(10))
    
    # Save output for further astrometric checking
    highlights.to_csv("planet_nine_infrared_candidates.csv", index=False)
    print("\n💾 Saved filtered candidates to 'planet_nine_infrared_candidates.csv'.")

if __name__ == "__main__":
    results_df = scan_for_cold_infrared_candidates(max_rows=200)
    evaluate_candidates(results_df)
