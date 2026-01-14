# Calidad media de las series según su género puntuacion_genero.py
import sys
import logging
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import col, avg, round as spark_round
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
    
    # 1. LEER: Coge los datos que el Crawler encontró
    dynamic_frame = glueContext.create_dynamic_frame.from_catalog(
        database=database,
        table_name=table
    )
    
    # Convertir a Spark DataFrame
    df = dynamic_frame.toDF()
    # df.printSchema()
    logger.info(f"Registros leídos: {df.count()}")
    
    # 2. TRANSFORMAR: Análisis de Calidad media por Género
    # Agrupamos por género y calculamos la media de puntuación redondeada
    calidad_df = df.groupBy("genero") \
        .agg(
            # avg para la media y round para dejar 2 decimales
            spark_round(avg("puntuacion"), 2).alias("rating_promedio")
        ) \
        .orderBy(col("rating_promedio").desc())
    
    # 3. CARGAR: Guardamos el resultado en Parquet
    output_dynamic_frame = DynamicFrame.fromDF(calidad_df, glueContext, "output")
    logger.info(f"Registros agregados: {output_dynamic_frame.count()}")
    # Escribir usando GlueContext
    glueContext.write_dynamic_frame.from_options(
        frame=output_dynamic_frame,
        connection_type="s3",
        connection_options={
            "path": f"{output_path}tabla_calidad/",
            "partitionKeys": ["genero"]
        },
        format="parquet",
        format_options={"compression": "snappy"}
    )
    
    logger.info(f"Completado. Registros: {calidad_df.count()}")

if __name__ == "__main__":
    main()