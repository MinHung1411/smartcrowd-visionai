-- data/01_databricks_seed.sql
-- Kịch bản khởi tạo dữ liệu cho Databricks Unity Catalog
-- Chỉ chứa admin user + sample detections
-- Chạy trực tiếp trên Databricks SQL Editor

-- 1. CHUẨN BỊ MÔI TRƯỜNG (Unity Catalog)
USE CATALOG visionai_catalog;
USE SCHEMA default;

-- ========================================================
-- 2. TẠO BẢNG USERS BẰNG DELTA LAKE (chỉ admin)
-- ========================================================
CREATE TABLE IF NOT EXISTS users (
  id BIGINT NOT NULL,
  email STRING NOT NULL,
  username STRING NOT NULL,
  password_hash STRING NOT NULL,
  role STRING DEFAULT 'user',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP,
  last_login TIMESTAMP,
  birth_date DATE,
  location STRING
) USING DELTA;

-- Xóa tất cả user không phải admin
DELETE FROM users WHERE username != 'admin';

-- Thêm admin nếu chưa tồn tại
-- Password: admin123
MERGE INTO users AS target
USING (SELECT 'admin' AS username) AS source
ON target.username = source.username
WHEN NOT MATCHED THEN
  INSERT (id, email, username, password_hash, role, is_active, created_at, birth_date, location)
  VALUES (
    CAST(unix_timestamp() * 1000 AS BIGINT),
    'admin@visionai.local',
    'admin',
    concat('pbkdf2:sha256:600000', chr(36), 'I9aPwiHzacjm5I14', chr(36), '1e42df90c142e944c7da7c98891c3d2755ace99423404e91fffce8a749f20ef9'),
    'admin',
    true,
    current_timestamp() - INTERVAL 30 DAYS,
    cast('1995-06-15' as date),
    'TP. Ho Chi Minh'
  );

-- ========================================================
-- 3. TẠO BẢNG DETECTIONS BẰNG DELTA LAKE
-- ========================================================
CREATE TABLE IF NOT EXISTS detections (
  id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  image_path STRING NOT NULL,
  detection_type STRING NOT NULL,
  objects_detected STRING NOT NULL,
  confidence_scores STRING,
  timestamp TIMESTAMP,
  processing_time DOUBLE
) USING DELTA;

-- Chèn dữ liệu Lịch sử Nhận diện mẫu cho admin
INSERT INTO detections (id, user_id, image_path, detection_type, objects_detected, confidence_scores, timestamp, processing_time)
SELECT
  CAST(unix_timestamp() * 1000 + 1 AS BIGINT),
  id,
  'seed_admin_object_01.jpg',
  'upload',
  '[{"name": {"en": "person", "vi": "Người"}, "confidence": 0.92, "class": "person"}, {"name": {"en": "car", "vi": "Ô tô"}, "confidence": 0.87, "class": "car"}]',
  '[0.92, 0.87]',
  current_timestamp() - INTERVAL 28 DAYS,
  CAST(0.145 AS DOUBLE)
FROM users WHERE username = 'admin'
AND NOT EXISTS (SELECT 1 FROM detections WHERE image_path = 'seed_admin_object_01.jpg');

INSERT INTO detections (id, user_id, image_path, detection_type, objects_detected, confidence_scores, timestamp, processing_time)
SELECT
  CAST(unix_timestamp() * 1000 + 2 AS BIGINT),
  id,
  'seed_admin_camera_01.jpg',
  'camera',
  '[{"en": "laptop", "vi": "Máy tính xách tay"}, {"en": "cell phone", "vi": "Điện thoại"}]',
  '[0.94, 0.88]',
  current_timestamp() - INTERVAL 25 DAYS,
  CAST(0.098 AS DOUBLE)
FROM users WHERE username = 'admin'
AND NOT EXISTS (SELECT 1 FROM detections WHERE image_path = 'seed_admin_camera_01.jpg');

INSERT INTO detections (id, user_id, image_path, detection_type, objects_detected, confidence_scores, timestamp, processing_time)
SELECT
  CAST(unix_timestamp() * 1000 + 3 AS BIGINT),
  id,
  'seed_admin_face_01.jpg',
  'face_upload',
  '[{"box": [150, 80, 200, 220], "confidence": 0.95, "name": "Admin"}]',
  '[0.95]',
  current_timestamp() - INTERVAL 22 DAYS,
  CAST(0.067 AS DOUBLE)
FROM users WHERE username = 'admin'
AND NOT EXISTS (SELECT 1 FROM detections WHERE image_path = 'seed_admin_face_01.jpg');

INSERT INTO detections (id, user_id, image_path, detection_type, objects_detected, confidence_scores, timestamp, processing_time)
SELECT
  CAST(unix_timestamp() * 1000 + 4 AS BIGINT),
  id,
  'seed_admin_color_01.jpg',
  'color',
  '[{"rgb": [41, 128, 185], "hex": "#2980b9", "name": "Blue", "percentage": 35.42}, {"rgb": [236, 240, 241], "hex": "#ecf0f1", "name": "White", "percentage": 28.15}]',
  '[35.42, 28.15]',
  current_timestamp() - INTERVAL 18 DAYS,
  CAST(0.034 AS DOUBLE)
FROM users WHERE username = 'admin'
AND NOT EXISTS (SELECT 1 FROM detections WHERE image_path = 'seed_admin_color_01.jpg');

INSERT INTO detections (id, user_id, image_path, detection_type, objects_detected, confidence_scores, timestamp, processing_time)
SELECT
  CAST(unix_timestamp() * 1000 + 5 AS BIGINT),
  id,
  'seed_admin_class_01.jpg',
  'classification',
  '[{"name": "dog", "confidence": 0.91, "box": [50, 100, 400, 350]}, {"name": "person", "confidence": 0.82, "box": [420, 60, 600, 440]}]',
  '[0.91, 0.82]',
  current_timestamp() - INTERVAL 12 DAYS,
  CAST(0.078 AS DOUBLE)
FROM users WHERE username = 'admin'
AND NOT EXISTS (SELECT 1 FROM detections WHERE image_path = 'seed_admin_class_01.jpg');

-- ========================================================
-- 4. KIỂM TRA DỮ LIỆU
-- ========================================================
SELECT 'USERS' as table_name, COUNT(*) as row_count FROM users
UNION ALL
SELECT 'DETECTIONS', COUNT(*) FROM detections;

SELECT
  u.username,
  d.detection_type,
  d.objects_detected,
  d.timestamp
FROM users u
LEFT JOIN detections d ON u.id = d.user_id
ORDER BY d.timestamp DESC;
