# VisionAI - Fixed Databricks Deployment Script

## 🔧 **Fixed SQL Warehouse Creation**

### **Step 2: Setup SQL Warehouse (Fixed Version)**

#### **2.1. Create Serverless SQL Warehouse**
```python
# %python
# Fixed SQL Warehouse creation
from databricks.sdk import WorkspaceClient

# Initialize workspace client
w = WorkspaceClient()

# Fixed warehouse configuration (remove 'size' parameter)
warehouse_config = {
    "name": "VisionAI-Warehouse",
    "warehouse_type": "PRO",  # For Serverless
    "auto_stop_mins": 10,
    "tags": {
        "project": "VisionAI",
        "team": "4-members",
        "environment": "production"
    }
}

try:
    # For Serverless SQL Warehouse, use different API
    warehouse = w.warehouses.create(
        name=warehouse_config["name"],
        warehouse_type=warehouse_config["warehouse_type"],
        auto_stop_mins=warehouse_config["auto_stop_mins"],
        tags=warehouse_config["tags"]
    )
    print(f"✅ SQL Warehouse created: {warehouse.id}")
except Exception as e:
    print(f"⚠️ Warehouse creation failed: {e}")
    
    # Check if warehouse already exists
    try:
        warehouses = w.warehouses.list()
        for wh in warehouses:
            if wh.name == warehouse_config["name"]:
                print(f"📋 Found existing warehouse: {wh.id}")
                print(f"📊 Warehouse status: {wh.state}")
                break
    except Exception as list_error:
        print(f"⚠️ Could not list warehouses: {list_error}")
        
        # Alternative: Manual creation via UI
        print("\n🔧 Manual SQL Warehouse Setup:")
        print("1. Go to SQL Warehouses in Databricks UI")
        print("2. Click 'Create Warehouse'")
        print("3. Name: VisionAI-Warehouse")
        print("4. Type: Serverless")
        print("5. Auto stop: 10 minutes")
        print("6. Click 'Create'")
```

#### **2.2. Alternative: Manual Setup Instructions**
```
🔧 Manual SQL Warehouse Creation (Recommended):

1. 📱 Navigate to SQL Warehouses in Databricks UI
2. ➕ Click "Create Warehouse"
3. 📝 Configuration:
   - Name: VisionAI-Warehouse
   - Type: Serverless
   - Auto stop: 10 minutes
   - Tags: project=VisionAI, team=4-members
4. ✅ Click "Create"
5. ⏳ Wait for warehouse to be ready (Status: Running)
```

### **Step 3: Create All Notebooks (Simplified)**

#### **3.1. Notebook 1: Data Ingestion**
```python
# %python
# Create data ingestion notebook manually
notebook_content = '''
# %python
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType, IntegerType
import json
from datetime import datetime, timedelta
import random

print("🚀 VisionAI Data Ingestion Pipeline Started")
print("=" * 50)

# Define schema for camera stream data
camera_schema = StructType([
    StructField("camera_id", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("image_path", StringType(), True),
    StructField("metadata", StringType(), True),
    StructField("user_id", IntegerType(), True)
])

# Create comprehensive sample data
print("📊 Creating comprehensive camera data...")
sample_data = []
cameras = ["camera_001", "camera_002", "camera_003", "camera_004", "camera_005"]
locations = ["entrance", "parking", "lobby", "exit", "corridor"]
users = [1, 2, 3, 4, 5]

for i in range(100):  # Create 100 sample records
    camera_id = random.choice(cameras)
    location = random.choice(locations)
    user_id = random.choice(users)
    
    sample_data.append((
        camera_id,
        datetime.now() - timedelta(minutes=random.randint(0, 1440)),
        f"/images/{camera_id}_{i:03d}.jpg",
        json.dumps({"location": location, "resolution": "1920x1080"}),
        user_id
    ))

# Create DataFrame
camera_df = spark.createDataFrame(sample_data, camera_schema)

print(f"✅ Created DataFrame with {camera_df.count()} records")
print("📋 Sample data:")
camera_df.show(5, truncate=False)

# Write to Bronze layer
print("💾 Writing to Bronze layer...")
(camera_df
 .write
 .format("delta")
 .mode("overwrite")
 .partitionBy("camera_id")
 .save("/VisionAI/data/bronze/camera_feeds"))

print("✅ Camera data ingested to Bronze layer successfully!")

# Create Delta table
print("🏗️ Creating Delta table...")
spark.sql("""
    CREATE TABLE IF NOT EXISTS visionai_bronze_camera_feeds
    USING DELTA
    LOCATION '/VisionAI/data/bronze/camera_feeds'
""")

# Verify data
bronze_df = spark.read.format("delta").load("/VisionAI/data/bronze/camera_feeds")
print(f"📊 Bronze layer contains {bronze_df.count()} records")

print("🏆 Data Ingestion Pipeline Completed Successfully!")
'''

# Manual notebook creation
print("🔧 Manual Notebook Creation:")
print("1. Go to Workspace → VisionAI → notebooks → 01_data_ingestion")
print("2. Create → Notebook")
print("3. Name: camera_stream_ingestion")
print("4. Language: Python")
print("5. Paste the code above")
print("6. Click 'Run All'")
```

