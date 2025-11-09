from flask import Flask, request, jsonify
from pydantic import ValidationError # Para validar los datos de entrada (JSON)
import psycopg2
from botocore.exceptions import ClientError # Para capturar errores de DynamoDB
from models.note import Note
from db.dynamodb_db import DynamoDBDatabase # La capa de acceso a DynamoDB

# 1. INICIALIZACIÓN DE LA APP
# =================================
app = Flask(__name__)

try:
    # Instancia la base de datos UNA VEZ cuando la aplicación arranca.
    db = DynamoDBDatabase()
except ValueError as e:
    raise RuntimeError(f"Error initializing DB: {e}") from e

# 2. CONFIGURACIÓN DE CORS
# =================================
@app.after_request
def add_cors_headers(response):
    # Esta función se ejecuta después de cada petición.
    # Añade las cabeceras CORS, permitiendo que un frontend
    # (en otro dominio) pueda llamar a esta API.
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,x-api-key'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    return response

# 3. ENDPOINTS DE LA API (CRUD)
# =================================

# --- CREATE ---
@app.route('/items', methods=['POST'])
def create_item():
    try:
        # 1. Obtener el JSON del body de la petición
        data = request.get_json()
        # 2. Validar el JSON usando el modelo Pydantic 'Note'
        note = Note(**data)
        # 3. Llamar a la capa de base de datos para crear la nota
        created = db.create_note(note)
        # 4. Devolver la nota creada con un código 201 (Created)
        return jsonify(created.model_dump()), 201
    
    # --- Manejo de Errores Específicos ---
    except ValidationError as e:
        # El JSON de entrada era inválido
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
        # Errores si usasemos PostgreSQL
    except psycopg2.IntegrityError as e:
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 409
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        # Error específico de AWS (ej. DynamoDB)
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

# --- READ (Get by ID) ---
@app.route('/items/<note_id>', methods=['GET'])
def get_item(note_id):
    try:
        # 1. Llamar a la capa de DB para obtener la nota por su ID
        note = db.get_note(note_id)
        # 2. Comprobar si la nota existe
        if note:
            # Devolver la nota con un 200 (OK)
            return jsonify(note.model_dump()), 200
        # 3. Si no existe, devolver un 404 (Not Found)
        return jsonify({'error': 'Item no encontrado'}), 404
    # Errores si usasemos PostgreSQL
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    # Error específico de AWS (ej. DynamoDB)
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

# --- READ (Get All) ---
@app.route('/items', methods=['GET'])
def get_all_items():
    try:
        # 1. Llamar a la capa de DB para obtener todas las notas
        notes = db.get_all_notes()
        # 2. Convertir la lista de objetos 'Note' a una lista de diccionarios
        #    y devolverla con un 200 (OK)
        return jsonify([t.model_dump() for t in notes]), 200
    # Errores si usasemos PostgreSQL
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    # Error específico de AWS (ej. DynamoDB)
    except ClientError as e:
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

# --- UPDATE ---
@app.route('/items/<note_id>', methods=['PUT'])
def update_item(note_id):
    try:
        # 1. Obtener el JSON del body
        data = request.get_json()
        # 2. Eliminar campos que no se deben actualizar
        # desde el body (como el ID o la fecha de creación).
        data.pop('note_id', None)
        data.pop('created_at', None)
        # 3. Validar los datos restantes
        note = Note(**data)
        # 4. Llamar a la capa de DB para actualizar
        updated = db.update_note(note_id, note)
        if updated:
            # Devolver la nota actualizada con un 200 (OK)
            return jsonify(updated.model_dump()), 200
        # 5. Si 'update_note' no devolvió nada, es que no existía
        return jsonify({'error': 'Item no encontrado'}), 404
    except ValidationError as e:
        # El JSON de entrada era inválido
        return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
    # Errores si usasemos PostgreSQL
    except psycopg2.IntegrityError as e:
        return jsonify({'error': 'Database integrity error', 'details': str(e)}), 409
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        # Error específico de AWS (ej. DynamoDB)
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

# --- DELETE ---
@app.route('/items/<note_id>', methods=['DELETE'])
def delete_item(note_id):
    try:
        # 1. Llamar a la capa de DB para borrar la nota
        if db.delete_note(note_id):
            # 2. Si tuvo éxito, devolver un 204 (No Content)
            #    (un body vacío es estándar para DELETE)
            return '', 204
        # 3. Si 'delete_note' devolvió False, es que no existía
        return jsonify({'error': 'Item no encontrado'}), 404
    # Errores si usasemos PostgreSQL
    except psycopg2.OperationalError as e:
        return jsonify({'error': 'Database connection error', 'details': str(e)}), 503
    except psycopg2.Error as e:
        return jsonify({'error': 'Database error', 'details': str(e)}), 500
    except ClientError as e:
        # Error específico de AWS (ej. DynamoDB)
        return jsonify({'error': 'DynamoDB error', 'details': e.response['Error']['Message']}), 500

# 4. ENDPOINT DE HEALTH CHECK
# =================================
@app.route('/health', methods=['GET'])
def health():
    # El TargetGroup del NLB está configurado para llamar a '/health'.
    # Si esta ruta devuelve un 200, el NLB sabe que el contenedor
    # está "sano" y puede recibir tráfico.
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)