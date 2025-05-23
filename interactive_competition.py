import pandas as pd
from typing import List
import random
import json
from tax_inspector_competition import CompetitionSimulator, DayRoute, POI
import matplotlib.pyplot as plt
import os

# Importa le funzioni per starting points da coordinate
try:
    from csv_starting_points import (
        load_starting_points_from_coordinates_csv,
        create_competition_with_coordinate_starting_points,
        create_example_coordinates_csv
    )
    CSV_STARTING_POINTS_AVAILABLE = True
except ImportError:
    print("csv_starting_points.py non trovato, usando solo starting points casuali")
    CSV_STARTING_POINTS_AVAILABLE = False

class Inspector:
    """Rappresenta un accertatore che utilizza la strategia high_value"""
    
    def __init__(self, name: str, seed: int = None):
        self.name = name
        self.strategy = 'high_value'
        self.seed = seed
        self.total_earnings = 0.0
        self.day_routes = []
        
    def __str__(self):
        return f"Accertatore {self.name} (Strategia: High Value)"

class MultiInspectorCompetition:
    """Gestisce una competizione tra più accertatori che usano la strategia high_value"""
    
    def __init__(self, dataset_path: str):
        self.simulator = CompetitionSimulator(dataset_path)
        self.inspectors = []
        self.competition_results = {}
        self.fixed_starting_points = None
        
    def add_inspector(self, name: str, seed: int = None):
        """Aggiunge un accertatore alla competizione"""
        inspector = Inspector(name, seed)
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
        """Esegue la competizione per tutti gli accertatori usando la strategia high_value"""
        if not self.fixed_starting_points:
            self.set_fixed_starting_points()
            
        print(f"\nINIZIO COMPETIZIONE CON {len(self.inspectors)} ACCERTATORI (Strategia High Value)")
        print("="*70)
        
        for inspector in self.inspectors:
            print(f"\nSimulazione per {inspector.name}")
            
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
        """Simula la competizione con punti di partenza fissi usando la strategia high_value"""
        day_routes = []
        
        for day, starting_point in enumerate(starting_points, 1):
            # Ottimizza il percorso usando la strategia high_value
            optimal_pois = self.simulator.optimizer.optimize_route_high_value(starting_point)
            
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
    
    def print_competition_results(self):
        """Stampa i risultati della competizione"""
        if not self.competition_results:
            print("Nessuna competizione eseguita!")
            return
            
        print("\n" + "="*70)
        print("RISULTATI FINALI DELLA COMPETIZIONE (Strategia High Value)")
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
            print(f"{i}. {inspector.name}: €{result['total_earnings']:.2f}")  
        
        # Dettagli per ogni accertatore
        print(f"\nDETTAGLI PER ACCERTATORE:")
        for result in sorted_results:
            inspector = result['inspector']
            routes = result['day_routes']
            
            print(f"\n{inspector.name}:")
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
            'strategy_used': 'high_value',
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
                'strategy': 'high_value',
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
                'total_earnings': result['total_earnings'],
                'total_pois': sum(len(route.visited_pois) for route in result['day_routes']),
                'total_distance': sum(route.total_distance_km for route in result['day_routes']),
                'total_time': sum(route.total_time_minutes for route in result['day_routes'])
            })
            
            for route in result['day_routes']:
                daily_data.append({
                    'inspector': name,
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
        plt.title('Totale raccolto per Accertatore (Strategia High Value)', fontsize=16, fontweight='bold')
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
        for inspector in df_daily['inspector'].unique():
            inspector_data = df_daily[df_daily['inspector'] == inspector]
            plt.plot(inspector_data['day'], inspector_data['earnings'], 
                    marker='o', linewidth=2, label=inspector)
        
        plt.title('Performance Giornaliera per Accertatore (Strategia High Value)', fontsize=16, fontweight='bold')
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
        plt.title('Efficienza Media (€/ora) per Accertatore (Strategia High Value)', fontsize=16, fontweight='bold')
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
        
        print(f"Grafici salvati in '{output_dir}/'")

def setup_sample_competition():
    """Configura una competizione di esempio con più accertatori usando strategia high_value"""
    competition = MultiInspectorCompetition('dataset.csv')
    
    # Aggiunge diversi accertatori con seed diversi per variabilità
    competition.add_inspector("Accertatore 1", seed=42)
    competition.add_inspector("Accertatore 2", seed=123)
    competition.add_inspector("Accertatore 3", seed=456)
    competition.add_inspector("Accertatore 4", seed=789)
    competition.add_inspector("Accertatore 5", seed=999)

    return competition

def setup_competition_with_csv_starting_points(starting_points_csv: str = None):
    """Configura una competizione con punti di partenza da CSV"""
    
    if not CSV_STARTING_POINTS_AVAILABLE:
        print("Sistema starting points da CSV non disponibile")
        return setup_sample_competition()
    
    # Se non specificato, cerca file predefiniti
    if starting_points_csv is None:
        # Lista di file CSV da cercare in ordine di priorità
        default_csv_files = [
            'starting_coordinates.csv',
            'starting_coordinates_example.csv',
            'custom_coordinates.csv'
        ]
        
        for csv_file in default_csv_files:
            if os.path.exists(csv_file):
                starting_points_csv = csv_file
                print(f"Trovato file starting points: {csv_file}")
                break
    
    if starting_points_csv and os.path.exists(starting_points_csv):
        # Usa starting points da CSV
        print(f"Caricamento starting points da CSV: {starting_points_csv}")
        
        competition = create_competition_with_coordinate_starting_points(
            dataset_path='dataset.csv',
            coordinates_csv_path=starting_points_csv,
            poi_type='custom_starting_point'
        )
        
        if competition:
            # Aggiunge accertatori con seed diversi
            competition.add_inspector("High Value Master", seed=42)
            competition.add_inspector("Value Hunter Pro", seed=123)
            competition.add_inspector("Premium Collector", seed=456)
            competition.add_inspector("Elite Gatherer", seed=789)
            competition.add_inspector("Top Value Seeker", seed=999)
            
            return competition
        else:
            print("Errore nel caricamento CSV, uso starting points casuali")
    
    # Fallback a starting points casuali
    print("🎲 Uso starting points casuali")
    return setup_sample_competition()

def main(starting_points_csv: str = None):
    """
    Funzione principale per la competizione interattiva usando strategia high_value
    
    Args:
        starting_points_csv: Percorso del file CSV con starting points (opzionale)
    """
    print("COMPETIZIONE INTERATTIVA ACCERTATORI SIAE (Strategia High Value)")
    print("="*65)
    
    # Controlla se il sistema CSV è disponibile
    if CSV_STARTING_POINTS_AVAILABLE:
        print("Sistema starting points da CSV disponibile")
        
        # Se non specificato file CSV, crea un esempio se non esiste
        if starting_points_csv is None and not any(os.path.exists(f) for f in [
            'starting_coordinates.csv', 'starting_coordinates_example.csv', 'custom_coordinates.csv'
        ]):
            print("📝 Creazione file di esempio per starting points...")
            create_example_coordinates_csv()
    else:
        print("Sistema starting points da CSV non disponibile")
    
    # Setup competizione
    print(f"\nConfigurazione competizione...")
    if CSV_STARTING_POINTS_AVAILABLE:
        competition = setup_competition_with_csv_starting_points(starting_points_csv)
    else:
        competition = setup_sample_competition()
    
    if not competition:
        print("Impossibile creare competizione, termino.")
        return
    
    # Mostra configurazione
    print(f"\nConfigurazione:")
    print(f"   - Strategia utilizzata: High Value")
    print(f"   - Accertatori: {len(competition.inspectors)}")
    
    if hasattr(competition, 'fixed_starting_points') and competition.fixed_starting_points:
        print(f"   - Starting points: PERSONALIZZATI da CSV")
        print(f"   - Distribuzione giurisdizioni:")
        jurisdiction_counts = {}
        for poi in competition.fixed_starting_points:
            jurisdiction_counts[poi.jurisdiction] = jurisdiction_counts.get(poi.jurisdiction, 0) + 1
        for jurisdiction, count in sorted(jurisdiction_counts.items()):
            print(f"     * {jurisdiction}: {count} giorni")
    else:
        print(f"   - Starting points: CASUALI")
    
    # Esegui competizione
    print(f"\nEsecuzione competizione...")
    competition.run_competition(num_days=5)
    
    # Mostra risultati
    print(f"\n" + "="*60)
    competition.print_competition_results()
    
    # Genera report e grafici
    print(f"\nGenerazione report...")
    competition.generate_detailed_report('competition_report.json')

    try:
        competition.create_comparison_charts()
        print("Grafici di confronto creati")
    except ImportError:
        print("Matplotlib non disponibile, salto la creazione dei grafici")
    except Exception as e:
        print(f"Errore nella creazione grafici: {e}")
    
    # Statistiche finali
    winner = max(competition.competition_results.values(), key=lambda x: x['total_earnings'])
    print(f"\nVINCITORE: {winner['inspector'].name} con €{winner['total_earnings']:.2f}!")
    
    # Analisi performance
    print(f"\nAnalisi Performance (Strategia High Value):")
    earnings_list = [result['total_earnings'] for result in competition.competition_results.values()]
    avg_earnings = sum(earnings_list) / len(earnings_list)
    max_earnings = max(earnings_list)
    min_earnings = min(earnings_list)
    
    print(f"   - Media guadagni: €{avg_earnings:.2f}")
    print(f"   - Massimo guadagno: €{max_earnings:.2f}")
    print(f"   - Minimo guadagno: €{min_earnings:.2f}")
    print(f"   - Differenza max-min: €{max_earnings - min_earnings:.2f}")
    
    print(f"\nCompetizione completata!")
    print(f"\nFile generati:")
    print(f"   - competition_report.json")
    if os.path.exists('charts'):
        print(f"   - charts/ (grafici di confronto)")
    if starting_points_csv and os.path.exists(starting_points_csv):
        print(f"   - {starting_points_csv} (starting points utilizzati)")

if __name__ == "__main__":
    main()