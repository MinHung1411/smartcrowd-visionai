-- ============================================
-- BƯỚC 3: SILVER - Feature Engineering
-- Biến dữ liệu thô thành dữ liệu phân tích
-- Thêm 6 Feature mới mà Web App không có
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.detections_enriched AS
SELECT
    detection_id,
    user_id,
    username,
    image_path,
    detection_type,
    objects_json,
    capture_time,
    processing_time,

    -- ⭐ Feature 1: Giờ trong ngày
    HOUR(capture_time) AS hour_of_day,

    -- ⭐ Feature 2: Ca làm việc (Sáng/Chiều/Tối/Đêm)
    CASE
        WHEN HOUR(capture_time) BETWEEN 6 AND 11  THEN 'MORNING'
        WHEN HOUR(capture_time) BETWEEN 12 AND 17 THEN 'AFTERNOON'
        WHEN HOUR(capture_time) BETWEEN 18 AND 22 THEN 'EVENING'
        ELSE 'NIGHT'
    END AS time_shift,

    -- ⭐ Feature 3: Phân loại chức năng AI
    CASE
        WHEN detection_type = 'upload'         THEN 'Object Detection'
        WHEN detection_type = 'camera'         THEN 'Realtime Detection'
        WHEN detection_type = 'face_upload'    THEN 'Face Recognition'
        WHEN detection_type = 'color'          THEN 'Color Analysis'
        WHEN detection_type = 'classification' THEN 'Classification'
        ELSE 'Other'
    END AS ai_feature,

    -- ⭐ Feature 4: Tốc độ xử lý AI
    CASE
        WHEN processing_time < 0.1  THEN 'FAST'
        WHEN processing_time < 0.5  THEN 'NORMAL'
        WHEN processing_time < 1.0  THEN 'SLOW'
        ELSE 'VERY_SLOW'
    END AS speed_grade,

    -- ⭐ Feature 5: Ngày trong tuần (1=CN, 2=T2, ... 7=T7)
    DAYOFWEEK(capture_time) AS day_of_week,

    -- ⭐ Feature 6: Khoảng cách tính từ hôm nay (ngày)
    DATEDIFF(current_date(), DATE(capture_time)) AS days_ago,

    -- Audit
    current_timestamp() AS processed_at

FROM bronze.raw_detections;


-- Kiểm tra Silver: xem các Feature mới
SELECT
    detection_id, username, detection_type, ai_feature,
    hour_of_day, time_shift, speed_grade, days_ago
FROM silver.detections_enriched
ORDER BY capture_time DESC;