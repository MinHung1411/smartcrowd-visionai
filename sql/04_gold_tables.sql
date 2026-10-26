-- ============================================
-- BƯỚC 4: GOLD - Bảng Tổng Hợp Phân Tích Dành Cho Dashboard & BI
-- 4 Bảng Gold chuyên sâu cho Hệ Thống SmartCrowd AI
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS gold;

-- Gold 1: Phân tích Lưu lượng Người theo Từng Giờ trong Ngày (Line / Bar Chart)
CREATE OR REPLACE TABLE gold.hourly_crowd_traffic AS
SELECT
    hour_of_day,
    time_shift,
    COUNT(*)                              AS total_frames_analyzed,
    ROUND(AVG(people_in_frame), 1)        AS avg_people_present,
    MAX(people_in_frame)                  AS peak_crowd_size,
    SUM(total_entered)                    AS total_inflow,
    SUM(total_exited)                     AS total_outflow,
    SUM(CASE WHEN is_overcrowded THEN 1 ELSE 0 END) AS alert_triggers_count
FROM silver.crowd_traffic_enriched
GROUP BY hour_of_day, time_shift
ORDER BY hour_of_day;


-- Gold 2: Thống kê Mật độ & Lưu lượng theo Ca Hoạt Động (Pie / Doughnut Chart)
CREATE OR REPLACE TABLE gold.shift_occupancy_summary AS
SELECT
    time_shift,
    COUNT(*)                              AS total_sessions,
    ROUND(AVG(people_in_frame), 1)        AS avg_crowd_density,
    MAX(people_in_frame)                  AS max_recorded_density,
    ROUND(AVG(net_occupancy), 1)          AS avg_net_occupancy,
    SUM(CASE WHEN is_overcrowded THEN 1 ELSE 0 END) AS total_overcrowded_incidents
FROM silver.crowd_traffic_enriched
GROUP BY time_shift
ORDER BY
    CASE time_shift
        WHEN 'MORNING_PEAK'  THEN 1
        WHEN 'AFTERNOON'     THEN 2
        WHEN 'EVENING_PEAK'  THEN 3
        WHEN 'NIGHT_OFFPEAK' THEN 4
    END;


-- Gold 3: Nhật Ký Cảnh Báo An Toàn Quá Tải Đám Đông (Safety Violation Log)
CREATE OR REPLACE TABLE gold.overcrowding_safety_alerts AS
SELECT
    detection_id,
    capture_time,
    time_shift,
    people_in_frame,
    traffic_intensity,
    username,
    processing_time
FROM silver.crowd_traffic_enriched
WHERE is_overcrowded = TRUE
ORDER BY capture_time DESC;


-- Gold 4: Đo lường Hiệu Năng AI & Tốc Độ Xử Lý Thời Gian Thực (Performance KPI)
CREATE OR REPLACE TABLE gold.ai_inference_performance AS
SELECT
    detection_type,
    latency_grade,
    COUNT(*)                              AS total_inferences,
    ROUND(AVG(processing_time) * 1000, 1) AS avg_latency_ms,
    ROUND(MIN(processing_time) * 1000, 1) AS min_latency_ms,
    ROUND(MAX(processing_time) * 1000, 1) AS max_latency_ms,
    ROUND(1.0 / NULLIF(AVG(processing_time), 0), 1) AS estimated_fps
FROM silver.crowd_traffic_enriched
GROUP BY detection_type, latency_grade
ORDER BY total_inferences DESC;