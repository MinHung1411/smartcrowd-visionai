-- ============================================
-- BƯỚC 4: GOLD - Tổng hợp cho Dashboard
-- 4 bảng Gold siêu nhẹ, sẵn sàng vẽ biểu đồ
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS gold;

-- Gold 1: Thống kê theo Chức năng AI (Bar Chart)
CREATE OR REPLACE TABLE gold.detection_by_feature AS
SELECT
    ai_feature,
    detection_type,
    COUNT(*)                        AS total_detections,
    ROUND(AVG(processing_time), 3)  AS avg_processing_sec,
    COUNT(DISTINCT username)        AS unique_users
FROM silver.detections_enriched
GROUP BY ai_feature, detection_type
ORDER BY total_detections DESC;


-- Gold 2: Thống kê theo Ca làm việc (Pie Chart)
CREATE OR REPLACE TABLE gold.detection_by_shift AS
SELECT
    time_shift,
    COUNT(*)                        AS total_detections,
    COUNT(DISTINCT username)        AS active_users,
    ROUND(AVG(processing_time), 3)  AS avg_processing_sec
FROM silver.detections_enriched
GROUP BY time_shift
ORDER BY
    CASE time_shift
        WHEN 'MORNING'   THEN 1
        WHEN 'AFTERNOON' THEN 2
        WHEN 'EVENING'   THEN 3
        WHEN 'NIGHT'     THEN 4
    END;


-- Gold 3: Hoạt động theo Giờ (Line Chart)
CREATE OR REPLACE TABLE gold.hourly_activity AS
SELECT
    hour_of_day,
    COUNT(*)                   AS total_detections,
    COUNT(DISTINCT username)   AS active_users
FROM silver.detections_enriched
GROUP BY hour_of_day
ORDER BY hour_of_day;


-- Gold 4: Hiệu suất xử lý AI (Stacked Bar)
CREATE OR REPLACE TABLE gold.speed_analysis AS
SELECT
    speed_grade,
    ai_feature,
    COUNT(*)                        AS total_detections,
    ROUND(AVG(processing_time), 3)  AS avg_time_sec,
    ROUND(MIN(processing_time), 3)  AS fastest_sec,
    ROUND(MAX(processing_time), 3)  AS slowest_sec
FROM silver.detections_enriched
GROUP BY speed_grade, ai_feature
ORDER BY avg_time_sec;


-- Kiểm tra kết quả Gold
SELECT '--- BY FEATURE ---' AS report;

SELECT * FROM gold.detection_by_feature;


SELECT '--- BY SHIFT ---' AS report;

SELECT * FROM gold.detection_by_shift;


SELECT '--- BY HOUR ---' AS report;

SELECT * FROM gold.hourly_activity;


SELECT '--- BY SPEED ---' AS report;

SELECT * FROM gold.speed_analysis;