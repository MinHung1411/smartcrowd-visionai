-- ============================================
-- BƯỚC 6: Giả lập MLflow Tracking bằng SQL
-- Log thí nghiệm huấn luyện mô hình YOLOv8
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
    dataset_size    INT,
    training_time   STRING,
    status          STRING,
    created_at      TIMESTAMP DEFAULT current_timestamp()
) TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');


INSERT INTO gold.ml_experiment_log
    (run_id, experiment_name, model_name, model_version, learning_rate, batch_size, epochs, img_size, precision_score, recall_score, map50, map50_95, dataset_size, training_time, status)
VALUES
    ('run_001', '/VisionAI/yolov8', 'yolov8n', 'v1.0', 0.01,  16, 50,  640, 0.72, 0.68, 0.71, 0.45, 500,  '12m 30s', 'COMPLETED'),
    ('run_002', '/VisionAI/yolov8', 'yolov8n', 'v1.1', 0.005, 16, 100, 640, 0.78, 0.74, 0.76, 0.52, 500,  '24m 15s', 'COMPLETED'),
    ('run_003', '/VisionAI/yolov8', 'yolov8s', 'v2.0', 0.005, 32, 100, 640, 0.85, 0.81, 0.83, 0.61, 1000, '45m 00s', 'COMPLETED'),
    ('run_004', '/VisionAI/yolov8', 'yolov8s', 'v2.1', 0.001, 32, 150, 640, 0.89, 0.86, 0.88, 0.67, 1000, '1h 05m',  'COMPLETED'),
    ('run_005', '/VisionAI/yolov8', 'yolov8m', 'v3.0', 0.001, 16, 200, 640, 0.92, 0.89, 0.91, 0.72, 2000, '2h 30m',  'COMPLETED');


-- Xem kết quả training
SELECT
    run_id, model_name, model_version,
    CONCAT('lr=', learning_rate, ' bs=', batch_size, ' ep=', epochs) AS hyperparams,
    ROUND(precision_score * 100, 1) AS `Precision (%)`,
    ROUND(recall_score * 100, 1)    AS `Recall (%)`,
    ROUND(map50 * 100, 1)           AS `mAP@50 (%)`,
    ROUND(map50_95 * 100, 1)        AS `mAP@50-95 (%)`,
    status
FROM gold.ml_experiment_log
ORDER BY map50_95 DESC;