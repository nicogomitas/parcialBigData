from pyspark.sql import SparkSession

# Crear o obtener la sesión de Spark
spark = SparkSession.builder \
    .appName("MiAplicacionSpark") \
    .getOrCreate()

# Ahora puedes usar 'spark' para ejecutar operaciones de Spark
#spark
df_zones = spark.read.csv("s3://jupyterbucket666/zones/",header=True,inferSchema=True) 
df_taxis = spark.read.parquet("s3://jupyterbucket666/taxis/")
from pyspark.sql import functions as F

# Convertir las columnas de tiempo a tipo Timestamp en el DataFrame original
df_taxis = df_taxis.withColumn("tpep_pickup_datetime", F.to_timestamp("tpep_pickup_datetime"))
df_taxis = df_taxis.withColumn("tpep_dropoff_datetime", F.to_timestamp("tpep_dropoff_datetime"))

# Calcular el tiempo de viaje en minutos y crear un nuevo DataFrame
df_trips = df_taxis \
    .withColumn("travel_time_minutes", 
                (F.col("tpep_dropoff_datetime").cast("long") - F.col("tpep_pickup_datetime").cast("long")) / 60) \
    .join(df_zones.alias("pu_zones"), 
          df_taxis.PULocationID == F.col("pu_zones.LocationID")) \
    .join(df_zones.alias("do_zones"), 
          df_taxis.DOLocationID == F.col("do_zones.LocationID")) \
    .select(
        F.col("pu_zones.Zone").alias("nombre_zona_origen"),
        F.col("do_zones.Zone").alias("nombre_zona_destino"),
        "travel_time_minutes"
    )

#Guardar df_trips en una carpeta de s3
df_trips.write.parquet("s3://jupyterbucket666/trips")