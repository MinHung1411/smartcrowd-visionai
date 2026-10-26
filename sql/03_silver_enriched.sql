-- ============================================
-- BƯỚC 3: SILVER - Feature Engineering & Crowd Analytics
-- Biến đổi dữ liệu thô thành dữ liệu phân tích lưu lượng thông minh
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS silver;

CREATE OR REPLACE TABLE silver.crowd_traffic_enriched AS
SELECT
    detection_id,
    user_id,
    username,
    detection_type,
    people_in_frame,
    total_entered,
    total_exited,
    GREATEST(0, total_entered - total_exited) AS net_occupancy,
    density_level,
    is_overcrowded,
    capture_time,
    processing_time,

    -- ⭐ Feature 1: Giờ trong ngày (0 - 23)
    HOUR(capture_time) AS hour_of_day,

    -- ⭐ Feature 2: Ca hoạt động (Sáng / Chiều / Tối / Đêm)
    CASE
        WHEN HOUR(capture_time) BETWEEN 6 AND 11  THEN 'MORNING_PEAK'
        WHEN HOUR(capture_time) BETWEEN 12 AND 16 THEN 'AFTERNOON'
        WHEN HOUR(capture_time) BETWEEN 17 AND 21 THEN 'EVENING_PEAK'
        ELSE 'NIGHT_OFFPEAK'
    END AS time_shift,

    -- ⭐ Feature 3: Phân cấp mức độ lưu lượng (Traffic Intensity)
    CASE
        WHEN people_in_frame < 5  THEN 'LIGHT'
        WHEN people_in_frame < 15 THEN 'MODERATE'
        WHEN people_in_frame < 25 THEN 'HEAVY'
        ELSE 'CRITICAL_CONGESTION'
    END AS traffic_intensity,

    -- ⭐ Feature 4: Tốc độ suy luận AI (Inference Speed Grade)
    CASE
        WHEN processing_time < 0.05 THEN 'REALTIME_FAST'
        WHEN processing_time < 0.15 THEN 'ACCEPTABLE'
        ELSE 'HIGH_LATENCY'
    END AS latency_grade,

    -- ⭐ Feature 5: Ngày trong tuần (1 = CN, 7 = T7)
    DAYOFWEEK(capture_time) AS day_of_week,

    -- ⭐ Feature 6: Phân loại Ngày thường vs Cuối tuần
    CASE 
        WHEN DAYOFWEEK(capture_time) IN (1, 7) THEN TRUE 
        ELSE FALSE 
    END AS is_weekend,

    -- Audit
    current_timestamp() AS processed_at

FROM bronze.raw_crowd_detections;