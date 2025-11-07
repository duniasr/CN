import json
import logging
import os
from pydantic import ValidationError
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
        # El ID de la nota que queremos editar (ej: "c145...")
        note_id = event['pathParameters']['id']
        if not note_id:
            return build_response(400, {'error': 'Falta note_id en la ruta'})

        # --- INICIO DE LA CORRECCIÓN ---

        # 1. Obtener la nota existente de la BD
        existing_note = db.get_note(note_id)
        if not existing_note:
            return build_response(404, {'error': 'Item no encontrado'})

        # 2. Cargar los datos nuevos del frontend
        body = event.get('body')
        if body is None:
            data = {}
        else:
            data = json.loads(body)

        # 3. PRESERVAR el note_id y created_at originales
        #    Esto evita que Pydantic genere un ID nuevo.
        data['note_id'] = existing_note.note_id
        data['created_at'] = existing_note.created_at

        # 4. Validar los datos (Pydantic usará el ID existente "c145...")
        note_to_save = Note(**data)
        
        # 5. Guardar la nota actualizada
        updated = db.update_note(note_id, note_to_save)
        
        # --- FIN DE LA CORRECCIÓN ---

        return build_response(200, updated.model_dump())

    except ValidationError as e:
        logger.error(f"Error de validación: {e.errors()}")
        return build_response(400, {'error': 'Validación fallida', 'details': e.errors()})
    except Exception as e:
        logger.error(f"Error: {e}")
        return build_response(500, {'error': 'Error interno', 'details': str(e)})