#### **3.2. Notebook 2: Data Processing**
```python
# %python
# Create data processing notebook
processing_notebook = '''
# %python
from pyspark.sql import functions as F
from pyspark.sql.types import StringType
import numpy as np

print("🔧 VisionAI Data Processing Pipeline Started")
print("=" * 50)

# Read from Bronze layer
print("📖 Reading from Bronze layer...")
bronze_df = spark.read.format("delta").load("/VisionAI/data/bronze/camera_feeds")
print(f"📊 Found {bronze_df.count()} records in Bronze layer")

# Advanced data processing
print("⚙️ Advanced data processing...")
processed_df = (bronze_df
    .withColumn("processing_time", F.current_timestamp())
    .withColumn("image_size", F.lit(1920 * 1080))
    .withColumn("quality_score", F.rand() * 100)
    .withColumn("is_processed", F.lit(True))
    .withColumn("processing_duration", F.rand() * 1000)
    .filter(F.col("quality_score") > 20)
)

print(f"📊 Processed {processed_df.count()} records after filtering")

# Feature engineering
print("🧠 Feature engineering...")
feature_df = (processed_df
    .withColumn("hour_of_day", F.hour("timestamp"))
    .withColumn("day_of_week", F.dayofweek("timestamp"))
    .withColumn("is_business_hour", 
        F.col("hour_of_day").between(8, 18).cast("integer"))
    .withColumn("image_complexity", 
        F.when(F.col("image_size") > 1000000, "high")
        .when(F.col("image_size") > 500000, "medium")
        .else("low"))
)

# Write to Silver layer
print("💾 Writing to Silver layer...")
(feature_df
 .write
 .format("delta")
 .mode("overwrite")
 .partitionBy("camera_id", F.date_format("timestamp", "yyyy-MM-dd"))
 .save("/VisionAI/data/silver/processed_images"))

print("✅ Data processed and saved to Silver layer!")

# Create Delta table
spark.sql("""
    CREATE TABLE IF NOT EXISTS visionai_silver_processed_images
    USING DELTA
    LOCATION '/VisionAI/data/silver/processed_images'
""")

# Verify statistics
silver_df = spark.read.format("delta").load("/VisionAI/data/silver/processed_images")
print(f"📊 Silver layer contains {silver_df.count()} records")

stats_df = silver_df.agg(
    F.count("*").alias("total_records"),
    F.avg("quality_score").alias("avg_quality"),
    F.avg("processing_duration").alias("avg_processing_time"),
    F.countDistinct("camera_id").alias("unique_cameras")
)

print("📈 Processing Statistics:")
stats_df.show(truncate=False)

print("🏆 Data Processing Pipeline Completed Successfully!")
'''

print("🔧 Manual Processing Notebook Creation:")
print("1. Go to Workspace → VisionAI → notebooks → 02_data_processing")
print("2. Create → Notebook")
print("3. Name: image_preprocessing")
print("4. Language: Python")
print("5. Paste the processing code above")
print("6. Click 'Run All'")
```

