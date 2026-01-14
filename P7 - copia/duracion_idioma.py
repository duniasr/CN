# Cuánto duran las series según su idioma duracion_idioma.py
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

    # 1. CARGAR: Leemos los datos originales del catálogo
    dynamic_frame = glueContext.create_dynamic_frame.from_catalog(
        database=database,
        table_name=table
    )
    df = dynamic_frame.toDF()

    # 2. TRANSFORMAR: Análisis de Duración por Idioma
    # Agrupamos por idioma y sacamos la media de la columna 'duracion'
    idiomas_df = df.groupBy("idioma") \
        .agg(
            spark_round(avg("duracion"), 2).alias("minutos_promedio")
        ) \
        .orderBy(col("minutos_promedio").desc())
    
    output_dynamic_frame = DynamicFrame.fromDF(idiomas_df, glueContext, "output")
    
    logger.info(f"Registros agregados: {output_dynamic_frame.count()}")
    
    # Escribir usando GlueContext
    glueContext.write_dynamic_frame.from_options(
        frame=output_dynamic_frame,
        connection_type="s3",
        connection_options={
            "path": f"{output_path}tabla_duracion/",
            "partitionKeys": ["idioma"]
        },
        format="parquet",
        format_options={"compression": "snappy"}
    )
    
    logger.info(f"Completado. Registros: {idiomas_df.count()}")

if __name__ == "__main__":
    main()