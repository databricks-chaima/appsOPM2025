# Databricks notebook source
# MAGIC %md
# MAGIC # Load Mock Data to Delta Tables
# MAGIC
# MAGIC This notebook loads the CCD Welding Quality Control mock data into Delta tables in Unity Catalog.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Unity Catalog configuration
CATALOG = "serverless_opm_catalog"
SCHEMA = "opm"

# Table names
FACTORIES_TABLE = f"{CATALOG}.{SCHEMA}.factories"
INSPECTIONS_TABLE = f"{CATALOG}.{SCHEMA}.inspections"

print(f"Target tables:")
print(f"  - {FACTORIES_TABLE}")
print(f"  - {INSPECTIONS_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Define Schemas

# COMMAND ----------

from pyspark.sql.types import (
    StructType, StructField, StringType, TimestampType, 
    DoubleType, IntegerType, DateType, ArrayType
)

# Factories schema
factories_schema = StructType([
    StructField("factory_id", StringType(), False),
    StructField("region", StringType(), False),
    StructField("cameras", ArrayType(StringType()), False)
])

# Inspections schema (matching the exact schema provided)
inspections_schema = StructType([
    StructField("inspection_id", StringType(), False),
    StructField("factory_id", StringType(), False),
    StructField("camera_id", StringType(), False),
    StructField("timestamp", TimestampType(), False),
    StructField("image_path", StringType(), False),
    StructField("prediction", StringType(), False),
    StructField("confidence_score", DoubleType(), False),
    StructField("defect_type", StringType(), True),
    StructField("inference_time_ms", IntegerType(), False),
    StructField("model_version", StringType(), False),
    StructField("date", DateType(), False)
])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Generate Mock Data

# COMMAND ----------

import random
from datetime import datetime, timedelta

# Factory configuration
FACTORIES = [
    "WUH-G426", "WUH-A79", "WUH-L42P", "WUH-BX11", "WUH-KX11",
    "YAN-YT01", "YAN-YT02", "YAN-YT03", "YAN-YT04", "YAN-YT05",
    "NGB-NB10", "NGB-NB11", "NGB-NB12", "NGB-NB13", "NGB-NB14",
    "GUA-GZ01", "GUA-GZ02", "GUA-GZ03", "GUA-GZ04", "GUA-GZ05",
    "SHE-SY01", "SHE-SY02", "SHE-SY03", "SHE-SY04", "SHE-SY05",
    "KYO-KY01", "KYO-KY02", "KYO-KY03", "KYO-KY04", "KYO-KY05",
    "RAY-RY01", "RAY-RY02", "RAY-RY03", "RAY-RY04", "RAY-RY05",
    "SHA-SH01", "SHA-SH02", "SHA-SH03", "SHA-SH04", "SHA-SH05",
]

CAMERAS = ["CAM-01", "CAM-02"]

DEFECT_TYPES = [
    "weld_crack", "porosity", "undercut", "spatter",
    "incomplete_fusion", "burn_through", "misalignment"
]

MODEL_VERSIONS = ["v2.3.1", "v2.3.0", "v2.2.5"]

IMAGE_VOLUME_PATH = "/Volumes/serverless_opm_catalog/opm/quality/images-highres"
NUM_PHOTOS = 10

# COMMAND ----------

# Generate factories data
factories_data = []
for factory_id in FACTORIES:
    region = factory_id.split("-")[0]
    factories_data.append({
        "factory_id": factory_id,
        "region": region,
        "cameras": CAMERAS
    })

print(f"Generated {len(factories_data)} factories")

# COMMAND ----------

# Generate inspections data
NUM_RECORDS = 500

inspections_data = []
end_time = datetime.now()
start_time = end_time - timedelta(days=7)

for i in range(NUM_RECORDS):
    # Random timestamp
    random_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
    timestamp = start_time + timedelta(seconds=random_seconds)
    
    # Random factory and camera
    factory_id = random.choice(FACTORIES)
    camera_id = random.choice(CAMERAS)
    
    # Prediction: 95% OK, 5% KO
    is_ok = random.random() < 0.95
    prediction = "OK" if is_ok else "KO"
    
    # Confidence score
    confidence_score = round(random.uniform(0.92, 0.99), 4) if is_ok else round(random.uniform(0.75, 0.95), 4)
    
    # Defect type (null if OK)
    defect_type = None if is_ok else random.choice(DEFECT_TYPES)
    
    # Image path (cycling through photo1.jpg to photo10.jpg)
    photo_num = (i % NUM_PHOTOS) + 1
    image_path = f"{IMAGE_VOLUME_PATH}/photo{photo_num}.jpg"
    
    inspections_data.append({
        "inspection_id": f"INSP-2025-{i+1:06d}",
        "factory_id": factory_id,
        "camera_id": camera_id,
        "timestamp": timestamp,
        "image_path": image_path,
        "prediction": prediction,
        "confidence_score": confidence_score,
        "defect_type": defect_type,
        "inference_time_ms": random.randint(45, 180),
        "model_version": random.choice(MODEL_VERSIONS),
        "date": timestamp.date()
    })

print(f"Generated {len(inspections_data)} inspections")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create DataFrames

# COMMAND ----------

# Create factories DataFrame
factories_df = spark.createDataFrame(factories_data, schema=factories_schema)
display(factories_df)

# COMMAND ----------

# Create inspections DataFrame
inspections_df = spark.createDataFrame(inspections_data, schema=inspections_schema)
display(inspections_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Write to Delta Tables

# COMMAND ----------

# Create schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")

# COMMAND ----------

# Write factories table
factories_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(FACTORIES_TABLE)

print(f"Created table: {FACTORIES_TABLE}")

# COMMAND ----------

# Write inspections table
inspections_df.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable(INSPECTIONS_TABLE)

print(f"Created table: {INSPECTIONS_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Tables

# COMMAND ----------

# Verify factories table
print(f"Factories table count: {spark.table(FACTORIES_TABLE).count()}")
display(spark.table(FACTORIES_TABLE).limit(5))

# COMMAND ----------

# Verify inspections table
print(f"Inspections table count: {spark.table(INSPECTIONS_TABLE).count()}")
display(spark.table(INSPECTIONS_TABLE).limit(10))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Table Statistics

# COMMAND ----------

# Inspections by prediction
display(
    spark.table(INSPECTIONS_TABLE)
    .groupBy("prediction")
    .count()
    .orderBy("prediction")
)

# COMMAND ----------

# Inspections by factory (top 10)
display(
    spark.table(INSPECTIONS_TABLE)
    .groupBy("factory_id")
    .count()
    .orderBy("count", ascending=False)
    .limit(10)
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done!
# MAGIC
# MAGIC Tables created:
# MAGIC - `serverless_opm_catalog.opm.factories` - Factory master data
# MAGIC - `serverless_opm_catalog.opm.inspections` - Inspection records with image paths
# MAGIC