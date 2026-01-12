import json
import logging
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
    cada vez que API Gateway reciba un GET /items.
    """
    try:
        # 1. No se necesita 'pathParameters' ni 'body',
        #    simplemente llamamos al método para obtener todos los items.
        notes = db.get_all_notes()
        # 2. Convertir la lista de objetos 'Note' a una lista de diccionarios
        #    (usando .model_dump() de Pydantic) que se pueda serializar a JSON.
        return build_response(200, [n.model_dump() for n in notes])
    except Exception as e:
        # Captura cualquier otro error
        return build_response(500, {'error': 'Error interno', 'details': str(e)})