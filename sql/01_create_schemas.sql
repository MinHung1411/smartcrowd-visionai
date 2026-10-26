-- ============================================
-- NGÀY 3: MEDALLION ARCHITECTURE - DỮ LIỆU THẬT
-- Sử dụng bảng detections đã có trên Databricks
-- làm Bronze, rồi xây Silver + Gold lên trên
-- ============================================

USE default;

-- Tạo 3 Schema cho kiến trúc Medallion
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
