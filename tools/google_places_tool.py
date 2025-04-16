from crewai.tools import BaseTool
import googlemaps
import os
import json

class GooglePlacesTool(BaseTool):
    name: str = "GooglePlacesTool"
    description: str = "Busca guarderías cerca de una ubicación usando Google Maps API."

    def _run(self, ubicacion: str, transporte: str, tiempo_max: int) -> str:
        try:
            gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

            try:
                geocode_result = gmaps.geocode(ubicacion)
                if not geocode_result:
                    return json.dumps({"error": f"No se pudo geolocalizar la dirección: {ubicacion}"})
                location = geocode_result[0]["geometry"]["location"]
                latlng = (location["lat"], location["lng"])
            except googlemaps.exceptions.ApiError as e:
                return json.dumps({"error": f"Error de API geolocalizando: {e}"})
            except Exception as e:
                 return json.dumps({"error": f"Error inesperado geolocalizando: {e}"})

            transporte_map = {
                "andando": "walking",
                "coche": "driving",
                "autobús": "transit",
                "bus": "transit"
            }
            transporte_api = transporte_map.get(transporte.lower(), "walking")
            velocidad_kmh = {
                "walking": 5,
                "driving": 30,
                "transit": 15
            }.get(transporte_api, 5)
            radio_metros = int((velocidad_kmh * 1000 / 60) * tiempo_max)

            try:
                places_result = gmaps.places_nearby(
                    location=latlng,
                    radius=radio_metros,
                    keyword="guardería"
                )
            except googlemaps.exceptions.ApiError as e:
                return json.dumps({"error": f"Error de API buscando lugares cercanos: {e}"})
            except Exception as e:
                 return json.dumps({"error": f"Error inesperado buscando lugares cercanos: {e}"})

            guarderias = []
            for place in places_result.get("results", []):
                nombre = place.get("name")
                direccion = place.get("vicinity")
                if not nombre or not direccion:
                    continue

                try:
                    directions = gmaps.directions(
                        origin=ubicacion,
                        destination=direccion,
                        mode=transporte_api,
                    )

                    if not directions or not directions[0]["legs"]:
                        continue # No se encontró ruta

                    duracion_info = directions[0]["legs"][0].get("duration")
                    if not duracion_info:
                         continue # No hay info de duración
                         
                    duracion_texto = duracion_info.get("text", "N/A")
                    duracion_min = duracion_info.get("value", float('inf')) / 60

                    if duracion_min <= tiempo_max:
                        guarderias.append({
                            "nombre": nombre,
                            "direccion": direccion,
                            "duracion_texto": duracion_texto,
                            "minutos": round(duracion_min, 1)
                        })
                except googlemaps.exceptions.ApiError as e:
                     # Loggear error pero continuar con otras guarderías
                     print(f"Advertencia: Error de API obteniendo direcciones para '{nombre}': {e}") 
                except Exception as e:
                     print(f"Advertencia: Error inesperado obteniendo direcciones para '{nombre}': {e}")
                     
            return json.dumps(guarderias, ensure_ascii=False, indent=2)
            
        except Exception as e:
            # Error general en la herramienta
             print(f"Error crítico en GooglePlacesTool: {e}")
             return json.dumps({"error": f"Error general en la herramienta GooglePlaces: {e}"})