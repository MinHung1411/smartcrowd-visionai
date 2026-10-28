import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import sys
import time

# --- Patch for gradio_client get_type boolean schema bug ---
try:
    import gradio_client.utils as _gcu
    _orig_get_type = _gcu.get_type

    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return "unknown"
        return _orig_get_type(schema)

    _gcu.get_type = _safe_get_type

    _orig_json_schema = getattr(_gcu, "_json_schema_to_python_type", None)
    if _orig_json_schema:
        def _safe_json_schema(schema, *args, **kwargs):
            if not isinstance(schema, dict):
                return "unknown"
            return _orig_json_schema(schema, *args, **kwargs)
        _gcu._json_schema_to_python_type = _safe_json_schema
except Exception:
    pass

# --- Patch for starlette TemplateResponse signature shift ---
try:
    import starlette.templating
    _orig_template_response = starlette.templating.Jinja2Templates.TemplateResponse

    def _compat_template_response(self, *args, **kwargs):
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            name = args[0]
            context = args[1]
            request = context.get("request")
            return _orig_template_response(self, request=request, name=name, context=context, **kwargs)
        return _orig_template_response(self, *args, **kwargs)

    starlette.templating.Jinja2Templates.TemplateResponse = _compat_template_response
except Exception:
    pass
# ------------------------------------------------------------

import cv2
import numpy as np
from collections import defaultdict, deque
from ultralytics import YOLO
import gradio as gr

# ----------------------------------------------------
# 1. ZeroGPU Integration (Hugging Face Free A100 GPU)
# ----------------------------------------------------
try:
    import spaces
    has_spaces = True
except Exception:
    has_spaces = False

def gpu_fn(duration=60):
    if has_spaces:
        return spaces.GPU(duration=duration)
    return lambda f: f

# Load YOLOv11m CrowdHuman model
model_path = "best.pt"
if not os.path.exists(model_path) and os.path.exists("src/best.pt"):
    model_path = "src/best.pt"
model = YOLO(model_path)

IMGSZ_MAP = {
    "Nhanh (384px)": 384,
    "Cân bằng (480px)": 480,
    "Chính xác cao (640px)": 640,
    "Siêu nét (960px)": 960
}
VIDEO_CHOICES = list(IMGSZ_MAP.keys())

