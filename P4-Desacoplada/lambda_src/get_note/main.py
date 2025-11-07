import json
import logging
import os
# Importamos desde la carpeta 'common'
from models.note import Note
from db.dynamodb_db import DynamoDBDatabase

logging.basicConfig(level=logging.INFO)
db = DynamoDBDatabase()
logger = logging.getLogger()

def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }

def handler(event, context):
    try:
        # Obtenemos el 'id' de los parámetros de la ruta
        note_id = event.get('pathParameters', {}).get('id')
        if not note_id:
            return build_response(400, {'error': 'Falta note_id en la ruta'})

        note = db.get_note(note_id)
        
        if note:
            return build_response(200, note.model_dump())
        else:
            return build_response(404, {'error': 'Item no encontrado'})

    except Exception as e:
        logger.error(f"Error: {e}")
        return build_response(500, {'error': 'Error interno', 'details': str(e)})
    