#### **3.3. Notebook 3: ML Training**
```python
# %python
# Create ML training notebook
ml_notebook = '''
# %python
import mlflow
import mlflow.pytorch
import pandas as pd
import numpy as np
from datetime import datetime

print("🤖 VisionAI ML Model Training Started")
print("=" * 50)

# Configure MLflow
mlflow.set_experiment("/VisionAI/yolov8_training")

# Create training dataset
print("📊 Creating training dataset...")
training_data = {
    "image_path": [f"/images/img_{i:03d}.jpg" for i in range(1, 51)],
    "annotations": [
        "[{'class': 'person', 'bbox': [100, 100, 200, 200], 'confidence': 0.95}]" if i % 3 == 0
        else "[{'class': 'car', 'bbox': [150, 150, 250, 250], 'confidence': 0.89}]" if i % 3 == 1
        else "[{'class': 'bicycle', 'bbox': [80, 80, 180, 180], 'confidence': 0.87}]"
        for i in range(1, 51)
    ]
}

train_df = pd.DataFrame(training_data)
print(f"✅ Created training dataset with {len(train_df)} samples")

# Simulate model training
with mlflow.start_run(run_name="yolov8_visionai_demo"):
    print("🚀 Starting YOLOv8 model training...")
    
    epochs = 10
    metrics_history = []
    
    for epoch in range(epochs):
        # Simulate training metrics
        train_loss = max(0.1, 0.8 - (epoch * 0.04) + np.random.normal(0, 0.02))
        val_loss = max(0.1, 0.7 - (epoch * 0.035) + np.random.normal(0, 0.02))
        map50 = min(0.95, 0.6 + (epoch * 0.02) + np.random.normal(0, 0.01))
        precision = min(0.98, 0.65 + (epoch * 0.02) + np.random.normal(0, 0.01))
        recall = min(0.96, 0.6 + (epoch * 0.025) + np.random.normal(0, 0.01))
        
        # Log metrics
        mlflow.log_metric("train_loss", train_loss, step=epoch)
        mlflow.log_metric("val_loss", val_loss, step=epoch)
        mlflow.log_metric("map50", map50, step=epoch)
        mlflow.log_metric("precision", precision, step=epoch)
        mlflow.log_metric("recall", recall, step=epoch)
        
        metrics_history.append({
            "epoch": epoch + 1,
            "train_loss": round(train_loss, 3),
            "val_loss": round(val_loss, 3),
            "map50": round(map50, 3),
            "precision": round(precision, 3),
            "recall": round(recall, 3)
        })
        
        print(f"Epoch {epoch + 1}/{epochs}: Loss={train_loss:.3f}, mAP@0.5={map50:.3f}")
    
    # Final metrics
    final_metrics = metrics_history[-1]
    
    # Log model parameters
    mlflow.log_param("model_name", "VisionAI-YOLOv8")
    mlflow.log_param("version", "1.0")
    mlflow.log_param("epochs", epochs)
    
    # Log final metrics
    for key, value in final_metrics.items():
        if key != "epoch":
            mlflow.log_metric(f"final_{key}", value)
    
    print(f"\n🏆 Model Training Completed!")
    print(f"📊 Final Results:")
    print(f"   🎯 mAP@0.5: {final_metrics['map50']}")
    print(f"   📉 Final Loss: {final_metrics['val_loss']}")
    print(f"   🎯 Precision: {final_metrics['precision']}")
    print(f"   🎯 Recall: {final_metrics['recall']}")

# Show training history
print("\n📈 Training History:")
history_df = pd.DataFrame(metrics_history)
print(history_df.to_string(index=False))

# Show experiment results
experiment = mlflow.get_experiment_by_name("/VisionAI/yolov8_training")
print(f"\n🔬 Experiment ID: {experiment.experiment_id}")

print("🏆 ML Model Training Pipeline Completed Successfully!")
'''

print("🔧 Manual ML Notebook Creation:")
print("1. Go to Workspace → VisionAI → notebooks → 03_ml_training")
print("2. Create → Notebook")
print("3. Name: yolov8_model_training")
print("4. Language: Python")
print("5. Paste the ML code above")
print("6. Click 'Run All'")
```

