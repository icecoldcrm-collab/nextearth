if __name__ == "__main__":
    filename = "habitable_candidates.csv"
    mock_columns = ['pl_name', 'pl_rade', 'size_classification', 'calculated_distance_au', 'hz_inner_edge_au', 'hz_outer_edge_au', 'habitability_status', 'observer_notes']
    
    # Read the batch limit from the GitHub Actions environment variable (default to 3 for local testing)
    batch_limit = int(os.environ.get('BATCH_LIMIT', 3))
    
    targets_pool = fetch_live_unidentified_stream(limit=batch_limit)
    new_logs = []
    
    for target_id in targets_pool:
        candidate_data = analyze_raw_star_light_chart(target_id)
        if candidate_data:
            new_logs.append(candidate_data)
            
    if os.path.exists(filename):
        try:
            existing_df = pd.read_csv(filename)
        except Exception:
            existing_df = pd.DataFrame(columns=mock_columns)
    else:
        mock_data = [
            ['Alpha-Discovery-01b', 3.18, 'Gas Giant', 0.115, 0.953, 1.374, '❌ Outside Habitable Zone', 'Discovery Log Notes: Clean U-shape transit signature flagged.'],
            ['Beta-Survey-12c', 14.59, 'Gas Giant', 0.822, 1.275, 1.837, '❌ Outside Habitable Zone', 'Deep dip, high visual noise profile.'],
            ['Gemma-Candidate-d', 0.30, 'Sub-Earth', 0.051, 0.073, 0.105, '❌ Outside Habitable Zone', 'Micro-transit event isolated on low-mass star.'],
            ['Zeta-Anomaly-e', 6.43, 'Gas Giant', 1.055, 0.795, 1.145, '⚠️ Zone Match (Gas World Configuration)', 'Long-duration single transit event verified.'],
            ['KIC10593626-b (Kepler-22b)', 2.40, 'Super-Earth / Ocean World', 0.849, 0.847, 1.222, '🎯 PRIORITY 1: Habitable Zone Rocky World', 'Calibrated True Baseline Observation Run.']
        ]
        existing_df = pd.DataFrame(mock_data, columns=mock_columns)
        
    if new_logs:
        df_new = pd.DataFrame(new_logs)
        existing_df = existing_df[~existing_df['pl_name'].isin(df_new['pl_name'])]
        existing_df = pd.concat([existing_df, df_new], ignore_index=True)
        
    existing_df.to_csv(filename, index=False)
    print(f"\n💾 High-Throughput Pipeline Complete! Active archive database updated to {len(existing_df)} rows.")
