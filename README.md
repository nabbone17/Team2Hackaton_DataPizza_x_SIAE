# Documentazione - Hackathon SIAE

## Preprocessing
Il dataset è contenuto nel file dataset_finale.csv, e ottenuto mediante:

1. **Filtraggio per tipo OSM**  
   Dal dataset `20250523_Hackaton_SIAE` rimuovere i record la cui colonna `osm_type` è diversa da `"nodes"`.

2. **Rimozione clienti storici dai POI**  
   Dal dataset `20250523_Hackaton_SIAE`, che contiene tutti i punti di interesse, sottrarre i record presenti nel dataset `20250519_Clients_Historical`.  
   - **Chiave di confronto:** colonna `id`.

3. **Stima del `fee_value` per i prospect**  
   - Calcolare la media del `fee_value` per ciascun `poi_type` nel dataset dei clienti storici.
   - Assegnare questo valore medio a tutti i prospect con lo stesso `poi_type`.

4. **Rimozione POI senza tipo**  
   Eliminare tutti i record con `poi_type = Null`.

5. **Aggiunta della colonna `jurisdiction`**  
   Unire i dati dei prospect con quelli contenuti in `jurisdiction.csv` per ottenere la colonna `jurisdiction`.

---

## Utilizzo del Motore di Inferenza

Il motore identifica i POI che soddisfano i criteri stabiliti. Da questi è possibile costruire un percorso ottimale.

- **Notebook da eseguire:** `inference_motor.ipynb`
- **Input richiesto:** `starting_point.csv`, da posizionare nella stessa directory.
- **Formato del file di input:**
  ```
  day,lat,lon
  ```

---

## Routing
Per il calcolo del percorso viene utilizzato l’algoritmo `high_value`. La distanza tra punti è ottenuta tramite formula Haversine; a partire da questa viene ricavato il tempo di percorrenza a piedi ad una velocità media di 5km/h. Il tempo di percorrenza trovato viene corretto con un fattore pari a 2 per adattarlo alla planimetria.

---

## Side Quest 1: Calcolo delle Distanze

Utilizzo delle API Maps per determinare distanze e durate a piedi tra punti di interesse.

- **Funzione:**  
  ```python
  get_walking_distance_duration(origin_lat, origin_long, dest_lat, dest_long)
  ```
- **File:** `side_quest1.py`

> *Nota:* La funzione non è integrata nel flusso principale per evitare il superamento delle quote API, ma può essere eseguita separatamente.

---

## Ulteriori Sviluppi

- **Clustering dei prospect:** per ridurre la complessità del grafo delle distanze.
- **Stima del fattore di correzione delle distanze:** per migliorare le valutazioni.
- **Analisi più sofisticata della redditività dei prospect**.
