import pandas as pd
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
import random

@dataclass
class POI:
    """Rappresenta un Point of Interest"""
    id: int
    lat: float
    lon: float
    poi_type: str
    fee_value: float
    jurisdiction: str

@dataclass
class RouteSegment:
    """Rappresenta un segmento del percorso"""
    from_poi: POI
    to_poi: POI
    distance_km: float
    travel_time_minutes: float

@dataclass
class DayRoute:
    """Rappresenta il percorso completo di una giornata"""
    day: int
    starting_point: POI
    visited_pois: List[POI]
    total_distance_km: float
    total_time_minutes: float
    total_fee_collected: float
    jurisdiction: str

class DistanceCalculator:
    """Calcola distanze tra coordinate GPS usando la formula di Haversine"""
    
    @staticmethod
    def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcola la distanza in km tra due punti GPS usando la formula di Haversine
        """
        R = 6371  # Raggio della Terra in km
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

    @staticmethod
    def walking_time_minutes(distance_km: float, walking_speed_kmh: float = 5.0) -> float:
        """
        Calcola il tempo di camminata in minuti
        Velocità media di camminata: 5 km/h
        """
        return (distance_km / walking_speed_kmh) * 60

class RouteOptimizer:
    """Ottimizza i percorsi utilizzando la strategia high_value"""
    
    def __init__(self, pois: List[POI]):
        self.pois = pois
        self.distance_calc = DistanceCalculator()
        self.jurisdictions = self._group_by_jurisdiction()
        
    def _group_by_jurisdiction(self) -> Dict[str, List[POI]]:
        """Raggruppa i POIs per giurisdizione"""
        jurisdictions = {}
        for poi in self.pois:
            if poi.jurisdiction not in jurisdictions:
                jurisdictions[poi.jurisdiction] = []
            jurisdictions[poi.jurisdiction].append(poi)
        return jurisdictions
    
    def calculate_route_metrics(self, starting_point: POI, route_pois: List[POI]) -> Tuple[float, float, float]:
        """
        Calcola metriche del percorso: distanza totale, tempo totale, profitto totale
        """
        if not route_pois:
            return 0.0, 0.0, 0.0
            
        total_distance = 0.0
        total_time = 0.0
        total_fee = 0.0
        
        # Dal punto di partenza al primo POI
        current_poi = starting_point
        
        for poi in route_pois:
            distance = self.distance_calc.haversine_distance(
                current_poi.lat, current_poi.lon, poi.lat, poi.lon
            )
            travel_time = self.distance_calc.walking_time_minutes(distance)
            
            total_distance += distance
            total_time += travel_time + 5  # 5 minuti per fermata
            total_fee += poi.fee_value
            
            current_poi = poi
        
        # Ritorno al punto di partenza
        if route_pois:
            return_distance = self.distance_calc.haversine_distance(
                current_poi.lat, current_poi.lon, starting_point.lat, starting_point.lon
            )
            return_time = self.distance_calc.walking_time_minutes(return_distance)
            total_distance += return_distance
            total_time += return_time
        
        return total_distance, total_time, total_fee
    
    def is_valid_route(self, starting_point: POI, route_pois: List[POI], 
                      max_time_minutes: int = 180, max_pois: int = 8) -> bool:
        """Verifica se un percorso rispetta i vincoli"""
        if len(route_pois) > max_pois:
            return False
            
        # Verifica giurisdizione
        jurisdiction = starting_point.jurisdiction
        for poi in route_pois:
            if poi.jurisdiction != jurisdiction:
                return False
        
        # Verifica tempo
        _, total_time, _ = self.calculate_route_metrics(starting_point, route_pois)
        return total_time <= max_time_minutes
    
    def optimize_route_high_value(self, starting_point: POI, max_time_minutes: int = 180, 
                                 max_pois: int = 8) -> List[POI]:
        """
        Strategia che privilegia POIs con valore alto
        Ordina i POIs per valore decrescente e li aggiunge se rispettano i vincoli
        """
        jurisdiction_pois = self.jurisdictions.get(starting_point.jurisdiction, [])
        available_pois = [poi for poi in jurisdiction_pois if poi.id != starting_point.id]
        
        # Ordina per valore decrescente
        available_pois.sort(key=lambda poi: poi.fee_value, reverse=True)
        
        # Prova ad aggiungere POIs in ordine di valore
        selected_pois = []
        for poi in available_pois:
            test_route = selected_pois + [poi]
            if (len(test_route) <= max_pois and 
                self.is_valid_route(starting_point, test_route, max_time_minutes, max_pois)):
                selected_pois.append(poi)
        
        return selected_pois

class CompetitionSimulator:
    """Simula la competizione degli accertatori usando la strategia high_value"""
    
    def __init__(self, dataset_path: str):
        self.pois = self._load_pois(dataset_path)
        self.optimizer = RouteOptimizer(self.pois)
        self.jurisdictions = list(self.optimizer.jurisdictions.keys())
        
    def _load_pois(self, dataset_path: str) -> List[POI]:
        """Carica i POIs dal dataset CSV"""
        df = pd.read_csv(dataset_path)
        pois = []
        
        for _, row in df.iterrows():
            poi = POI(
                id=row['id'],
                lat=row['lat'],
                lon=row['lon'],
                poi_type=row['poi_type'],
                fee_value=row['fee_value'],
                jurisdiction=row['jurisdiction']
            )
            pois.append(poi)
        
        return pois
    
    def get_random_starting_points(self, num_days: int = 5) -> List[POI]:
        """Seleziona punti di partenza casuali per ogni giornata"""
        starting_points = []
        
        for day in range(num_days):
            # Seleziona una giurisdizione casuale
            jurisdiction = random.choice(self.jurisdictions)
            jurisdiction_pois = self.optimizer.jurisdictions[jurisdiction]
            
            # Seleziona un POI casuale come punto di partenza
            starting_point = random.choice(jurisdiction_pois)
            starting_points.append(starting_point)
        
        return starting_points
    
    def simulate_inspector_competition(self, num_days: int = 5) -> List[DayRoute]:
        """
        Simula la competizione di un accertatore per tutte le giornate usando la strategia high_value
        """
        starting_points = self.get_random_starting_points(num_days)
        day_routes = []
        
        for day, starting_point in enumerate(starting_points, 1):
            print(f"\n=== GIORNATA {day} ===")
            print(f"Punto di partenza: {starting_point.poi_type} (ID: {starting_point.id})")
            print(f"Giurisdizione: {starting_point.jurisdiction}")
            print(f"Coordinate: ({starting_point.lat:.4f}, {starting_point.lon:.4f})")
            
            # Ottimizza il percorso usando la strategia high_value
            optimal_pois = self.optimizer.optimize_route_high_value(starting_point)
            
            # Calcola metriche del percorso
            distance, time, fee = self.optimizer.calculate_route_metrics(starting_point, optimal_pois)
            
            day_route = DayRoute(
                day=day,
                starting_point=starting_point,
                visited_pois=optimal_pois,
                total_distance_km=distance,
                total_time_minutes=time,
                total_fee_collected=fee,
                jurisdiction=starting_point.jurisdiction
            )
            
            day_routes.append(day_route)
            
            # Stampa risultati della giornata
            print(f"POIs visitati: {len(optimal_pois)}")
            print(f"Distanza totale: {distance:.2f} km")
            print(f"Tempo totale: {time:.1f} minuti ({time/60:.1f} ore)")
            print(f"Tasse raccolte: €{fee:.2f}")
            
            if optimal_pois:
                print("Percorso dettagliato:")
                current = starting_point
                for i, poi in enumerate(optimal_pois, 1):
                    dist = self.optimizer.distance_calc.haversine_distance(
                        current.lat, current.lon, poi.lat, poi.lon
                    )
                    walk_time = self.optimizer.distance_calc.walking_time_minutes(dist)
                    print(f"  {i}. {poi.poi_type} (ID: {poi.id}) - "
                          f"Distanza: {dist:.2f}km, Tempo: {walk_time:.1f}min, "
                          f"Valore: €{poi.fee_value:.2f}")
                    current = poi
                
                # Ritorno
                return_dist = self.optimizer.distance_calc.haversine_distance(
                    current.lat, current.lon, starting_point.lat, starting_point.lon
                )
                return_time = self.optimizer.distance_calc.walking_time_minutes(return_dist)
                print(f"  Ritorno: {return_dist:.2f}km, {return_time:.1f}min")
        
        return day_routes
    
    def print_competition_summary(self, day_routes: List[DayRoute]):
        """Stampa il riassunto della competizione"""
        print("\n" + "="*60)
        print("RIASSUNTO COMPETIZIONE (Strategia High Value)")
        print("="*60)
        
        total_fee = sum(route.total_fee_collected for route in day_routes)
        total_distance = sum(route.total_distance_km for route in day_routes)
        total_time = sum(route.total_time_minutes for route in day_routes)
        total_pois = sum(len(route.visited_pois) for route in day_routes)
        
        print(f"Totale 5 giornate:")
        print(f"  - Tasse raccolte: €{total_fee:.2f}")
        print(f"  - Distanza percorsa: {total_distance:.2f} km")
        print(f"  - Tempo impiegato: {total_time:.1f} minuti ({total_time/60:.1f} ore)")
        print(f"  - POIs visitati: {total_pois}")
        print(f"  - Media per giornata: €{total_fee/5:.2f}")
        
        print(f"\nDettaglio per giornata:")
        for route in day_routes:
            print(f"  Giorno {route.day} ({route.jurisdiction}): "
                  f"€{route.total_fee_collected:.2f} - "
                  f"{len(route.visited_pois)} POIs - "
                  f"{route.total_time_minutes:.1f} min")
        
        # Statistiche per giurisdizione
        jurisdiction_stats = {}
        for route in day_routes:
            if route.jurisdiction not in jurisdiction_stats:
                jurisdiction_stats[route.jurisdiction] = {'fee': 0, 'days': 0}
            jurisdiction_stats[route.jurisdiction]['fee'] += route.total_fee_collected
            jurisdiction_stats[route.jurisdiction]['days'] += 1
        
        print(f"\nPerformance per giurisdizione:")
        for jurisdiction, stats in sorted(jurisdiction_stats.items()):
            avg_fee = stats['fee'] / stats['days']
            print(f"  {jurisdiction}: €{stats['fee']:.2f} totale, €{avg_fee:.2f} media/giorno")

def main():
    print("COMPETIZIONE ACCERTATORI SIAE (Strategia High Value)")
    print("="*55)
    
    # Inizializza il simulatore
    simulator = CompetitionSimulator('dataset.csv')
    
    print(f"Dataset caricato: {len(simulator.pois)} POIs")
    print(f"Giurisdizioni disponibili: {len(simulator.jurisdictions)}")
    print(f"POIs per giurisdizione:")
    for jurisdiction, pois in simulator.optimizer.jurisdictions.items():
        total_value = sum(poi.fee_value for poi in pois)
        print(f"  {jurisdiction}: {len(pois)} POIs, Valore totale: €{total_value:.2f}")
    
    # Simula la competizione usando la strategia high_value
    print(f"\nInizio simulazione competizione con strategia High Value...")
    day_routes = simulator.simulate_inspector_competition(num_days=5)
    
    # Stampa riassunto
    simulator.print_competition_summary(day_routes)
    
    # Salva risultati in CSV
    results_data = []
    for route in day_routes:
        for i, poi in enumerate(route.visited_pois):
            results_data.append({
                'day': route.day,
                'visit_order': i + 1,
                'poi_id': poi.id,
                'poi_type': poi.poi_type,
                'fee_value': poi.fee_value,
                'jurisdiction': poi.jurisdiction,
                'lat': poi.lat,
                'lon': poi.lon
            })
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv('competition_results.csv', index=False)
    print(f"\nRisultati salvati in 'competition_results.csv'")

if __name__ == "__main__":
    main()