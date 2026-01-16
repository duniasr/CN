import json
import base64
import datetime

def lambda_handler(event, context):
    output = []
    for record in event['records']:
        # 1. Decodificar el dato que viene de Kinesis
        payload = base64.b64decode(record['data']).decode('utf-8')
        serie_data = json.loads(payload)
        
        # 2. Lógica de procesamiento: Añadimos un timestamp de procesamiento
        # Esto ayuda a demostrar "transformación básica" en la memoria
        now = datetime.datetime.now(datetime.timezone.utc)
        serie_data['aws_ingestion_timestamp'] = now.isoformat()
        
        # 3. Crear la partición por fecha (Requisito para S3)
        partition_date = now.strftime('%Y-%m-%d')
        
        # 4. Preparar el dato para S3 (añadimos salto de línea)
        processed_data = json.dumps(serie_data) + '\n'
        
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(processed_data.encode('utf-8')).decode('utf-8'),
            'metadata': {
                'partitionKeys': {
                    'processing_date': partition_date  # Esta es la clave que usa Firehose en el Prefix
                }
            }
        }
        output.append(output_record)
    
    return {'records': output}