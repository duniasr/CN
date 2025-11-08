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
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # La tabla no existe, crearla
                print(f"Creando tabla DynamoDB '{self.table_name}'...")
                table = self.dynamodb.create_table(
                    TableName=self.table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'note_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'note_id',
                            'AttributeType': 'S'
                        }
                    ],
                    BillingMode='PAY_PER_REQUEST'
                )
                
                # Esperar a que la tabla esté activa
                table.wait_until_exists()
                
                # Actualizar referencia a la tabla
                self.table = table
            else:
                raise
    
    def create_note(self, note: Note) -> Note:
        self.table.put_item(Item=note.model_dump())
        return note
    
    def get_note(self, note_id: str) -> Optional[Note]:
        response = self.table.get_item(Key={'note_id': note_id})
        if 'Item' in response:
            return Note(**response['Item'])
        return None
    
    def get_all_notes(self) -> List[Note]:
        response = self.table.scan()
        notes = [Note(**item) for item in response.get('Items', [])]
        return notes
    
    def update_note(self, note_id: str, note: Note) -> Optional[Note]:
        note.update_timestamp()
        note.note_id = note_id
        self.table.put_item(Item=note.model_dump())
        return note
    
    def delete_note(self, note_id: str) -> bool:
        response = self.table.delete_item(
            Key={'note_id': note_id},
            ReturnValues='ALL_OLD'
        )
        return 'Attributes' in response