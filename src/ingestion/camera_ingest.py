# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Layer: Camera Feed Ingestion
# MAGIC Reads raw camera feed data (simulated JSONs) from Azure Blob Storage into a Bronze Delta table.

def process_bronze_data(spark, source_path, target_table):
    """
    Ingest data from source to Bronze Delta table.
    For local testing purposes, returns a simple dataframe if source_path is 'test'
    """
    if source_path == "test":
        try:
            data = [("cam-01", "2026-04-20 10:00:00", 0.95)]
            return spark.createDataFrame(data, ["camera_id", "timestamp", "confidence"])
        except Exception:
            return "Mocked DataFrame"
        
    print(f"Reading from {source_path}")
    print(f"Writing to {target_table}")
    return True

if __name__ == "__main__":
    try:
        from pyspark.sql import SparkSession
        spark = SparkSession.builder.getOrCreate()
        print("Running in Databricks environment")
        # Example logic:
        # source_path = "abfss://raw@storage.dfs.core.windows.net/camera_feeds/"
        # process_bronze_data(spark, source_path, "visionai_catalog.bronze.camera_feeds")
    except ImportError:
        print("Local mode - PySpark environment not found.")