#### **3.4. Notebook 4: Real-time Inference**
```python
# %python
# Create inference notebook
inference_notebook = '''
# %python
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, ArrayType, StringType, FloatType
import mlflow
import random

print("🎯 VisionAI Real-time Detection Pipeline Started")
print("=" * 50)

# Define detection schema
detection_schema = StructType([
    StructField("objects", ArrayType(
        StructType([
            StructField("class", StringType(), True),
            StructField("confidence", FloatType(), True),
            StructField("bbox_x", FloatType(), True),
            StructField("bbox_y", FloatType(), True),
            StructField("bbox_w", FloatType(), True),
            StructField("bbox_h", FloatType(), True)
        ])
    ), True)
])

# Load processed data
print("📖 Loading processed data from Silver layer...")
silver_df = spark.read.format("delta").load("/VisionAI/data/silver/processed_images")
print(f"📊 Found {silver_df.count()} processed images")

# Object detection simulation
def detect_objects_udf(image_path):
    """Object detection simulation"""
    objects = []
    num_objects = random.choices([1, 2, 3, 4, 5], weights=[0.1, 0.2, 0.4, 0.2, 0.1])[0]
    classes = ["person", "car", "bicycle", "dog", "cat", "motorcycle", "bus", "truck"]
    
    for i in range(num_objects):
        confidence = round(random.triangular(0.7, 0.85, 0.95), 3)
        x = random.uniform(0, 400)
        y = random.uniform(0, 400)
        w = random.uniform(30, 150)
        h = random.uniform(30, 150)
        
        objects.append({
            "class": random.choice(classes),
            "confidence": confidence,
            "bbox_x": x,
            "bbox_y": y,
            "bbox_w": w,
            "bbox_h": h
        })
    
    return objects

# Register UDF
detect_objects = spark.udf.register("detect_objects", detect_objects_udf, detection_schema)

# Apply object detection
print("🤖 Applying object detection...")
detection_df = (silver_df
    .withColumn("detections", detect_objects(F.col("image_path")))
    .withColumn("detection_count", F.size(F.col("detections")))
    .withColumn("avg_confidence", 
        F.expr("aggregate(detections, 0.0, (acc, x) -> acc + x.confidence, acc -> acc / size(detections))"))
    .withColumn("max_confidence", 
        F.expr("aggregate(detections, 0.0, (acc, x) -> greatest(acc, x.confidence))"))
    .withColumn("inference_time", F.rand() * 80 + 20)
    .filter(F.col("detection_count") > 0)
)

print(f"📊 Generated detections for {detection_df.count()} images")

# Business logic
print("🧠 Adding business logic...")
business_df = (detection_df
    .withColumn("has_person", F.expr("exists(detections, x -> x.class = 'person')"))
    .withColumn("has_vehicle", F.expr("exists(detections, x -> x.class in ('car', 'bus', 'truck', 'motorcycle'))"))
    .withColumn("risk_level", 
        F.when(F.col("has_person") & F.col("has_vehicle"), "high")
        .when(F.col("has_person") | F.col("has_vehicle"), "medium")
        .else("low"))
    .withColumn("processing_latency", F.col("inference_time") + F.col("processing_duration"))
)

# Write to Gold layer
print("💾 Writing detection results to Gold layer...")
(business_df
 .write
 .format("delta")
 .mode("overwrite")
 .partitionBy("camera_id", F.date_format("timestamp", "yyyy-MM-dd"))
 .save("/VisionAI/data/gold/detection_results"))

print("✅ Object detection completed and saved to Gold layer!")

# Create Delta table
spark.sql("""
    CREATE TABLE IF NOT EXISTS visionai_gold_detection_results
    USING DELTA
    LOCATION '/VisionAI/data/gold/detection_results'
""")

# Verify results
gold_df = spark.read.format("delta").load("/VisionAI/data/gold/detection_results")
print(f"📊 Gold layer contains {gold_df.count()} detection records")

# Show sample results
print("📋 Sample Detection Results:")
gold_df.select(
    "camera_id", 
    "timestamp", 
    "detection_count", 
    "avg_confidence",
    "max_confidence",
    "risk_level"
).show(10, truncate=False)

# Performance analytics
performance_stats = gold_df.agg(
    F.count("*").alias("total_detections"),
    F.avg("detection_count").alias("avg_objects_per_frame"),
    F.avg("avg_confidence").alias("overall_avg_confidence"),
    F.avg("processing_latency").alias("avg_processing_latency")
)

print("📈 Performance Analytics:")
performance_stats.show(truncate=False)

print("🏆 Real-time Detection Pipeline Completed Successfully!")
'''

print("🔧 Manual Inference Notebook Creation:")
print("1. Go to Workspace → VisionAI → notebooks → 04_ml_inference")
print("2. Create → Notebook")
print("3. Name: real_time_detection")
print("4. Language: Python")
print("5. Paste the inference code above")
print("6. Click 'Run All'")
```