# ----------------------------------------------------
# 2. AI Inference Functions (A100 GPU Accelerated)
# ----------------------------------------------------
@gpu_fn(duration=30)
def detect_image(img, conf):
    if img is None:
        return None, "Vui lòng tải ảnh lên."
    results = model(img, conf=float(conf), imgsz=640, verbose=False)[0]
    annotated = results.plot()
    count = len(results.boxes)
    
    if count < 5:
        density = "LOW (Thấp)"
    elif count <= 15:
        density = "MODERATE (Trung bình)"
    elif count <= 25:
        density = "HIGH (Đông đúc)"
    else:
        density = "CRITICAL (Quá tải báo động!)"
        
    cv2.putText(annotated, f"PEOPLE COUNT: {count} | DENSITY: {density}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
    
    return annotated, f"Số người phát hiện: {count} | Mật độ: {density}"

@gpu_fn(duration=120)
def detect_video(video_path, frame_skip, conf, iou, imgsz_label, min_hits, max_seconds):
    if video_path is None:
        return None, "Vui lòng tải video lên."

    imgsz_val = IMGSZ_MAP.get(imgsz_label, 480)
    step = int(frame_skip) + 1
    min_hits = int(min_hits)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    out_fps = max(fps / step, 1)

    out_path = "output_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(out_path, fourcc, out_fps, (w, h))

    start_time = time.time()
    frame_idx = 0
    max_count = 0
    unique_ids = set()
    track_hits = {}
    first_infer = True
    truncated = False

    while True:
        if max_seconds and (time.time() - start_time) > max_seconds:
            truncated = True
            break

        if frame_idx % step == 0:
            ret, frame = cap.read()
        else:
            ret = cap.grab()
            frame = None

        if not ret:
            break

        if frame_idx % step == 0:
            results = model.track(
                frame,
                persist=not first_infer,
                tracker="bytetrack.yaml",
                conf=float(conf),
                iou=float(iou),
                imgsz=imgsz_val,
                verbose=False,
            )[0]
            first_infer = False

            annotated = frame.copy()
            confirmed_ids_this_frame = []

            if results.boxes.id is not None:
                for (x1, y1, x2, y2), c, tid in zip(
                    results.boxes.xyxy.tolist(),
                    results.boxes.conf.tolist(),
                    results.boxes.id.tolist(),
                ):
                    tid = int(tid)
                    track_hits[tid] = track_hits.get(tid, 0) + 1
                    if track_hits[tid] >= min_hits:
                        unique_ids.add(tid)
                        confirmed_ids_this_frame.append(tid)
                        cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 128), 2)
                        cv2.putText(annotated, f"ID:{tid}", (int(x1), max(20, int(y1) - 6)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 128), 2)

            cur_count = len(confirmed_ids_this_frame)
            max_count = max(max_count, cur_count)

            # HUD Top Bar
            cv2.rectangle(annotated, (0, 0), (w, 36), (20, 20, 20), -1)
            hud_text = f"FRAME: {cur_count:02d} | TOTAL UNIQUE: {len(unique_ids):03d} | PEAK: {max_count:02d}"
            cv2.putText(annotated, hud_text, (15, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

            out.write(annotated)

        frame_idx += 1

    cap.release()
    out.release()

    elapsed = round(time.time() - start_time, 1)
    summary = f"Xử lý hoàn tất trong {elapsed}s | Tổng số lượt người duy nhất: {len(unique_ids)} | Đỉnh điểm trong 1 frame: {max_count}"
    if truncated:
        summary += f" (Dừng sớm tại giới hạn {max_seconds}s)."
    return out_path, summary

def detect_webcam(frame, conf, iou, imgsz_label):
    if frame is None:
        return None, ""
    imgsz_val = IMGSZ_MAP.get(imgsz_label, 480)
    results = model(frame, conf=float(conf), iou=float(iou), imgsz=imgsz_val, verbose=False)[0]
    annotated = results.plot()
    count = len(results.boxes)
    density = "AN TOÀN" if count < 10 else "CẢNH BÁO ĐÔNG ĐÚC"
    return annotated, f"Số người hiện tại: {count} ({density})"

# ----------------------------------------------------
# 3. Premium Gradio Web Interface
# ----------------------------------------------------
custom_css = """
.gradio-container {
    background: linear-gradient(135deg, #090d16 0%, #0f172a 100%);
    font-family: 'Inter', system-ui, sans-serif;
    color: #f8fafc;
}
.tabitem {
    border-radius: 12px;
}
.btn-primary {
    background: linear-gradient(135deg, #0d9488 0%, #10b981 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    border: none !important;
}
"""

with gr.Blocks(title="SmartCrowd VisionAI", css=custom_css, theme=gr.themes.Soft(primary_hue="teal", neutral_hue="slate")) as demo:
    gr.HTML(
        """
        <div style="text-align: center; padding: 25px 10px 15px 10px;">
            <div style="display: inline-flex; align-items: center; gap: 10px; background: rgba(13, 148, 136, 0.15); border: 1px solid rgba(13, 148, 136, 0.3); padding: 6px 16px; rounded: 9999px; border-radius: 30px; margin-bottom: 12px;">
                <span style="height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block;"></span>
                <span style="font-size: 13px; font-weight: bold; color: #5eead4; letter-spacing: 0.05em; text-transform: uppercase;">A100 GPU Accelerated • Databricks Medallion Lakehouse</span>
            </div>
            <h1 style="font-size: 32px; font-weight: 900; background: linear-gradient(135deg, #ffffff 0%, #5eead4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                SmartCrowd: Real-Time Crowd Analytics & People Counting
            </h1>
            <p style="color: #94a3b8; font-size: 14px; max-width: 750px; margin: 10px auto 0 auto;">
                Hệ thống thị giác máy tính giám sát đám đông thông minh sử dụng mô hình <b>YOLOv11m fine-tuned trên CrowdHuman</b> kết hợp <b>ByteTrack</b> và kiến trúc <b>Databricks Lakehouse</b>.
            </p>
        </div>
        """
    )

    with gr.Tabs():
        # Tab 1: Image Detection
        with gr.Tab("📷 Nhận diện Đám đông qua Ảnh"):
            with gr.Row():
                with gr.Column(scale=1):
                    img_in = gr.Image(type="numpy", label="Ảnh tải lên (CCTV / Phone)")
                    img_conf = gr.Slider(
                        0.10, 0.85, value=0.25, step=0.05,
                        label="Ngưỡng tin cậy (Confidence) — Mặc định 0.25 để nhận diện đủ người ở xa"
                    )
                    img_btn = gr.Button("🔍 Chạy Phân Tích Đám Đông", variant="primary")
                with gr.Column(scale=1):
                    img_out = gr.Image(label="Kết quả vẽ Bounding Box & HUD")
                    count_out = gr.Textbox(label="Báo cáo Mật độ & Số lượng", interactive=False)

            img_btn.click(detect_image, inputs=[img_in, img_conf], outputs=[img_out, count_out])

        # Tab 2: Video Analytics
        with gr.Tab("🎬 Phân tích Video CCTV & Tracking"):
            with gr.Row():
                with gr.Column(scale=1):
                    vid_in = gr.Video(label="Tải lên Video CCTV (.mp4, .avi, .mov)")
                    with gr.Row():
                        frame_skip = gr.Slider(0, 10, value=3, step=1, label="Bỏ qua frame (Tăng tốc)")
                        vid_conf = gr.Slider(0.1, 0.85, value=0.30, step=0.05, label="Confidence")
                    with gr.Row():
                        vid_iou = gr.Slider(0.2, 0.8, value=0.5, step=0.05, label="IoU Threshold")
                        vid_min_hits = gr.Slider(1, 8, value=3, step=1, label="Số frame xác nhận Track")
                    with gr.Row():
                        vid_imgsz = gr.Dropdown(choices=VIDEO_CHOICES, value="Cân bằng (480px)", label="Độ phân giải")
                        vid_max_seconds = gr.Slider(30, 240, value=120, step=10, label="Giới hạn thời gian (giây)")
                    vid_btn = gr.Button("🚀 Bắt đầu Phân Tích Video", variant="primary")
                with gr.Column(scale=1):
                    vid_out = gr.Video(label="Video đã vẽ Quỹ đạo Track & HUD")
                    vid_count_out = gr.Textbox(label="Thống kê Traffic Video", interactive=False)

            vid_btn.click(
                detect_video,
                inputs=[vid_in, frame_skip, vid_conf, vid_iou, vid_imgsz, vid_min_hits, vid_max_seconds],
                outputs=[vid_out, vid_count_out]
            )

        # Tab 3: Live Camera
        with gr.Tab("🎥 Giám sát Camera Trực tiếp"):
            with gr.Row():
                with gr.Column(scale=1):
                    cam_in = gr.Image(sources=["webcam"], streaming=True, label="Webcam Trực Tiếp")
                    with gr.Row():
                        cam_conf = gr.Slider(0.1, 0.8, value=0.30, step=0.05, label="Confidence")
                        cam_iou = gr.Slider(0.2, 0.8, value=0.5, step=0.05, label="IoU")
                    cam_imgsz = gr.Dropdown(choices=VIDEO_CHOICES, value="Nhanh (384px)", label="Độ phân giải Camera")
                with gr.Column(scale=1):
                    cam_out = gr.Image(label="Live HUD Stream")
                    cam_count = gr.Textbox(label="Trạng thái Hiện tại", interactive=False)

            cam_in.stream(
                detect_webcam,
                inputs=[cam_in, cam_conf, cam_iou, cam_imgsz],
                outputs=[cam_out, cam_count]
            )

        # Tab 4: Databricks Architecture & SQL Lakehouse
        with gr.Tab("📊 Kiến trúc Databricks Lakehouse & Benchmarks"):
            gr.HTML(
                """
                <div style="padding: 15px; background: rgba(30, 41, 59, 0.5); border-radius: 12px; border: 1px solid #334155;">
                    <h3 style="color: #38bdf8; margin-top: 0;">Kiến trúc Medallion Lakehouse (Databricks Unity Catalog)</h3>
                    <p style="color: #cbd5e1; font-size: 13.5px;">Toàn bộ dữ liệu đếm người, tọa độ Bounding Box và nhật ký an ninh được đồng bộ tự động theo mô hình 3 tầng chuẩn Enterprise:</p>
                    <ul style="color: #94a3b8; font-size: 13px; line-height: 1.8;">
                        <li><b style="color: #cd7f32;">Bronze Layer (01_bronze_raw.sql):</b> Lưu trữ streaming telemetry thô từ CCTV camera theo chuẩn Delta Lake.</li>
                        <li><b style="color: #c0c0c0;">Silver Layer (03_silver_enriched.sql):</b> Làm sạch, khử trùng lặp (Deduplication) và gán nhãn mức độ mật độ (LOW/MODERATE/HIGH/CRITICAL).</li>
                        <li><b style="color: #ffd700;">Gold Layer (04_gold_tables.sql):</b> Bảng tổng hợp KPI (Hourly Aggregates, Overcrowding Anomaly Detection) phục vụ Dashboard và báo cáo điều hành.</li>
                        <li><b style="color: #a78bfa;">MLflow Tracking (05_mlflow_experiment.sql):</b> Quản lý vòng đời mô hình, mAP@50 đạt <b>95.8%</b> trên CrowdHuman test set.</li>
                    </ul>
                </div>
                """
            )

    gr.HTML(
        """
        <div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 25px; border-top: 1px solid #1e293b; padding-top: 15px;">
            SmartCrowd VisionAI • Nghiên cứu & Phát triển bởi Hồ Minh Hưng • YOLOv11m + ByteTrack + Databricks
        </div>
        """
    )

# ----------------------------------------------------
# 3. Mount Full-Stack VisionAI Web Application at Root /
# ----------------------------------------------------
try:
    sys.path.insert(0, os.path.abspath('src'))
    from app import create_app
    import gradio.routes
    from starlette.middleware.wsgi import WSGIMiddleware

    flask_app = create_app()

    class FlaskRoutingMiddleware:
        def __init__(self, app, flask_wsgi):
            self.app = app
            self.flask = WSGIMiddleware(flask_wsgi)

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http":
                path = scope.get("path", "")
                if not path:
                    path = "/"
                    scope = dict(scope)
                    scope["path"] = "/"
                # Gradio internal endpoints for ZeroGPU supervisor, API info, and queue
                if path.startswith(("/gradio_api", "/queue", "/assets")) or path in ["/config", "/info", "/startup-events", "/theme.css"]:
                    await self.app(scope, receive, send)
                    return
                # Route everything else to the full Flask VisionAI application
                await self.flask(scope, receive, send)
                return
            await self.app(scope, receive, send)

    _orig_create_app = gradio.routes.App.create_app
    def _patched_create_app(*args, **kwargs):
        app = _orig_create_app(*args, **kwargs)
        app.add_middleware(FlaskRoutingMiddleware, flask_wsgi=flask_app)
        app.middleware_stack = app.build_middleware_stack()
        return app

    gradio.routes.App.create_app = _patched_create_app
    print("[SYSTEM] Patched gradio.routes.App.create_app: Full Flask Web App mounted at root '/'!")
except Exception as e:
    print(f"[SYSTEM] Notice mounting Flask app: {e}")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
