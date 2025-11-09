import json
import logging
import os
# Importamos desde la carpeta 'common'
from models.note import Note
from db.dynamodb_db import DynamoDBDatabase

logging.basicConfig(level=logging.INFO)
db = DynamoDBDatabase()

def build_response(status_code, body):
    """
    Función 'helper' para formatear la respuesta JSON
    requerida por API Gateway (AWS_PROXY).
    """
    return {
        'statusCode': status_code,
        'headers': {
            # La Lambda también es responsable de devolver las cabeceras CORS.
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
    cada vez que API Gateway reciba un DELETE /items/{id}.
    """
    try:
        # 1. Extraer el 'id' de los parámetros de la ruta.
        # API Gateway pasa la URL (ej. /items/123) como un dict 'pathParameters'.
        note_id = event.get('pathParameters', {}).get('id')
        if not note_id:
            # 2. Validar que el ID se ha proporcionado.
            return build_response(400, {'error': 'Falta note_id en la ruta'})

        # 3. Llamar a la lógica de negocio (solo el método de borrado).
        # db.delete_note() devuelve True si el ítem existía y se borró.
        if db.delete_note(note_id):
            # ¡Éxito! Devolvemos 204 (No Content)
            return build_response(204, "") 
        else:
            # Si db.delete_note() devuelve False, el ítem no existía.
            return build_response(404, {'error': 'Item no encontrado'})

    except Exception as e:
        # Captura cualquier otro error
        logger.error(f"Error: {e}")
        return build_response(500, {'error': 'Error interno', 'details': str(e)})