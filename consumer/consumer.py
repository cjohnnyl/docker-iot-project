from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, avg, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType

# 🚀 SparkSession com Kafka + PostgreSQL
spark = (
    SparkSession.builder
    .appName("IoTConsumer")
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
        "org.postgresql:postgresql:42.6.0"
    )
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# 🧩 Schema das mensagens JSON
schema = StructType([
    StructField("sensor_id", StringType(), True),
    StructField("estufa_id", StringType(), True),
    StructField("bed_id", IntegerType(), True),
    StructField("clone_id", StringType(), True),
    StructField("soil_temp_c", DoubleType(), True),
    StructField("humidity", DoubleType(), True),
    StructField("timestamp", StringType(), True),
])

# 🛰️ Leitura do Kafka
kafka_df = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "iot_sensors")
    .option("startingOffsets", "earliest")  # 👈 força ler tudo desde o início
    .load()
)

# 📦 Converte o valor binário em JSON
json_df = (
    kafka_df.selectExpr("CAST(value AS STRING) AS json_data")
    .select(from_json(col("json_data"), schema).alias("data"))
    .select("data.*")
)

# 📊 Agrega por estufa
agg_df = (
    json_df.groupBy("estufa_id")
    .agg(
        avg("soil_temp_c").alias("avg_soil_temp_c"),
        avg("humidity").alias("avg_humidity")
    )
    .withColumn("processed_at", current_timestamp())
)

# 🗄️ Configuração do PostgreSQL
db_url = "jdbc:postgresql://postgres:5432/iot_data"
db_props = {
    "user": "postgres",
    "password": "postgres",
    "driver": "org.postgresql.Driver"
}

# 💾 Função para salvar cada batch no banco
def write_to_postgres(batch_df, batch_id):
    batch_df.write.jdbc(
        url=db_url,
        table="iot_readings",
        mode="append",
        properties=db_props
    )
    print(f"✅ Batch {batch_id} gravado no Postgres com sucesso.")

# 🧠 Inicia o streaming
query = (
    agg_df.writeStream
    .foreachBatch(write_to_postgres)
    .outputMode("complete")                 # 👈 garante saída mesmo sem updates
    .option("checkpointLocation", "/tmp/spark-checkpoint")
    .trigger(processingTime="10 seconds")   # 👈 executa a cada 10s
    .start()
)

query.awaitTermination()
