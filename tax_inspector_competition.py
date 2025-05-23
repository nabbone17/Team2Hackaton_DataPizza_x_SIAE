#!/usr/bin/env python3
"""
Sistema di Competizione per Accertatori Fiscali
================================================

Simula una competizione di 5 giornate dove gli accertatori devono ottimizzare
i loro percorsi per massimizzare il profitto raccolto dai POIs, rispettando
vari vincoli temporali e territoriali.

Vincoli:
- 3 ore massime per giornata
- Massimo 8 POIs per giornata
- 5 minuti per fermata
- Solo una giurisdizione per giornata
- Ritorno al punto di partenza obbligatorio
- Spostamento a piedi
"""

import pandas as pd
import numpy as np
import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from itertools import combinations
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
    """Ottimizza i percorsi per massimizzare il profitto"""
    
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
    
    def optimize_route_greedy(self, starting_point: POI, max_time_minutes: int = 180, 
                             max_pois: int = 8) -> List[POI]:
        """
        Algoritmo greedy per ottimizzazione del percorso:
        Seleziona sempre il POI più vicino con il miglior rapporto valore/tempo
        """
        jurisdiction_pois = self.jurisdictions.get(starting_point.jurisdiction, [])
        available_pois = [poi for poi in jurisdiction_pois if poi.id != starting_point.id]
        
        selected_pois = []
        current_pos = starting_point
        
        while len(selected_pois) < max_pois and available_pois:
            best_poi = None
            best_score = -1
            
            for poi in available_pois:
                # Testa se aggiungere questo POI è valido
                test_route = selected_pois + [poi]
                if not self.is_valid_route(starting_point, test_route, max_time_minutes, max_pois):
                    continue
                
                # Calcola score (valore/tempo)
                distance = self.distance_calc.haversine_distance(
                    current_pos.lat, current_pos.lon, poi.lat, poi.lon
                )
                travel_time = self.distance_calc.walking_time_minutes(distance) + 5
                
                if travel_time > 0:
                    score = poi.fee_value / travel_time
                    if score > best_score:
                        best_score = score
                        best_poi = poi
            
            if best_poi is None:
                break
                
            selected_pois.append(best_poi)
            available_pois.remove(best_poi)
            current_pos = best_poi
        
        return selected_pois
    
    def optimize_route_genetic(self, starting_point: POI, max_time_minutes: int = 180, 
                              max_pois: int = 8, generations: int = 100) -> List[POI]:
        """
        Algoritmo genetico per ottimizzazione del percorso (più sofisticato)
        """
        jurisdiction_pois = self.jurisdictions.get(starting_point.jurisdiction, [])
        available_pois = [poi for poi in jurisdiction_pois if poi.id != starting_point.id]
        
        if len(available_pois) <= max_pois:
            # Se abbiamo pochi POIs, testa tutte le combinazioni valide
            return self._brute_force_optimization(starting_point, available_pois, max_time_minutes, max_pois)
        
        # Implementazione semplificata dell'algoritmo genetico
        population_size = min(50, len(available_pois) * 2)
        population = []
        
        # Crea popolazione iniziale
        for _ in range(population_size):
            route_size = random.randint(1, min(max_pois, len(available_pois)))
            route = random.sample(available_pois, route_size)
            if self.is_valid_route(starting_point, route, max_time_minutes, max_pois):
                population.append(route)
        
        # Se non ci sono route valide, usa greedy
        if not population:
            return self.optimize_route_greedy(starting_point, max_time_minutes, max_pois)
        
        # Evoluzione
        for generation in range(generations):
            # Valuta fitness
            fitness_scores = []
            for route in population:
                _, _, fee = self.calculate_route_metrics(starting_point, route)
                fitness_scores.append(fee)
            
            # Selezione migliori
            sorted_indices = sorted(range(len(population)), key=lambda i: fitness_scores[i], reverse=True)
            elite_size = max(1, population_size // 4)
            elite = [population[i] for i in sorted_indices[:elite_size]]
            
            # Crea nuova popolazione
            new_population = elite[:]
            
            while len(new_population) < population_size:
                # Crossover
                parent1, parent2 = random.sample(elite, 2)
                child = self._crossover(parent1, parent2)
                
                # Mutazione
                if random.random() < 0.1:
                    child = self._mutate(child, available_pois)
                
                if self.is_valid_route(starting_point, child, max_time_minutes, max_pois):
                    new_population.append(child)
                elif len(new_population) < population_size:
                    # Se il figlio non è valido, aggiungi un genitore
                    new_population.append(random.choice(elite))
            
            population = new_population
        
        # Restituisci la migliore route
        best_route = max(population, key=lambda route: self.calculate_route_metrics(starting_point, route)[2])
        return best_route
    
    def _brute_force_optimization(self, starting_point: POI, available_pois: List[POI], 
                                 max_time_minutes: int, max_pois: int) -> List[POI]:
        """Forza bruta per piccoli insiemi di POIs"""
        best_route = []
        best_fee = 0
        
        for r in range(1, min(max_pois + 1, len(available_pois) + 1)):
            for combo in combinations(available_pois, r):
                route = list(combo)
                if self.is_valid_route(starting_point, route, max_time_minutes, max_pois):
                    _, _, fee = self.calculate_route_metrics(starting_point, route)
                    if fee > best_fee:
                        best_fee = fee
                        best_route = route
        
        return best_route
    
    def _crossover(self, parent1: List[POI], parent2: List[POI]) -> List[POI]:
        """Crossover genetico tra due percorsi"""
        # Usa gli ID dei POI per evitare problemi di hashing
        all_poi_ids = set([poi.id for poi in parent1] + [poi.id for poi in parent2])
        
        # Crea un dizionario per accesso rapido agli oggetti POI
        poi_dict = {}
        for poi in parent1 + parent2:
            poi_dict[poi.id] = poi
        
        # Seleziona POI casuali per il figlio
        child_size = random.randint(1, min(8, len(all_poi_ids)))
        selected_ids = random.sample(list(all_poi_ids), child_size)
        
        return [poi_dict[poi_id] for poi_id in selected_ids]
    
    def _mutate(self, route: List[POI], available_pois: List[POI]) -> List[POI]:
        """Mutazione genetica di un percorso"""
        if not route:
            return route
            
        # Crea una copia della route per evitare modifiche indesiderate
        route = route.copy()
        mutation_type = random.choice(['add', 'remove', 'replace'])
        
        if mutation_type == 'add' and len(route) < 8:
            route_ids = {poi.id for poi in route}
            unused_pois = [poi for poi in available_pois if poi.id not in route_ids]
            if unused_pois:
                route.append(random.choice(unused_pois))
        elif mutation_type == 'remove' and len(route) > 1:
            route.pop(random.randint(0, len(route) - 1))
        elif mutation_type == 'replace' and route:
            route_ids = {poi.id for poi in route}
            unused_pois = [poi for poi in available_pois if poi.id not in route_ids]
            if unused_pois:
                idx = random.randint(0, len(route) - 1)
                route[idx] = random.choice(unused_pois)
        
        return route

class CompetitionSimulator:
    """Simula la competizione degli accertatori"""
    
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
    
    def simulate_inspector_competition(self, num_days: int = 5, 
                                     optimization_method: str = 'greedy') -> List[DayRoute]:
        """
        Simula la competizione di un accertatore per tutte le giornate
        """
        starting_points = self.get_random_starting_points(num_days)
        day_routes = []
        
        for day, starting_point in enumerate(starting_points, 1):
            print(f"\n=== GIORNATA {day} ===")
            print(f"Punto di partenza: {starting_point.poi_type} (ID: {starting_point.id})")
            print(f"Giurisdizione: {starting_point.jurisdiction}")
            print(f"Coordinate: ({starting_point.lat:.4f}, {starting_point.lon:.4f})")
            
            # Ottimizza il percorso
            if optimization_method == 'genetic':
                optimal_pois = self.optimizer.optimize_route_genetic(starting_point)
            else:
                optimal_pois = self.optimizer.optimize_route_greedy(starting_point)
            
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
        print("RIASSUNTO COMPETIZIONE")
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
    print("COMPETIZIONE ACCERTATORI SIAE")
    print("="*50)
    
    # Inizializza il simulatore
    simulator = CompetitionSimulator('dataset.csv')
    
    print(f"Dataset caricato: {len(simulator.pois)} POIs")
    print(f"Giurisdizioni disponibili: {len(simulator.jurisdictions)}")
    print(f"POIs per giurisdizione:")
    for jurisdiction, pois in simulator.optimizer.jurisdictions.items():
        total_value = sum(poi.fee_value for poi in pois)
        print(f"  {jurisdiction}: {len(pois)} POIs, Valore totale: €{total_value:.2f}")
    
    # Simula la competizione
    print(f"\nInizio simulazione competizione...")
    day_routes = simulator.simulate_inspector_competition(
        num_days=5, 
        optimization_method='greedy'  # Cambia in 'genetic' per algoritmo più sofisticato
    )
    
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
    print(f"\n📄 Risultati salvati in 'competition_results.csv'")

if __name__ == "__main__":
    main() 