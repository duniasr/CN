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
    """
    Función 'helper' para formatear la respuesta JSON
    requerida por API Gateway (AWS_PROXY).
    """
    return {
        'statusCode': status_code,
        'headers': {
            # Devuelve las cabeceras CORS en cada respuesta.
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,x-api-key',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        # El 'body' debe ser un *string* JSON.
        'body': json.dumps(body)
    }

def handler(event, context):
    """
    Esta es la función principal que AWS Lambda ejecutará
    cada vez que API Gateway reciba un GET /items/{id}.
    """
    try:
        # 1. Extraer el 'id' de los parámetros de la ruta.
        # API Gateway pasa la URL (ej. /items/123) como un dict 'pathParameters'.
        note_id = event.get('pathParameters', {}).get('id')
        # 2. Validar que el ID se ha proporcionado.
        if not note_id:
            return build_response(400, {'error': 'Falta note_id en la ruta'})

        # 3. Llamar a la lógica de negocio (solo el método de obtener por ID).
        note = db.get_note(note_id)
        
        # 4. Comprobar si la nota se encontró.
        if note:
            # ¡Éxito! Devolver el objeto 'Note' como JSON con un 200 (OK).
            return build_response(200, note.model_dump())
        else:
            # Si db.get_note() devolvió None, el ítem no existía.
            return build_response(404, {'error': 'Item no encontrado'})

    except Exception as e:
        # Captura cualquier otro error
        logger.error(f"Error: {e}")
        return build_response(500, {'error': 'Error interno', 'details': str(e)})
    