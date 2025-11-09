import json
import logging
from pydantic import ValidationError
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
            # En la versión acoplada, esto lo hacía Flask (@app.after_request).
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
    cada vez que API Gateway reciba un POST /items.
    """
    try:
        # 1. API Gateway pasa la petición HTTP (incluyendo body, headers, etc.)
        #    como un gran diccionario JSON (el 'event').
        data = json.loads(event.get('body', '{}'))
        # 2. Validar los datos de entrada usando el modelo Pydantic 'Note'.
        note = Note(**data)
        # 3. Reutilizar nuestro objeto 'db' global para crear la nota.
        #    Esta función solo llama a .create_note()
        created = db.create_note(note)
        # 4. Devolver una respuesta 201 (Created)
        return build_response(201, created.model_dump())
    
    # --- Manejo de Errores ---
    except ValidationError as e:
        # El JSON de entrada era inválido.
        return build_response(400, {'error': 'Validación fallida', 'details': e.errors()})
    except Exception as e:
        # Cualquier otro error (ej. DynamoDB no responde).
        return build_response(500, {'error': 'Error interno', 'details': str(e)})