-- ============================================
-- BƯỚC 2: BRONZE - Raw Crowd Traffic & Tracking Events
-- Lưu trữ toàn bộ dữ liệu thô từ hệ thống SmartCrowd AI
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS bronze;

-- Bronze View: Kết hợp detections + users (giữ nguyên dữ liệu thô)
CREATE OR REPLACE VIEW bronze.raw_crowd_detections AS
SELECT
    d.id                  AS detection_id,
    d.user_id,
    u.username,
    u.email,
    d.image_path,
    d.detection_type,
    d.current_count       AS people_in_frame,
    d.in_count            AS total_entered,
    d.out_count           AS total_exited,
    d.density_level,
    d.alert_triggered     AS is_overcrowded,
    d.objects_detected    AS objects_json,
    d.confidence_scores   AS confidence_json,
    d.timestamp           AS capture_time,
    d.processing_time
FROM default.detections d
LEFT JOIN default.users u ON d.user_id = u.id;

-- Kiểm tra Bronze
SELECT * FROM bronze.raw_crowd_detections ORDER BY capture_time DESC;