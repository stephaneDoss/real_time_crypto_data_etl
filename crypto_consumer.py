import os
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import from_json, col, to_timestamp, lower, avg
from pyspark.sql.types import StructType, StringType, DoubleType
import logging


# Configurer les logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_spark_session():
    """
    Initialise et retourne une SparkSession.
    """
    return SparkSession.builder \
        .appName("CryptoViz") \
        .master("spark://spark-master:7077") \
        .config("spark.mongodb.read.connection.uri", os.getenv('MONGODB_URI')) \
        .config("spark.mongodb.write.connection.uri", os.getenv('MONGODB_URI')) \
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.13:3.0.0") \
        .getOrCreate()


def read_from_kafka(spark):
    """
    Lit les données depuis Kafka et retourne un DataFrame.
    """
    return spark \
        .readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", os.getenv('KAFKA_BOOTSTRAP_SERVERS')) \
        .option("subscribe", "CryptoData") \
        .load() \
        .selectExpr("CAST(value AS STRING)")


def parse_json(df, schema):
    """
    Parse les données JSON avec le schéma défini.
    """
    return df.withColumn("value", from_json(col("value"), schema)) \
             .select(col("value.*")) \
             .withColumn("timestamp", to_timestamp(col("timestamp"))) \
             .withColumn("symbol", lower(col("symbol")))


def write_to_mongo(df, epoch_id, collection_name):
    """
    Écrit le DataFrame donné dans la collection MongoDB spécifiée.
    """
    df.write.format("mongo").mode("append").options(
        timeseries={"timeField": "timestamp"}
    ).option("spark.mongodb.output.uri", f"{os.getenv('MONGODB_URI')}/{collection_name}?retryWrites=true&w=majority").save()


def define_aggregations(df):
    """
    Définit les agrégations de fenêtre pour différentes durées.
    """
    window_durations = {
        "10s": "10 seconds",
        "1min": "1 minute",
        "5min": "5 minutes",
        "15min": "15 minutes",
        "30min": "30 minutes",
        "1h": "1 hour",
        "1d": "1 day",
        "1w": "1 week"
    }

    aggregations = {}
    for key, duration in window_durations.items():
        aggregations[key] = df.withWatermark("timestamp", duration) \
                              .groupBy(window("timestamp", duration), "symbol") \
                              .agg(avg("price").alias(f"avg_price_{key}"))

    return aggregations


def start_queries(aggregations):
    """
    Démarre les requêtes de streaming pour chaque agrégation définie.
    """
    queries = {}
    for key, df_agg in aggregations.items():
        collection_name = f"Crypto.aggregated_{key}"
        queries[key] = df_agg \
            .writeStream \
            .trigger(processingTime=key) \
            .outputMode("update") \
            .foreachBatch(lambda df, epoch_id: write_to_mongo(df, epoch_id, collection_name)) \
            .start()
    return queries


def main():
    """
    Point d'entrée principal du script.
    """
    # Récupérer les URI de connexion depuis les variables d'environnement
    if not os.getenv('MONGODB_URI') or not os.getenv('KAFKA_BOOTSTRAP_SERVERS'):
        logger.error(
            "Les variables d'environnement MONGODB_URI et KAFKA_BOOTSTRAP_SERVERS doivent être définies.")
        return

    spark = get_spark_session()

    schema = StructType() \
        .add("symbol", StringType()) \
        .add("logo", StringType()) \
        .add("price", DoubleType()) \
        .add("variation_1h", DoubleType()) \
        .add("variation_24h", DoubleType()) \
        .add("variation_7d", DoubleType()) \
        .add("capitalisation_boursiere", DoubleType()) \
        .add("volume", DoubleType()) \
        .add("timestamp", StringType())

    kafka_df = read_from_kafka(spark)
    parsed_df = parse_json(kafka_df, schema)
    aggregations = define_aggregations(parsed_df)
    queries = start_queries(aggregations)

    # Attendre la terminaison des requêtes
    for query in queries.values():
        query.awaitTermination()


if __name__ == "__main__":
    main()
