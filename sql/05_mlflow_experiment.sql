-- ============================================
-- BƯỚC 5: MLflow Model Tracking & Benchmark Evaluation
-- Nhật ký thí nghiệm huấn luyện mô hình YOLOv11 trên CrowdHuman
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE TABLE gold.ml_experiment_log (
    run_id          STRING,
    experiment_name STRING,
    model_name      STRING,
    model_version   STRING,
    learning_rate   DOUBLE,
    batch_size      INT,
    epochs          INT,
    img_size        INT,
    precision_score DOUBLE,
    recall_score    DOUBLE,
    map50           DOUBLE,
    map50_95        DOUBLE,
    dataset_name    STRING,
    dataset_size    INT,
    training_time   STRING,
    status          STRING,
    created_at      TIMESTAMP DEFAULT current_timestamp()
) TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');


INSERT INTO gold.ml_experiment_log
    (run_id, experiment_name, model_name, model_version, learning_rate, batch_size, epochs, img_size, precision_score, recall_score, map50, map50_95, dataset_name, dataset_size, training_time, status)
VALUES
    ('run_001_baseline', '/SmartCrowd/YOLOv8',  'yolov8n',  'v1.0', 0.01,  16, 50, 640, 0.720, 0.680, 0.710, 0.450, 'COCO-Person', 5000,   '1h 10m', 'COMPLETED'),
    ('run_002_yolov8m',  '/SmartCrowd/YOLOv8',  'yolov8m',  'v1.2', 0.005, 16, 50, 640, 0.810, 0.795, 0.825, 0.610, 'CrowdHuman',  15000,  '3h 45m', 'COMPLETED'),
    ('run_003_yolov10m', '/SmartCrowd/YOLOv10', 'yolov10m', 'v2.0', 0.003, 16, 50, 640, 0.845, 0.830, 0.865, 0.670, 'CrowdHuman',  15000,  '3h 20m', 'COMPLETED'),
    ('run_004_yolov11s', '/SmartCrowd/YOLOv11', 'yolov11s', 'v3.0', 0.001, 32, 50, 640, 0.860, 0.855, 0.910, 0.745, 'CrowdHuman',  15000,  '2h 30m', 'COMPLETED'),
    ('run_005_champion', '/SmartCrowd/YOLOv11', 'yolov11m', 'v3.1', 0.001, 16, 50, 640, 0.880, 0.901, 0.958, 0.848, 'CrowdHuman',  15000,  '4h 15m', 'CHAMPION_SERVED');


-- Bảng xếp hạng mô hình
SELECT
    run_id, model_name, model_version, dataset_name,
    CONCAT('lr=', learning_rate, ' | bs=', batch_size, ' | ep=', epochs) AS hyperparameters,
    ROUND(precision_score * 100, 1) AS `Precision (%)`,
    ROUND(recall_score * 100, 1)    AS `Recall (%)`,
    ROUND(map50 * 100, 1)           AS `mAP@50 (%)`,
    ROUND(map50_95 * 100, 1)        AS `mAP@50-95 (%)`,
    status
FROM gold.ml_experiment_log
ORDER BY map50 DESC;