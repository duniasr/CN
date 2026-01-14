# PRACTICA
# 1. Variables de entorno (Asegúrate de que el Bucket coincida con tu nueva temática)
$env:AWS_REGION="us-east-1"
$env:ACCOUNT_ID=(aws sts get-caller-identity --query Account --output text)
$env:BUCKET_NAME="datalake-ambiental-$env:ACCOUNT_ID"
$env:ROLE_ARN="arn:aws:iam::339712904114:role/LabRole"

# 2. Crear la infraestructura base
aws s3 mb "s3://$env:BUCKET_NAME"
aws s3api put-object --bucket $env:BUCKET_NAME --key raw/
aws s3api put-object --bucket $env:BUCKET_NAME --key processed/tabla_calidad/
aws s3api put-object --bucket $env:BUCKET_NAME --key processed/tabla_duracion/
aws s3api put-object --bucket $env:BUCKET_NAME --key scripts/

# 3. Crear el Stream de Kinesis con el nuevo nombre
aws kinesis create-stream --stream-name ambiental-stream --shard-count 1
# Comprobar que está activo
aws kinesis describe-stream-summary --stream-name tv-shows-stream

# 4. Sube la Lambda
aws lambda create-function --function-name tv-series-transformer `
    --runtime python3.12 --role $env:ROLE_ARN `
    --handler firehose.lambda_handler --zip-file fileb://firehose.zip `
    --timeout 60 --memory-size 128

$env:LAMBDA_ARN=(aws lambda get-function --function-name tv-series-transformer --query 'Configuration.FunctionArn' --output text)

# 5. Crea el Firehose
aws firehose create-delivery-stream --delivery-stream-name tv-series-firehose --delivery-stream-type KinesisStreamAsSource --kinesis-stream-source-configuration "KinesisStreamARN=arn:aws:kinesis:us-east-1:$($env:ACCOUNT_ID):stream/tv-shows-stream,RoleARN=$($env:ROLE_ARN)" --extended-s3-destination-configuration "{\`"BucketARN\`":\`"arn:aws:s3:::$($env:BUCKET_NAME)\`",\`"RoleARN\`":\`"$($env:ROLE_ARN)\`",\`"Prefix\`":\`"raw/processing_date=!{partitionKeyFromLambda:processing_date}/\`",\`"ErrorOutputPrefix\`":\`"errors/!{firehose:error-output-type}/\`",\`"BufferingHints\`":{\`"SizeInMBs\`":64,\`"IntervalInSeconds\`":300},\`"DynamicPartitioningConfiguration\`":{\`"Enabled\`":true},\`"ProcessingConfiguration\`":{\`"Enabled\`":true,\`"Processors\`":[{\`"Type\`":\`"Lambda\`",\`"Parameters\`":[{\`"ParameterName\`":\`"LambdaArn\`",\`"ParameterValue\`":\`"$($env:LAMBDA_ARN)\`"}]}]}}"
# Comprobar estado de firehose
aws firehose describe-delivery-stream --delivery-stream-name tv-series-firehose --query "DeliveryStreamDescription.DeliveryStreamStatus"

# 6. Lanzar kinesis
python kinesis.py

# 7. Subir scripts de Glue
# Crear la base de datos
aws glue create-database --database-input "Name=tv_series_db"
# Comprobar base de datos creada
aws glue get-database --name tv_series_db


# 8. Subir archivos
aws s3 cp puntuacion_genero.py "s3://$($env:BUCKET_NAME)/scripts/puntuacion_genero.py"
aws s3 cp duracion_idioma.py "s3://$($env:BUCKET_NAME)/scripts/duracion_idioma.py"

# 9. Crear el Crawler apuntando a la carpeta de sensores
aws glue create-crawler --name tv-series-raw-crawler --role $env:ROLE_ARN --database-name tv_series_db --targets "{\`"S3Targets\`": [{\`"Path\`": \`"s3://$($env:BUCKET_NAME)/raw/\`"}]}"
aws glue start-crawler --name tv-series-raw-crawler
# Comprobar que se creó
aws glue get-crawler --name tv-series-raw-crawler --query "Crawler.State"

# 10. Crear Jobs
# Crear Job de Calidad (Puntuación por Género)
aws glue create-job --name "tv-puntuacion-genero" --role $env:ROLE_ARN --command "{\`"Name\`": \`"glueetl\`", \`"ScriptLocation\`": \`"s3://$($env:BUCKET_NAME)/scripts/puntuacion_genero.py\`", \`"PythonVersion\`": \`"3\`"}" --default-arguments "{\`"--job-language\`":\`"python\`"}"
# Crear Job de Duración (Minutos por Idioma)
aws glue create-job --name "tv-duracion-idioma" --role $env:ROLE_ARN --command "{\`"Name\`": \`"glueetl\`", \`"ScriptLocation\`": \`"s3://$($env:BUCKET_NAME)/scripts/duracion_idioma.py\`", \`"PythonVersion\`": \`"3\`"}" --default-arguments "{\`"--job-language\`":\`"python\`"}"

# 11. Lanzar los Jobs
# Lanzar análisis de Puntuación/Calidad
# Guardaremos en: /processed/calidad/
aws glue start-job-run --job-name "tv-puntuacion-genero" --arguments "{\`"--database\`":\`"tv_series_db\`",\`"--table\`":\`"raw\`",\`"--output_path\`":\`"s3://$($env:BUCKET_NAME)/processed/\`"}"
# Comprobar estado job
aws glue get-job-runs --job-name "tv-puntuacion-genero" --query "JobRuns[0].JobRunState"

# Lanzar análisis de Duración por Idioma
# Guardaremos en: /processed/duracion/
aws glue start-job-run --job-name "tv-duracion-idioma" --arguments "{\`"--database\`":\`"tv_series_db\`",\`"--table\`":\`"raw\`",\`"--output_path\`":\`"s3://$($env:BUCKET_NAME)/processed/\`"}"
# Comprobar estado job
aws glue get-job-runs --job-name "tv-duracion-idioma" --query "JobRuns[0].JobRunState"

# Comprobar q los archivos están en S3

# 12. Crear Crawler final que registrará las dos tablas "tabla_calidad" y "tabla_duracion"
aws glue create-crawler --name tv-series-processed-crawler --role $env:ROLE_ARN --database-name tv_series_db --targets "{\`"S3Targets\`": [{\`"Path\`": \`"s3://$($env:BUCKET_NAME)/processed/\`"}]}"
# 13. Lanzar Crawler final
aws glue start-crawler --name tv-series-processed-crawler
# Cromprobar estado crawler
aws glue get-crawler --name tv-series-processed-crawler --query "Crawler.State"