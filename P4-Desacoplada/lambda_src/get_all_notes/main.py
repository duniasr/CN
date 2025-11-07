import json
import logging
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
        notes = db.get_all_notes()
        return build_response(200, [n.model_dump() for n in notes])
    except Exception as e:
        return build_response(500, {'error': 'Error interno', 'details': str(e)})