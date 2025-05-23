#!/usr/bin/env python3
"""
Sistema Interattivo per Competizione Accertatori
================================================

Permette di far competere più accertatori con strategie diverse
e di confrontare i loro risultati.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import random
import json
from tax_inspector_competition import CompetitionSimulator, DayRoute, POI
import matplotlib.pyplot as plt
import seaborn as sns

class Inspector:
    """Rappresenta un accertatore con la sua strategia"""
    
    def __init__(self, name: str, strategy: str = 'greedy', seed: int = None):
        self.name = name
        self.strategy = strategy
        self.seed = seed
        self.total_earnings = 0.0
        self.day_routes = []
        
    def __str__(self):
        return f"Accertatore {self.name} (Strategia: {self.strategy})"

class MultiInspectorCompetition:
    """Gestisce una competizione tra più accertatori"""
    
    def __init__(self, dataset_path: str):
        self.simulator = CompetitionSimulator(dataset_path)
        self.inspectors = []
        self.competition_results = {}
        self.fixed_starting_points = None
        
    def add_inspector(self, name: str, strategy: str = 'greedy', seed: int = None):
        """Aggiunge un accertatore alla competizione"""
        inspector = Inspector(name, strategy, seed)
        self.inspectors.append(inspector)
        print(f"Aggiunto {inspector}")
        
    def set_fixed_starting_points(self, starting_points: List[POI] = None):
        """Imposta punti di partenza fissi per tutti gli accertatori"""
        if starting_points is None:
            # Genera punti di partenza casuali che saranno usati da tutti
            random.seed(42)  # Per riproducibilità
            self.fixed_starting_points = self.simulator.get_random_starting_points(5)
        else:
            self.fixed_starting_points = starting_points
            
        print(f"📍 Punti di partenza fissi impostati:")
        for i, point in enumerate(self.fixed_starting_points, 1):
            print(f"  Giorno {i}: {point.poi_type} in {point.jurisdiction} (ID: {point.id})")
    
    def run_competition(self, num_days: int = 5):
        """Esegue la competizione per tutti gli accertatori"""
        if not self.fixed_starting_points:
            self.set_fixed_starting_points()
            
        print(f"\nINIZIO COMPETIZIONE CON {len(self.inspectors)} ACCERTATORI")
        print("="*60)
        
        for inspector in self.inspectors:
            print(f"\nSimulazione per {inspector.name} ({inspector.strategy})")
            
            # Imposta seed se specificato
            if inspector.seed:
                random.seed(inspector.seed)
                
            # Simula usando i punti di partenza fissi
            day_routes = self._simulate_with_fixed_points(inspector, self.fixed_starting_points)
            
            inspector.day_routes = day_routes
            inspector.total_earnings = sum(route.total_fee_collected for route in day_routes)
            
            self.competition_results[inspector.name] = {
                'inspector': inspector,
                'total_earnings': inspector.total_earnings,
                'day_routes': day_routes,
                'strategy': inspector.strategy
            }
            
            print(f"Totale raccolto: €{inspector.total_earnings:.2f}")
    
    def _simulate_with_fixed_points(self, inspector: Inspector, starting_points: List[POI]) -> List[DayRoute]:
        """Simula la competizione con punti di partenza fissi"""
        day_routes = []
        
        for day, starting_point in enumerate(starting_points, 1):
            # Ottimizza il percorso secondo la strategia dell'accertatore
            if inspector.strategy == 'genetic':
                optimal_pois = self.simulator.optimizer.optimize_route_genetic(starting_point)
            elif inspector.strategy == 'greedy':
                optimal_pois = self.simulator.optimizer.optimize_route_greedy(starting_point)
            elif inspector.strategy == 'random':
                optimal_pois = self._random_strategy(starting_point)
            elif inspector.strategy == 'high_value':
                optimal_pois = self._high_value_strategy(starting_point)
            else:
                optimal_pois = self.simulator.optimizer.optimize_route_greedy(starting_point)
            
            # Calcola metriche del percorso
            distance, time, fee = self.simulator.optimizer.calculate_route_metrics(starting_point, optimal_pois)
            
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
        
        return day_routes
    
    def _random_strategy(self, starting_point: POI) -> List[POI]:
        """Strategia casuale (per confronto)"""
        jurisdiction_pois = self.simulator.optimizer.jurisdictions.get(starting_point.jurisdiction, [])
        available_pois = [poi for poi in jurisdiction_pois if poi.id != starting_point.id]
        
        # Seleziona POIs casuali che rispettano i vincoli
        max_attempts = 100
        for _ in range(max_attempts):
            num_pois = random.randint(1, min(8, len(available_pois)))
            random_pois = random.sample(available_pois, num_pois)
            
            if self.simulator.optimizer.is_valid_route(starting_point, random_pois):
                return random_pois
        
        return []
    
    def _high_value_strategy(self, starting_point: POI) -> List[POI]:
        """Strategia che privilegia POIs con valore alto"""
        jurisdiction_pois = self.simulator.optimizer.jurisdictions.get(starting_point.jurisdiction, [])
        available_pois = [poi for poi in jurisdiction_pois if poi.id != starting_point.id]
        
        # Ordina per valore decrescente
        available_pois.sort(key=lambda poi: poi.fee_value, reverse=True)
        
        # Prova ad aggiungere POIs in ordine di valore
        selected_pois = []
        for poi in available_pois:
            test_route = selected_pois + [poi]
            if (len(test_route) <= 8 and 
                self.simulator.optimizer.is_valid_route(starting_point, test_route)):
                selected_pois.append(poi)
        
        return selected_pois
    
    def print_competition_results(self):
        """Stampa i risultati della competizione"""
        if not self.competition_results:
            print("Nessuna competizione eseguita!")
            return
            
        print("\n" + "="*70)
        print("RISULTATI FINALI DELLA COMPETIZIONE")
        print("="*70)
        
        # Ordina per guadagni totali
        sorted_results = sorted(
            self.competition_results.values(), 
            key=lambda x: x['total_earnings'], 
            reverse=True
        )
        
        print(f"\nCLASSIFICA FINALE:")
        for i, result in enumerate(sorted_results, 1):
            inspector = result['inspector']
            print(f"{inspector.name} ({inspector.strategy}): €{result['total_earnings']:.2f}")  
        
        # Dettagli per ogni accertatore
        print(f"\nDETTAGLI PER ACCERTATORE:")
        for result in sorted_results:
            inspector = result['inspector']
            routes = result['day_routes']
            
            print(f"\n{inspector.name} ({inspector.strategy}):")
            print(f"   Totale: €{result['total_earnings']:.2f}")
            print(f"   POIs visitati: {sum(len(route.visited_pois) for route in routes)}")
            print(f"   Distanza totale: {sum(route.total_distance_km for route in routes):.2f} km")
            print(f"   Tempo totale: {sum(route.total_time_minutes for route in routes):.1f} min")
            
            print(f"   Per giornata:")
            for route in routes:
                efficiency = route.total_fee_collected / max(route.total_time_minutes, 1) * 60
                print(f"    Giorno {route.day}: €{route.total_fee_collected:.2f} "
                      f"({len(route.visited_pois)} POIs, {route.total_time_minutes:.1f}min, "
                      f"€{efficiency:.1f}/ora)")
    
    def generate_detailed_report(self, output_file: str = 'competition_report.json'):
        """Genera un report dettagliato in formato JSON"""
        report = {
            'competition_date': pd.Timestamp.now().isoformat(),
            'total_inspectors': len(self.inspectors),
            'starting_points': [
                {
                    'day': i + 1,
                    'poi_id': point.id,
                    'poi_type': point.poi_type,
                    'jurisdiction': point.jurisdiction,
                    'lat': point.lat,
                    'lon': point.lon
                }
                for i, point in enumerate(self.fixed_starting_points)
            ],
            'results': {}
        }
        
        for name, result in self.competition_results.items():
            inspector_data = {
                'strategy': result['strategy'],
                'total_earnings': result['total_earnings'],
                'daily_results': []
            }
            
            for route in result['day_routes']:
                day_data = {
                    'day': route.day,
                    'jurisdiction': route.jurisdiction,
                    'pois_visited': len(route.visited_pois),
                    'total_distance_km': route.total_distance_km,
                    'total_time_minutes': route.total_time_minutes,
                    'fee_collected': route.total_fee_collected,
                    'efficiency_euro_per_hour': (route.total_fee_collected / max(route.total_time_minutes, 1)) * 60,
                    'visited_pois': [
                        {
                            'poi_id': poi.id,
                            'poi_type': poi.poi_type,
                            'fee_value': poi.fee_value,
                            'lat': poi.lat,
                            'lon': poi.lon
                        }
                        for poi in route.visited_pois
                    ]
                }
                inspector_data['daily_results'].append(day_data)
            
            report['results'][name] = inspector_data
        
        # Salva il report
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Report dettagliato salvato in '{output_file}'")
    
    def create_comparison_charts(self, output_dir: str = 'charts'):
        """Crea grafici di confronto tra accertatori"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        if not self.competition_results:
            print("Nessun dato per creare grafici!")
            return
        
        # Prepara i dati
        inspectors_data = []
        daily_data = []
        
        for name, result in self.competition_results.items():
            inspectors_data.append({
                'name': name,
                'strategy': result['strategy'],
                'total_earnings': result['total_earnings'],
                'total_pois': sum(len(route.visited_pois) for route in result['day_routes']),
                'total_distance': sum(route.total_distance_km for route in result['day_routes']),
                'total_time': sum(route.total_time_minutes for route in result['day_routes'])
            })
            
            for route in result['day_routes']:
                daily_data.append({
                    'inspector': name,
                    'strategy': result['strategy'],
                    'day': route.day,
                    'earnings': route.total_fee_collected,
                    'pois': len(route.visited_pois),
                    'time': route.total_time_minutes,
                    'efficiency': (route.total_fee_collected / max(route.total_time_minutes, 1)) * 60
                })
        
        df_inspectors = pd.DataFrame(inspectors_data)
        df_daily = pd.DataFrame(daily_data)
        
        # Grafico 1: Guadagni totali
        plt.figure(figsize=(12, 6))
        bars = plt.bar(df_inspectors['name'], df_inspectors['total_earnings'], 
                      color=plt.cm.Set3(range(len(df_inspectors))))
        plt.title('Totale raccolto per Accertatore', fontsize=16, fontweight='bold')
        plt.xlabel('Accertatore')
        plt.ylabel('Totale raccolto (€)')
        plt.xticks(rotation=45)
        
        # Aggiungi valori sulle barre
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'€{height:.0f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/total_earnings.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Grafico 2: Performance giornaliera
        plt.figure(figsize=(14, 8))
        for strategy in df_daily['strategy'].unique():
            strategy_data = df_daily[df_daily['strategy'] == strategy]
            plt.plot(strategy_data['day'], strategy_data['earnings'], 
                    marker='o', linewidth=2, label=f'Strategia: {strategy}')
        
        plt.title('Performance Giornaliera per Strategia', fontsize=16, fontweight='bold')
        plt.xlabel('Giorno')
        plt.ylabel('Raccolto (€)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/daily_performance.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Grafico 3: Efficienza (€/ora)
        plt.figure(figsize=(12, 6))
        efficiency_by_inspector = df_daily.groupby('inspector')['efficiency'].mean()
        bars = plt.bar(efficiency_by_inspector.index, efficiency_by_inspector.values,
                      color=plt.cm.Pastel1(range(len(efficiency_by_inspector))))
        plt.title('Efficienza Media (€/ora) per Accertatore', fontsize=16, fontweight='bold')
        plt.xlabel('Accertatore')
        plt.ylabel('€/ora')
        plt.xticks(rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{height:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f'{output_dir}/efficiency.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Grafici salvati in '{output_dir}/'")

def setup_sample_competition():
    """Configura una competizione di esempio"""
    competition = MultiInspectorCompetition('dataset.csv')
    
    # Aggiunge diversi accertatori con strategie diverse
    competition.add_inspector("Mario Greedy", "greedy", seed=42)
    competition.add_inspector("Luigi Genetico", "genetic", seed=123)
    competition.add_inspector("Peach Casuale", "random", seed=456)
    competition.add_inspector("Bowser Avido", "high_value", seed=789)
    
    return competition

def main():
    """Funzione principale per la competizione interattiva"""
    print("COMPETIZIONE INTERATTIVA ACCERTATORI SIAE")
    print("="*55)
    
    # Setup competizione
    competition = setup_sample_competition()
    
    # Esegui competizione
    competition.run_competition(num_days=5)
    
    # Mostra risultati
    competition.print_competition_results()
    
    # Genera report e grafici
    competition.generate_detailed_report()
    try:
        competition.create_comparison_charts()
    except ImportError:
        print("Matplotlib non disponibile, salto la creazione dei grafici")
    
    # Statistiche finali
    winner = max(competition.competition_results.values(), key=lambda x: x['total_earnings'])
    print(f"\nVINCITORE: {winner['inspector'].name} con €{winner['total_earnings']:.2f}!")
    
    print(f"\nCompetizione completata!")

if __name__ == "__main__":
    main() 