```bash
export AWS_REGION="us-east-1"
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export BUCKET_NAME="datalake-consumo-energetico-${ACCOUNT_ID}"
export ROLE_ARN=$(aws iam get-role --role-name LabRole --query 'Role.Arn' --output text)
echo "Usando Bucket: $BUCKET_NAME y Role: $ROLE_ARN"
```

**Windows (PowerShell):**

```powershell
$env:AWS_REGION = "us-east-1"
$env:ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
$env:BUCKET_NAME = "datalake-ambiental-$env:ACCOUNT_ID"
$env:ROLE_ARN = "arn:aws:iam::$env:ACCOUNT_ID:role/LabRole"

$env:AWS_REGION="us-east-1"
$env:ACCOUNT_ID="339712904114"
$env:BUCKET_NAME="datalake-consumo-energetico-env:339712904114"
$env:ROLE_ARN="arn:aws:iam::339712904114:role/LabRole"
```

---


# Crear el bucket
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Crear carpetas (objetos vacíos con / al final)
aws s3api put-object --bucket $env:BUCKET_NAME --key raw/
aws s3api put-object --bucket $env:BUCKET_NAME --key processed/
aws s3api put-object --bucket $env:BUCKET_NAME --key config/
aws s3api put-object --bucket $env:BUCKET_NAME --key scripts/

---

aws kinesis create-stream --stream-name energy-stream --shard-count 1

aws firehose create-delivery-stream `
    --delivery-stream-name energy-stream-store `
    --delivery-stream-type KinesisStreamAsSource `
    --kinesis-stream-source-configuration "KinesisStreamARN=arn:aws:kinesis:us-east-1:339712904114:stream/energy-stream,RoleARN=arn:aws:iam::339712904114:role/LabRole" `
    --extended-s3-destination-configuration "BucketARN=arn:aws:s3:::datalake-consumo-energetico-339712904114,RoleARN=arn:aws:iam::339712904114:role/LabRole,Prefix=raw/,ErrorOutputPrefix=errors/,BufferingHints={SizeInMBs=1,IntervalInSeconds=60}"

aws glue create-database --database-input "{\"Name\":\"energy_db\"}"

aws glue create-crawler \
    --name energy_temp_crawler \
    --role $ROLE_ARN \
    --database-name energy_db \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://$BUCKET_NAME/raw/\"}]}"

aws glue create-crawler \
    --name energy_temp_crawler \
    --role arn:aws:iam::339712904114:role/LabRole \
    --database-name energy_db \
    --targets "{\"S3Targets\": [{\"Path\": \"s3://datalake-consumo-energetico-env:339712904114/raw/\"}]}"


# PRACTICA
# 1. Variables de entorno (Asegúrate de que el Bucket coincida con tu nueva temática)
$env:AWS_REGION="us-east-1"
$env:ACCOUNT_ID=(aws sts get-caller-identity --query Account --output text)
$env:BUCKET_NAME="datalake-ambiental-$env:ACCOUNT_ID"
$env:ROLE_ARN="arn:aws:iam::339712904114:role/LabRole"

# 2. Crear la infraestructura base
aws s3 mb "s3://$env:BUCKET_NAME"
aws s3api put-object --bucket $env:BUCKET_NAME --key raw/
aws s3api put-object --bucket $env:BUCKET_NAME --key processed/daily_env/
aws s3api put-object --bucket $env:BUCKET_NAME --key processed/monthly_env/
aws s3api put-object --bucket $env:BUCKET_NAME --key scripts/

# 3. Crear el Stream de Kinesis con el nuevo nombre
aws kinesis create-stream --stream-name ambiental-stream --shard-count 1

# 4. Sube la Lambda
aws lambda create-function --function-name ambiental-transformer `
    --runtime python3.12 --role $env:ROLE_ARN `
    --handler firehose.lambda_handler --zip-file fileb://firehose.zip `
    --timeout 60 --memory-size 128

$env:LAMBDA_ARN=(aws lambda get-function --function-name ambiental-transformer --query 'Configuration.FunctionArn' --output text)

