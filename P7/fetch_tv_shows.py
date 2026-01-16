import requests
import json
import time

def fetch_tv_data():
    total_shows = []
    print("Conectando con la base de datos de TV Maze (Sin API Key)...")
    
    # Bajamos las primeras 4 páginas (250 shows por página = 1,000 registros)
    for page in range(0, 4):
        url = f"http://api.tvmaze.com/shows?page={page}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            total_shows.extend(data)
            print(f"Página {page} recuperada. Total actual: {len(total_shows)} series...")
        else:
            print(f"Error en página {page}: {response.status_code}")
            break
        
        time.sleep(0.5) # Un pequeño respiro para la API

    # Limpiamos los datos para que el análisis en Glue sea potente
    cleaned_data = []
    for s in total_shows:
        cleaned_data.append({
            "show_id": s.get('id'),
            "nombre": s.get('name'),
            "idioma": s.get('language'),
            "genero_principal": s.get('genres')[0] if s.get('genres') else "Drama",
            "puntuacion": float(s['rating']['average']) if s.get('rating') and s['rating']['average'] else 0.0,
            "duracion": int(s.get('runtime')) if s.get('runtime') else 0,
            "estreno": s.get('premiered')
        })

    with open('tv_shows_data.json', 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
    
    print(f"¡Éxito! Hay {len(cleaned_data)} registros en 'tv_shows_data.json'")

if __name__ == "__main__":
    fetch_tv_data()