import json
import logging
from pydantic import ValidationError
# Importamos desde la carpeta 'common'
from models.note import Note
from db.dynamodb_db import DynamoDBDatabase

logging.basicConfig(level=logging.INFO)
db = DynamoDBDatabase()

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
        data = json.loads(event.get('body', '{}'))
        note = Note(**data)
        created = db.create_note(note)
        return build_response(201, created.model_dump())
    except ValidationError as e:
        return build_response(400, {'error': 'Validación fallida', 'details': e.errors()})
    except Exception as e:
        return build_response(500, {'error': 'Error interno', 'details': str(e)})