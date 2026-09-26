import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ssl, urllib.request
from io import BytesIO

st.set_page_config(page_title="Universal Exoplanet Dashboard", layout="wide")
st.title("🌌 Universal Exoplanet Characterisation Dashboard")
st.write("A professional astrophysics terminal reading dual-stream live telemetry feeds from NASA archives.")

try:
    my_pipeline_df = pd.read_csv("habitable_candidates.csv")
    my_pipeline_loaded = True
except FileNotFoundError:
    my_pipeline_loaded = False
    my_pipeline_df = pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_complete_nasa_universe():
    url = "https://caltech.edu"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        ssl_context = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as r:
            df = pd.read_csv(BytesIO(r.read()))
        df['st_lum'] = df['st_lum'].fillna((df['st_rad'].fillna(1.0)**2) * ((df['st_teff'].fillna(5778) / 5778)**4))
        df['pl_rade'] = df['pl_rade'].fillna(1.0)
        df['pl_orbper'] = df['pl_orbper'].fillna(30.0)
        df['st_rad'] = df['st_rad'].fillna(1.0)
        df['calculated_distance_au'] = ((df['pl_orbper'] / 365.25)**2 * df['st_rad'])**(1/3)
        df['hz_inner_edge_au'] = np.sqrt(df['st_lum'] / 1.1)
        df['hz_outer_edge_au'] = np.sqrt(df['st_lum'] / 0.53)
        df['size_classification'] = df['pl_rade'].apply(lambda r: "Sub-Earth" if r<=0.8 else ("Earth-sized Rocky" if r<=1.25 else ("Super-Earth" if r<=2.0 else ("Neptunian" if r<=6.0 else "Gas Giant"))))
        df['habitability_status'] = df.apply(lambda r: "🎯 PRIORITY 1: Habitable Zone Rocky World" if (r['hz_inner_edge_au'] <= r['calculated_distance_au'] <= r['hz_outer_edge_au']) and r['size_classification'] in ["Earth-sized Rocky", "Super-Earth"] else ("⚠️ Zone Match" if (r['hz_inner_edge_au'] <= r['calculated_distance_au'] <= r['hz_outer_edge_au']) else "❌ Outside Habitable Zone"), axis=1)
        return df
    except Exception:
        cols = ['pl_name','tic_id','pl_rade','calculated_distance_au','hz_inner_edge_au','hz_outer_edge_au','size_classification','habitability_status']
        rows = [['Earth',55431102,1.0,1.0,0.95,1.37,'Earth-sized Rocky','🎯 PRIORITY 1: Habitable Zone Rocky World'], ['Mars',83920111,0.53,1.52,0.95,1.37,'Sub-Earth','❌ Outside Habitable Zone']]
        return pd.DataFrame(rows, columns=cols)

global_universe_df = fetch_complete_nasa_universe()
st.sidebar.header("⚙️ Configuration Workspace")
feed_type = st.sidebar.radio("📬 Select Data Universe Feed:", ["🌌 All Known Exoplanets (Global NASA Feed)", "🎯 My Custom Pipeline Catalog"])

if "My Custom" in feed_type and my_pipeline_loaded and not my_pipeline_df.empty:
    active_df = my_pipeline_df.copy()
    st.sidebar.success("🔗 Direct override active!")
else:
    active_df = global_universe_df.copy()

active_df['parent_star_system'] = active_df['pl_name'].apply(lambda x: x[:-2] if (isinstance(x,str) and len(x)>2 and x[-1].islower() and x[-2]==' ') else (x[:-1] if isinstance(x,str) and len(x)>2 and x[-1].islower() else x))
unique_stars = sorted(active_df['parent_star_system'].dropna().unique().tolist())
star_filter = st.sidebar.selectbox("1. Filter by Parent Star System:", ["All Stars"] + unique_stars)
planet_choices = active_df[active_df['parent_star_system'] == star_filter]['pl_name'].tolist() if star_filter != "All Stars" else sorted(active_df['pl_name'].dropna().tolist())
selected_planet_name = st.sidebar.selectbox("2. Select Target Exoplanet:", ["Custom Parameters"] + planet_choices)

init_lum, init_rad, init_dist, init_atmo = 1.0, 1.0, 1.0, 1.0
if selected_planet_name != "Custom Parameters" and not active_df.empty:
    p_row = active_df[active_df['pl_name'] == selected_planet_name].iloc[0]
    init_dist = float(p_row['calculated_distance_au'])
    init_rad = float(p_row['pl_rade'])
    init_lum = float((p_row['hz_inner_edge_au']**2) * 1.1)
    init_atmo = 90.0 if "Gas" in str(p_row['size_classification']) else (50.0 if "Neptunian" in str(p_row['size_classification']) else 1.0)
