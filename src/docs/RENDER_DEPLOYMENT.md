# Hướng dẫn triển khai VisionAI lên Render (Gói dịch vụ Cloud)

Tài liệu này hướng dẫn chi tiết cách đóng gói và triển khai Flask Web App của ứng dụng **VisionAI** lên nền tảng **Render** sử dụng công nghệ Docker. 

> [!NOTE]
> Do ứng dụng sử dụng các thư viện nặng về xử lý ảnh và AI như **OpenCV (cv2)** và **YOLOv8**, việc triển khai trực tiếp bằng Python buildpack thông thường trên Render sẽ bị thiếu các thư viện hệ thống (ví dụ: `libGL.so.1`) dẫn đến crash server.
> Do đó, **Docker** là phương pháp tối ưu và an toàn nhất để triển khai ứng dụng này lên Render.

---

## 📋 Mục lục
1. [Chuẩn bị trước khi triển khai](#1-chuẩn-bị-trước-khi-triển-khai)
2. [Cấu hình biến môi trường trên Render](#2-cấu-hình-biến-môi-trường-trên-render)
3. [Các bước tạo Web Service trên Render](#3-các-bước-tạo-web-service-trên-render)
4. [Cấu hình Lưu trữ Vĩnh viễn (Persistent Disk) - Quan trọng](#4-cấu-hình-lưu-trữ-vĩnh-viễn-persistent-disk---quan-trọng)
5. [Giám sát và kiểm tra sức khỏe](#5-giám-sát-và-kiểm-tra-sức-khỏe)

---

## 1. Chuẩn bị trước khi triển khai

### Đẩy mã nguồn lên GitHub/GitLab:
1. Đảm bảo mã nguồn chính của bạn trong thư mục `visionai_app` (bao gồm file [Dockerfile](file:///c:/Users/ADMIN/OneDrive/TaiLieu/CLOUD/exam/visionai_app/Dockerfile) vừa được tạo ở thư mục gốc) đã được đẩy (push) lên một kho chứa (repository) trên GitHub hoặc GitLab của bạn.
2. Kiểm tra xem file `requirements.txt` có dòng `gunicorn==21.2.0` hay chưa (Gunicorn là Web Server chuẩn cho môi trường Production).

---

## 2. Cấu hình biến môi trường trên Render

Khi tạo dịch vụ trên Render, bạn cần cấu hình các biến môi trường (Environment Variables) sau:

| Tên biến | Kiểu giá trị | Mô tả |
| :--- | :--- | :--- |
| `DATABASE_URL` | String | Đường dẫn kết nối Databricks Catalog (lấy từ file `.env` cục bộ của bạn, ví dụ: `databricks://token:...`). |
| `SECRET_KEY` | String | Một chuỗi ký tự ngẫu nhiên dùng để mã hóa session người dùng (Ví dụ: `supersecretkey123`). |
| `FLASK_APP` | String | Để mặc định là `run.py`. |
| `FLASK_ENV` | String | Để mặc định là `production`. |
| `PYTHONPATH` | String | Để mặc định là `/app`. |

---

## 3. Các bước tạo Web Service trên Render

1. Truy cập vào trang quản lý [Dashboard của Render](https://dashboard.render.com/) và đăng nhập.
2. Bấm vào nút **New +** ở góc trên bên phải và chọn **Web Service**.
3. Kết nối với tài khoản GitHub/GitLab của bạn và chọn kho chứa (repository) của dự án `visionai_app`.
4. Cấu hình thông tin dịch vụ:
   - **Name**: Nhập tên dịch vụ (ví dụ: `visionai-app`).
   - **Region**: Chọn khu vực gần nhất (ví dụ: `Singapore` hoặc `Oregon`).
   - **Branch**: Chọn nhánh deploy (ví dụ: `main`).
   - **Root Directory**: Để trống (nếu repository của bạn chứa trực tiếp code `visionai_app`). Nếu bạn push cả thư mục cha `exam/`, hãy điền `visionai_app` vào đây.
   - **Runtime**: Chọn **Docker** (Render sẽ tự động tìm thấy và build theo file [Dockerfile](file:///c:/Users/ADMIN/OneDrive/TaiLieu/CLOUD/exam/visionai_app/Dockerfile) ở thư mục gốc).
5. Cuộn xuống và chọn gói tài nguyên (Instance Type):
   - Chọn gói **Free** hoặc nâng cấp lên gói **Starter** (gói Starter có 512MB-1GB RAM giúp build và load model YOLO nhanh hơn).
6. Bấm vào nút **Advanced** để thêm biến môi trường:
   - Thêm các biến môi trường đã liệt kê ở [Mục 2](#2-cấu-hình-biến-môi-trường-trên-render).
7. Bấm nút **Create Web Service** để Render bắt đầu build Docker Image và chạy ứng dụng.

---

## 4. Cấu hình Lưu trữ Vĩnh viễn (Persistent Disk) - Quan trọng

Mặc định, bộ lưu trữ container của Render là tạm thời (ephemeral). Khi ứng dụng restart hoặc deploy phiên bản mới, tất cả ảnh nhận diện được lưu trong thư mục `uploads/` và file dữ liệu nhận diện khuôn mặt `known_faces.pkl` sẽ bị xóa sạch.

Để giữ lại hình ảnh và khuôn mặt đã đăng ký:
1. Trong màn hình quản lý dịch vụ trên Render, truy cập vào tab **Disk** ở menu bên trái.
2. Bấm **Add Disk**:
   - **Name**: Điền `uploads-disk`.
   - **Mount Path**: Điền `/app/uploads` (đây là thư mục lưu trữ ảnh và model nhận diện khuôn mặt).
   - **Size**: Điền `1 GiB` (mức tối thiểu là đủ dùng, chi phí rất rẻ khoảng $1/tháng).
3. Bấm **Save**. Dịch vụ sẽ tự động khởi động lại và gắn đĩa cứng này vào thư mục lưu trữ.

---

## 5. Giám sát và kiểm tra sức khỏe

- **Log Deploy**: Bạn có thể theo dõi tiến trình tải thư viện và build container ở tab **Events** hoặc **Logs**.
- **Địa chỉ truy cập**: Render sẽ cấp cho bạn một địa chỉ URL miễn phí dạng `https://visionai-app.onrender.com`.
- **Health Check URL**: Bạn có thể kiểm tra xem server hoạt động bình thường không bằng cách truy cập `https://visionai-app.onrender.com/`.

---

**Chúc mừng! Ứng dụng VisionAI Object Detection của bạn đã sẵn sàng hoạt động trên môi trường đám mây Render!**
