import boto3
from botocore.exceptions import ClientError
from typing import List, Optional
from .db import Database
from models.note import Note
import os

class DynamoDBDatabase(Database):
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.table_name = os.getenv('DB_DYNAMONAME')
        self.table = self.dynamodb.Table(self.table_name)
        self.initialize()
    
    def initialize(self):
        try:
            # Intenta cargar la información de la tabla.
            self.table.load()
        except ClientError as e:
            # Si da un error, comprueba si es porque la tabla no existe.
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # La tabla no existe, así que la creamos.
                print(f"Creando tabla DynamoDB '{self.table_name}'...")
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[ # Define la clave primaria (Partition Key)
                        {
                            'AttributeName': 'note_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[ # Define el tipo de dato de los atributos clave
                        {
                            'AttributeName': 'note_id',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                # Espera hasta que la tabla termine de crearse.
                table.wait_until_exists()
                
                # Actualizar referencia a la tabla
                self.table = table
            else:
                raise
    
    # Implementación del método "Create" (Crear)
    def create_note(self, note: Note) -> Note:
        # 'put_item' crea un nuevo ítem (o sobrescribe uno existente si la ID ya existe).
        # 'note.model_dump()' convierte el objeto Pydantic 'Note' en un diccionario.
        self.table.put_item(Item=note.model_dump())
        return note
    
    # Implementación del método "Read" (Leer por ID)
    def get_note(self, note_id: str) -> Optional[Note]:
        # 'get_item' busca un ítem usando su clave primaria
        response = self.table.get_item(Key={'note_id': note_id})
        # Comprueba si la respuesta de DynamoDB contiene el 'Item'.
        if 'Item' in response:
            return Note(**response['Item'])
        return None
    
    # Implementación del método "Read All" (Leer todos)
    def get_all_notes(self) -> List[Note]:
        # 'scan' lee *toda* la tabla.
        response = self.table.scan()
        # Convierte cada ítem del diccionario de la respuesta en un objeto 'Note'.
        notes = [Note(**item) for item in response.get('Items', [])]
        return notes
    
    # Implementación del método "Update" (Actualizar)
    def update_note(self, note_id: str, note: Note) -> Optional[Note]:
        # Actualiza el timestamp del objeto 'note'.
        note.update_timestamp()
        # Asegura que la note_id en el cuerpo coincida con la de la URL.
        note.note_id = note_id
        # Sobrescribe el ítem entero.
        self.table.put_item(Item=note.model_dump())
        return note
    
    # Implementación del método "Delete" (Eliminar)
    def delete_note(self, note_id: str) -> bool:
        response = self.table.delete_item(
            Key={'note_id': note_id},
            # Pide a DynamoDB que devuelva el ítem que acaba de borrar.
            ReturnValues='ALL_OLD'
        )
        # Si 'Attributes' está en la respuesta, significa que encontró y borró un ítem.
        return 'Attributes' in response