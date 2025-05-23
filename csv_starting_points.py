import pandas as pd
from typing import List, Optional
from tax_inspector_competition import POI
from utils import find_jurisdiction

def load_jurisdiction_bounds() -> pd.DataFrame:
    
    jurisdiction_bounds = [
        {'jurisdiction': 'J1', 'lat_min': 41.8128, 'lat_max': 41.848600000000005, 'lon_min': 12.43652, 'lon_max': 12.485109999999999},
        {'jurisdiction': 'J2', 'lat_min': 41.8128, 'lat_max': 41.848600000000005, 'lon_min': 12.485109999999999, 'lon_max': 12.5337},
        {'jurisdiction': 'J3', 'lat_min': 41.848600000000005, 'lat_max': 41.8844, 'lon_min': 12.43652, 'lon_max': 12.485109999999999},
        {'jurisdiction': 'J4', 'lat_min': 41.848600000000005, 'lat_max': 41.8844, 'lon_min': 12.485109999999999, 'lon_max': 12.5337},
        {'jurisdiction': 'J5', 'lat_min': 41.8844, 'lat_max': 41.9202, 'lon_min': 12.43652, 'lon_max': 12.485109999999999},
        {'jurisdiction': 'J6', 'lat_min': 41.8844, 'lat_max': 41.9202, 'lon_min': 12.485109999999999, 'lon_max': 12.5337}
    ]
    
    return pd.DataFrame(jurisdiction_bounds)

def create_poi_from_coordinates(lat: float, lon: float, poi_id: int, 
                               jurisdictions_df: pd.DataFrame,
                               default_poi_type: str = "starting_point",
                               default_fee_value: float = 0.0) -> POI:

    jurisdiction = find_jurisdiction(lat, lon, jurisdictions_df)
    
    if jurisdiction is None:
        # Se non trova giurisdizione, assegna una di default
        jurisdiction = "J1"
        print(f"Coordinate ({lat}, {lon}) non ricadono in nessuna giurisdizione, assegnata J1")
    
    return POI(
        id=poi_id,
        lat=lat,
        lon=lon,
        poi_type=default_poi_type,
        fee_value=default_fee_value,
        jurisdiction=jurisdiction
    )

def load_starting_points_from_coordinates_csv(csv_path: str, 
                                            poi_type: str = "starting_point",
                                            fee_value: float = 0.0) -> List[POI]:
    try:
        # Carica il CSV
        df = pd.read_csv(csv_path)
        
        # Verifica colonne richieste
        required_columns = ['lat', 'lon']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colonne mancanti nel CSV: {missing_columns}")
        
        # Carica confini giurisdizioni
        jurisdictions_df = load_jurisdiction_bounds()
        
        # Ordina per giorno se presente
        if 'day' in df.columns:
            df = df.sort_values('day')
        
        # Crea POI per ogni riga
        starting_points = []
        for idx, row in df.iterrows():
            poi_id = 9000 + idx  # ID univoco per starting points
            
            poi = create_poi_from_coordinates(
                lat=row['lat'],
                lon=row['lon'],
                poi_id=poi_id,
                jurisdictions_df=jurisdictions_df,
                default_poi_type=poi_type,
                default_fee_value=fee_value
            )
            
            starting_points.append(poi)
        
        print(f"Caricati {len(starting_points)} punti di partenza da '{csv_path}'")
        
        # Stampa riepilogo giurisdizioni
        jurisdiction_counts = {}
        for poi in starting_points:
            jurisdiction_counts[poi.jurisdiction] = jurisdiction_counts.get(poi.jurisdiction, 0) + 1
        
        print("Distribuzione per giurisdizione:")
        for jurisdiction, count in sorted(jurisdiction_counts.items()):
            print(f"   {jurisdiction}: {count} punti")
        
        return starting_points
        
    except Exception as e:
        print(f"Errore nel caricamento del CSV '{csv_path}': {e}")
        return []

def save_starting_points_to_detailed_csv(starting_points: List[POI], output_path: str):

    data = []
    for i, poi in enumerate(starting_points, 1):
        data.append({
            'day': i,
            'poi_id': poi.id,
            'lat': poi.lat,
            'lon': poi.lon,
            'poi_type': poi.poi_type,
            'fee_value': poi.fee_value,
            'jurisdiction': poi.jurisdiction
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"Punti di partenza dettagliati salvati in '{output_path}'")

def create_competition_with_coordinate_starting_points(dataset_path: str, 
                                                     coordinates_csv_path: str,
                                                     poi_type: str = "starting_point"):

    from interactive_competition import MultiInspectorCompetition
    
    # Carica starting points dalle coordinate
    starting_points = load_starting_points_from_coordinates_csv(
        coordinates_csv_path, 
        poi_type=poi_type
    )
    
    if not starting_points:
        print("Impossibile caricare starting points, abort.")
        return None
    
    # Crea competizione
    competition = MultiInspectorCompetition(dataset_path)
    
    # Imposta starting points
    competition.set_fixed_starting_points(starting_points)
    
    return competition

if __name__ == "__main__":
    print("CSV STARTING POINTS MANAGER")
    print("="*40)
    
    # Test di caricamento
    print(f"\nTest di caricamento:")
    starting_points = load_starting_points_from_coordinates_csv('starting_coordinates_example.csv')
    
    if starting_points:
        print(f"\nDettagli punti di partenza:")
        for i, poi in enumerate(starting_points, 1):
            print(f"  Giorno {i}: ({poi.lat}, {poi.lon}) -> {poi.jurisdiction}")
        
        # Salva versione dettagliata
        save_starting_points_to_detailed_csv(starting_points, 'starting_points_detailed.csv')