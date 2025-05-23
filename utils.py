# Per ogni riga di df, trova la jurisdiction in cui ricadono le coordinate (lat, lon)
def find_jurisdiction(lat, lon, jurisdictions_df):
    for _, row in jurisdictions_df.iterrows():
        if (row['lat_min'] <= lat <= row['lat_max']) and (row['lon_min'] <= lon <= row['lon_max']):
            return row['jurisdiction']
    return None