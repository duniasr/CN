# monthly_aggregation.py
import sys
import logging
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import col, sum as spark_sum, avg, substring
from awsglue.dynamicframe import DynamicFrame

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    args = getResolvedOptions(sys.argv, ['database', 'table', 'output_path'])
    database = args['database']
    table = args['table']
    output_path = args['output_path']

    logger.info(f"Database: {database}, Table: {table}, Output: {output_path}")
    
    sc = SparkContext()
    glueContext = GlueContext(sc)

    # Asegúrate de CARGAR los datos (tu snippet anterior no tenía esta parte)
    dynamic_frame = glueContext.create_dynamic_frame.from_catalog(database=database, table_name=table)
    df = dynamic_frame.toDF()

    # Cambia el substring a 7 para agrupar por MES (YYYY-MM)
    df = df.withColumn("fecha", substring(col("timestamp"), 1, 7))

    # Agregación mensual
    monthly_df = df.groupBy("fecha", "sensor_id") \
        .agg(
            avg("temperatura").alias("temp_media_mes"),
            avg("humedad").alias("humedad_media_mes")
        ) \
        .orderBy("fecha", "sensor_id")
    
    output_dynamic_frame = DynamicFrame.fromDF(monthly_df, glueContext, "output")
    
    logger.info(f"Registros agregados: {output_dynamic_frame.count()}")
    
    # Escribir usando GlueContext
    glueContext.write_dynamic_frame.from_options(
        frame=output_dynamic_frame,
        connection_type="s3",
        connection_options={
            "path": output_path,
            "partitionKeys": ["fecha"]
        },
        format="parquet",
        format_options={"compression": "snappy"}
    )
    
    logger.info(f"Completado. Registros: {monthly_df.count()}")

if __name__ == "__main__":
    main()