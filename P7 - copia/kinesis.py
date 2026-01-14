#kinesis.py
import boto3
import json
import time
from loguru import logger
import datetime

# CONFIGURACIÓN
STREAM_NAME = 'tv-shows-stream'
REGION = 'us-east-1' # Cambia si usas otra región
INPUT_FILE = 'tv_shows_data.json'

kinesis = boto3.client('kinesis', region_name=REGION)

def load_data(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def run_producer():
    data = load_data(INPUT_FILE)
    records_sent = 0
    
    logger.info(f"Iniciando transmisión al stream: {STREAM_NAME}...")
    
    for s in data:
        # Estructura del mensaje a enviar
        payload = {
            'show_id': s['show_id'],
            'nombre': s['nombre'],
            'idioma': s['idioma'],
            'genero': s['genero_principal'],
            'puntuacion': s['puntuacion'], # Campo numérico para promedios
            'duracion': s['duracion'],     # Campo numérico para promedios
            'timestamp': datetime.datetime.now().isoformat()
        }
            
        # Enviar a Kinesis
        kinesis.put_record(
            StreamName=STREAM_NAME,
            Data=json.dumps(payload),
            PartitionKey=s['genero_principal']
        )
            
        records_sent += 1
        if records_sent % 100 == 0:
            logger.info(f"Progreso: {records_sent} registros enviados...")

        # Pequeña pausa para simular streaming y no saturar de golpe
        time.sleep(0.1) 

    logger.info(f"Fin de la transmisión. Total registros enviados: {records_sent}")

if __name__ == '__main__':
    run_producer()