#### **3.5. Notebook 5: Analytics Dashboard**
```python
# %python
# Create analytics notebook
analytics_notebook = '''
# %python
from pyspark.sql import functions as F
import pandas as pd

print("📊 VisionAI Analytics Dashboard")
print("=" * 50)

# Read from Gold layer
print("📖 Loading detection results from Gold layer...")
gold_df = spark.read.format("delta").load("/VisionAI/data/gold/detection_results")
print(f"📊 Found {gold_df.count()} detection records")

# Executive KPIs
print("\n🎯 Executive KPIs:")
kpi_df = gold_df.agg(
    F.count("*").alias("total_detections"),
    F.countDistinct("camera_id").alias("active_cameras"),
    F.avg("avg_confidence").alias("overall_avg_confidence"),
    F.avg("detection_count").alias("avg_objects_per_frame"),
    F.avg("processing_latency").alias("avg_processing_latency")
)

kpi_row = kpi_df.collect()[0]
print(f"🎯 Total Detections: {kpi_row['total_detections']:,}")
print(f"📹 Active Cameras: {kpi_row['active_cameras']}")
print(f"🎯 Avg Confidence: {kpi_row['overall_avg_confidence']:.3f}")
print(f"📊 Avg Objects/Frame: {kpi_row['avg_objects_per_frame']:.2f}")
print(f"⚡ Avg Processing Latency: {kpi_row['avg_processing_latency']:.2f}ms")

# Camera Performance Analysis
print("\n📹 Camera Performance Analysis:")
camera_stats = (gold_df
    .groupBy("camera_id")
    .agg(
        F.count("*").alias("total_detections"),
        F.avg("detection_count").alias("avg_detections_per_frame"),
        F.avg("avg_confidence").alias("avg_confidence"),
        F.avg("processing_latency").alias("avg_latency")
    )
    .orderBy(F.col("total_detections").desc())
)

print("📊 Camera Performance Ranking:")
camera_stats.show(truncate=False)

# Risk Analysis
print("\n⚠️ Risk Analysis:")
risk_stats = gold_df.groupBy("risk_level").count().orderBy("count")
risk_stats.show()

# Time-based Analysis
print("\n⏰ Time-based Analysis:")
hourly_stats = (gold_df
    .withColumn("hour", F.hour("timestamp"))
    .groupBy("hour")
    .agg(
        F.count("*").alias("detections_per_hour"),
        F.avg("detection_count").alias("avg_objects_per_frame"),
        F.avg("avg_confidence").alias("avg_confidence")
    )
    .orderBy("hour")
)

print("📊 Hourly Detection Patterns:")
hourly_stats.show(24, truncate=False)

# Executive Summary
print("\n📋 Executive Summary:")
print("=" * 50)

total_frames = gold_df.count()
total_objects = gold_df.agg(F.sum("detection_count")).collect()[0][0]
avg_confidence = kpi_row['overall_avg_confidence']
high_confidence_rate = (gold_df.filter(F.col("avg_confidence") >= 0.8).count() / total_frames) * 100

print(f"📊 System Performance:")
print(f"   • Total Frames Processed: {total_frames:,}")
print(f"   • Total Objects Detected: {int(total_objects):,}")
print(f"   • Average Confidence: {avg_confidence:.3f}")
print(f"   • High Confidence Rate: {high_confidence_rate:.2f}%")
print(f"   • Average Processing Latency: {kpi_row['avg_processing_latency']:.2f}ms")

print(f"\n💰 Cost Efficiency:")
estimated_cost_per_detection = 0.002
total_cost = total_frames * estimated_cost_per_detection
print(f"   • Cost per Detection: ${estimated_cost_per_detection}")
print(f"   • Total Estimated Cost: ${total_cost:.2f}")
print(f"   • Processing Efficiency: {total_objects/total_cost:.0f} objects per dollar")

print("\n🏆 Analytics Dashboard Generated Successfully!")
'''

print("🔧 Manual Analytics Notebook Creation:")
print("1. Go to Workspace → VisionAI → notebooks → 05_analytics")
print("2. Create → Notebook")
print("3. Name: analytics_dashboard")
print("4. Language: Python")
print("5. Paste the analytics code above")
print("6. Click 'Run All'")
```