# 5. Crea el Firehose
aws firehose create-delivery-stream --delivery-stream-name ambiental-firehose --delivery-stream-type KinesisStreamAsSource --kinesis-stream-source-configuration "KinesisStreamARN=arn:aws:kinesis:us-east-1:$($env:ACCOUNT_ID):stream/ambiental-stream,RoleARN=$($env:ROLE_ARN)" --extended-s3-destination-configuration "{\`"BucketARN\`":\`"arn:aws:s3:::$($env:BUCKET_NAME)\`",\`"RoleARN\`":\`"$($env:ROLE_ARN)\`",\`"Prefix\`":\`"raw/processing_date=!{partitionKeyFromLambda:processing_date}/\`",\`"ErrorOutputPrefix\`":\`"errors/!{firehose:error-output-type}/\`",\`"BufferingHints\`":{\`"SizeInMBs\`":64,\`"IntervalInSeconds\`":60},\`"DynamicPartitioningConfiguration\`":{\`"Enabled\`":true},\`"ProcessingConfiguration\`":{\`"Enabled\`":true,\`"Processors\`":[{\`"Type\`":\`"Lambda\`",\`"Parameters\`":[{\`"ParameterName\`":\`"LambdaArn\`",\`"ParameterValue\`":\`"$($env:LAMBDA_ARN)\`"}]}]}}"

# 6. Lanzar kinesis
python kinesis.py

# 7. Subir scripts de Glue
# Crear la base de datos
aws glue create-database --database-input '{"Name":"ambiental_db"}'

# Crear el Crawler apuntando a la carpeta de sensores
aws glue create-crawler --name ambiental-raw-crawler --role $env:ROLE_ARN --database-name ambiental_db --targets "{\`"S3Targets\`": [{\`"Path\`": \`"s3://$($env:BUCKET_NAME)/raw/\`"}]}"
aws glue start-crawler --name ambiental-raw-crawler


# Crear Job Diario (creará archivos en /processed/daily_env/)
aws glue create-job --name "energy-daily-aggregation" --role $env:ROLE_ARN --command "{\`"Name\`": \`"glueetl\`", \`"ScriptLocation\`": \`"s3://$($env:BUCKET_NAME)/scripts/energy_aggregation_daily.py\`", \`"PythonVersion\`": \`"3\`"}" --default-arguments "{\`"--job-language\`":\`"python\`"}"
# Crear Job Mensual (creará archivos en /processed/monthly_env/)
aws glue create-job --name "energy-monthly-aggregation" --role $env:ROLE_ARN --command "{\`"Name\`": \`"glueetl\`", \`"ScriptLocation\`": \`"s3://$($env:BUCKET_NAME)/scripts/energy_aggregation_monthly.py\`", \`"PythonVersion\`": \`"3\`"}" --default-arguments "{\`"--job-language\`":\`"python\`"}"

aws glue start-job-run --job-name "energy-monthly-aggregation" --arguments "{\`"--database\`":\`"ambiental_db\`",\`"--table\`":\`"raw\`",\`"--output_path\`":\`"s3://$($env:BUCKET_NAME)/processed/monthly_env/\`"}"

# Subir archivos
aws s3 cp energy_aggregation_daily.py "s3://$($env:BUCKET_NAME)/scripts/energy_aggregation_daily.py"
aws s3 cp energy_aggregation_monthly.py "s3://$($env:BUCKET_NAME)/scripts/energy_aggregation_monthly.py"

# Lanzar los Jobs
aws glue start-job-run --job-name "energy-daily-aggregation" --arguments "{\`"--database\`":\`"ambiental_db\`",\`"--table\`":\`"raw\`",\`"--output_path\`":\`"s3://$($env:BUCKET_NAME)/processed/daily_env/\`"}"
aws glue start-job-run --job-name "energy-monthly-aggregation" --arguments "{\`"--database\`":\`"ambiental_db\`",\`"--table\`":\`"raw\`",\`"--output_path\`":\`"s3://$($env:BUCKET_NAME)/processed/monthly_env/\`"}"

# Comprobar q los archivos están en S3


#### RECUERDA Q EL S3 Y LA LAMBDA YA ESTÁN CREADAS ####