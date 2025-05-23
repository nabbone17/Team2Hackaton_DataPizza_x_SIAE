import requests
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def get_walking_distance_duration(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    Calcola distanza e durata a piedi tra due coordinate usando Google Maps Distance Matrix API.
    """
    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "mode": "walking",
        "key": API_KEY
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    try:
        element = data["rows"][0]["elements"][0]
        if element["status"] == "OK":
            return {
                "distance_m": element["distance"]["value"],
                "duration_s": element["duration"]["value"]
            }
        else:
            return {"error": element["status"]}
    except Exception as e:
        return {"error": str(e)}