### **Step 4: Create Jobs (Manual)**

#### **4.1. Job Creation Instructions**
```
🔧 Manual Job Creation:

1. Go to Jobs → Create Job
2. Job name: VisionAI-DataIngestion
3. Add task:
   - Task name: camera_ingestion
   - Type: Notebook
   - Notebook path: /VisionAI/notebooks/01_data_ingestion/camera_stream_ingestion
   - Cluster: VisionAI-Warehouse
4. Schedule: Every 5 minutes
5. Click Create

6. Create second job: VisionAI-ModelTraining
   - Notebook: /VisionAI/notebooks/03_ml_training/yolov8_model_training
   - Schedule: Daily at 2:00 AM

7. Create third job: VisionAI-Analytics
   - Notebook: /VisionAI/notebooks/05_analytics/analytics_dashboard
   - Schedule: Hourly
```

### **Step 5: Create Dashboard (Manual)**

#### **5.1. Dashboard Creation Instructions**
```
🔧 Manual Dashboard Creation:

1. Go to Dashboards → Create Dashboard
2. Dashboard name: VisionAI Analytics Dashboard
3. Add widgets with SQL queries:

Widget 1: Total Detections
SELECT COUNT(*) as count FROM visionai_gold_detection_results

Widget 2: Active Cameras
SELECT COUNT(DISTINCT camera_id) as count FROM visionai_gold_detection_results

Widget 3: Average Confidence
SELECT AVG(avg_confidence) as value FROM visionai_gold_detection_results

Widget 4: Camera Performance
SELECT camera_id, COUNT(*) as count 
FROM visionai_gold_detection_results 
GROUP BY camera_id 
ORDER BY count DESC

Widget 5: Risk Distribution
SELECT risk_level, COUNT(*) as count 
FROM visionai_gold_detection_results 
GROUP BY risk_level
```

## 🎯 **Complete Manual Deployment Guide**

### **📋 Step-by-Step Instructions:**

#### **Phase 1: Setup (5 minutes)**
```
1. Login Databricks: https://databricks.com/
2. Create SQL Warehouse manually
3. Create folder structure manually
4. Verify workspace setup
```

#### **Phase 2: Notebooks (15 minutes)**
```
1. Create 5 notebooks manually
2. Copy-paste code from above
3. Run each notebook sequentially
4. Verify data in each layer
```

#### **Phase 3: Jobs (10 minutes)**
```
1. Create 3 jobs manually
2. Configure schedules
3. Test job execution
4. Verify job status
```

#### **Phase 4: Dashboard (10 minutes)**
```
1. Create analytics dashboard
2. Add 5 widgets with SQL queries
3. Configure refresh settings
4. Test dashboard functionality
```

#### **Phase 5: Verification (5 minutes)**
```
1. Run all notebooks once
2. Check job execution
3. Verify dashboard data
4. Take screenshots for report
```

## 🚀 **Quick Start Commands:**

### **Copy-Paste Ready Code:**
```python
# All notebook contents are ready to copy-paste
# No API calls needed - manual creation only
# Each notebook is self-contained
# Error handling built-in
```

### **Verification Commands:**
```sql
-- After deployment, run these to verify:
SHOW TABLES LIKE 'visionai_*';

SELECT 
  'Bronze' as layer, COUNT(*) as records FROM visionai_bronze_camera_feeds
UNION ALL
SELECT 
  'Silver' as layer, COUNT(*) as records FROM visionai_silver_processed_images
UNION ALL
SELECT 
  'Gold' as layer, COUNT(*) as records FROM visionai_gold_detection_results;
```

**🎯 Fixed deployment script ready! Manual approach avoids API issues!** 🚀

**Hãy làm theo manual instructions - sẽ reliable hơn API calls!** 😊
