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
    cada vez que API Gateway reciba un PUT /items/{id}.
    """
    try:
        # 1. Extraer el 'id' de la nota que queremos editar de la URL.
        note_id = event['pathParameters']['id']
        if not note_id:
            return build_response(400, {'error': 'Falta note_id en la ruta'})
        
        # 2. Obtener la nota que ya existe en la BD.
        existing_note = db.get_note(note_id)
        # Si no existe, no podemos actualizarla. Devolver 404.
        if not existing_note:
            return build_response(404, {'error': 'Item no encontrado'})

        # 3. Cargar los datos *nuevos* que envía el usuario en el body.
        body = event.get('body')
        if body is None:
            data = {}
        else:
            data = json.loads(body)

        # 3. Se sobrescribe el 'note_id' y 'created_at' en los datos nuevos.
        # Esto evita que el modelo Pydantic genere un *nuevo* ID
        # y asegura que la fecha de creación original no se pierda.
        data['note_id'] = existing_note.note_id
        data['created_at'] = existing_note.created_at

        # 4. Validar el objeto *completo* (datos nuevos + ID/fecha antiguos).
        note_to_save = Note(**data)
        
        # 5. Llamar a la capa de DB para guardar (sobrescribir) la nota.
        updated = db.update_note(note_id, note_to_save)

        # 6. Devolver la nota actualizada con un 200 (OK).
        return build_response(200, updated.model_dump())

    except ValidationError as e:
        # Error de validación (Pydantic) si los datos del body son incorrectos.
        logger.error(f"Error de validación: {e.errors()}")
        return build_response(400, {'error': 'Validación fallida', 'details': e.errors()})
    except Exception as e:
        # Captura cualquier otro error
        logger.error(f"Error: {e}")
        return build_response(500, {'error': 'Error interno', 'details': str(e)})