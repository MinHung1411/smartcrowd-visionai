# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer & Model Training: YOLOv8
# MAGIC Simulates YOLOv8 training and logs metrics using MLflow.

import random

def train_yolov8_simulated():
    print("Starting simulated YOLOv8 training...")
    try:
        import mlflow
        mlflow.set_experiment("/VisionAI/yolov8")
        
        with mlflow.start_run() as run:
            # Simulate params
            mlflow.log_param("epochs", 50)
            mlflow.log_param("learning_rate", 0.01)
            
            # Simulate metrics
            for epoch in range(50):
                loss = random.uniform(0.1, 0.5) / (epoch + 1)
                map50 = min(0.95, 0.5 + (epoch * 0.01))
                mlflow.log_metric("loss", loss, step=epoch)
                mlflow.log_metric("mAP50", map50, step=epoch)
                
            print("Training complete. Registering model to Model Registry...")
            # Simulate registration
            # mlflow.register_model(model_uri=f"runs:/{run.info.run_id}/model", name="VisionAI_YOLOv8")
    except ImportError:
        print("MLflow not installed. Simulating locally...")
        for epoch in range(5):
            print(f"Epoch {epoch}: loss={random.uniform(0.1, 0.5):.4f}")

if __name__ == "__main__":
    try:
        train_yolov8_simulated()
    except Exception as e:
        print(f"Error during training: {e}")
