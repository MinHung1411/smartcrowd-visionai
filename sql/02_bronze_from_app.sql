-- ============================================
-- BƯỚC 2: BRONZE - Tạo View từ dữ liệu thật
-- Bảng detections + users đã có trong default schema
-- Bronze chỉ cần tạo VIEW tham chiếu, giữ nguyên gốc
-- ============================================

USE CATALOG visionai_catalog;

CREATE SCHEMA IF NOT EXISTS bronze;

-- Bronze View: Kết hợp detections + users (giữ nguyên dữ liệu thô)
CREATE OR REPLACE VIEW bronze.raw_detections AS
SELECT
    d.id              AS detection_id,
    d.user_id,
    u.username,
    u.email,
    d.image_path,
    d.detection_type,
    d.objects_detected AS objects_json,
    d.confidence_scores AS confidence_json,
    d.timestamp        AS capture_time,
    d.processing_time
FROM default.detections d
LEFT JOIN default.users u ON d.user_id = u.id;


-- Kiểm tra Bronze
SELECT * FROM bronze.raw_detections ORDER BY capture_time DESC;