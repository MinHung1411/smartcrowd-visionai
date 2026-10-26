import os
import cv2
import numpy as np
import time
from collections import defaultdict, deque
from ultralytics import YOLO

class CrowdTrackerService:
    """
    Dịch vụ phát hiện, theo dõi (tracking) và đếm người 2 chiều (IN/OUT)
    Sử dụng mô hình YOLOv11m fine-tuned trên CrowdHuman kết hợp ByteTrack.
    """
    def __init__(self, model_path=None):
        if model_path is None:
            # Ưu tiên best.pt trong src/ hoặc biến môi trường
            src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            default_path = os.path.join(src_dir, 'best.pt')
            model_path = os.environ.get('YOLO_MODEL_PATH') or default_path
            if not os.path.exists(model_path):
                # Fallback nếu tìm ở root
                model_path = 'best.pt'
                
        self.model_path = model_path
        self.model = None
        
        # Cấu hình đếm & tracking
        self.conf_threshold = 0.35
        self.iou_threshold = 0.5
        self.line_ratio = 0.5  # Vị trí vạch đếm (50% chiều cao khung hình)
        self.alert_threshold = 20  # Ngưỡng cảnh báo quá tải
        
        # Trạng thái đếm tích lũy
        self.total_in = 0
        self.total_out = 0
        self.counted_in_ids = set()
        self.counted_out_ids = set()
        self.peak_count = 0
        
        # Lịch sử quỹ đạo di chuyển: track_id -> deque[(x, y), maxlen=30]
        self.track_history = defaultdict(lambda: deque(maxlen=30))
        
        # Tích lũy vị trí để vẽ Heatmap
        self.heatmap_points = []
        self.max_heatmap_points = 5000
        
    def get_model(self):
        """Khởi tạo model (lazy load)"""
        if self.model is None:
            print(f"[AI] Loading YOLOv11 CrowdHuman model from: {self.model_path}")
            self.model = YOLO(self.model_path)
            print(f"[AI] Model ready! Classes: {self.model.names}")
        return self.model

    def update_config(self, conf=None, line_ratio=None, alert_threshold=None):
        """Cập nhật các tham số cấu hình linh hoạt từ giao diện"""
        if conf is not None:
            self.conf_threshold = float(conf)
        if line_ratio is not None:
            self.line_ratio = float(line_ratio)
        if alert_threshold is not None:
            self.alert_threshold = int(alert_threshold)

    def reset_counter(self):
        """Đặt lại bộ đếm IN/OUT và lịch sử track"""
        self.total_in = 0
        self.total_out = 0
        self.counted_in_ids.clear()
        self.counted_out_ids.clear()
        self.track_history.clear()
        self.heatmap_points.clear()
        self.peak_count = 0
        return {
            'success': True,
            'message': 'Bộ đếm đã được đặt lại thành công',
            'total_in': 0,
            'total_out': 0,
            'occupancy': 0
        }

    def process_frame(self, frame, custom_conf=None, custom_line_ratio=None):
        """
        Xử lý 1 frame ảnh/camera:
        1. Chạy YOLOv11m + ByteTrack
        2. Xác định cắt qua vạch kẻ (Line Crossing IN/OUT)
        3. Tính toán mật độ và trạng thái quá tải
        4. Vẽ Bounding Box, quỹ đạo, vạch đếm và HUD banner
        """
        start_time = time.time()
        model = self.get_model()
        h, w = frame.shape[:2]
        
        conf = custom_conf if custom_conf is not None else self.conf_threshold
        line_ratio = custom_line_ratio if custom_line_ratio is not None else self.line_ratio
        line_y = int(h * line_ratio)
        
        # Chạy tracking ByteTrack
        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=conf,
            iou=self.iou_threshold,
            verbose=False
        )[0]
        
        annotated_frame = frame.copy()
        current_detected_people = []
        current_frame_ids = []
        
        # Vẽ vạch kẻ ảo IN / OUT (Neon Cyan / Yellow line)
        cv2.line(annotated_frame, (0, line_y), (w, line_y), (255, 200, 0), 2)
        cv2.putText(annotated_frame, "COUNTING LINE (A -> B: IN | B -> A: OUT)", (15, line_y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 200, 0), 1, cv2.LINE_AA)
        
        # Mũi tên chỉ hướng IN/OUT bên cạnh vạch
        cv2.arrowedLine(annotated_frame, (w - 40, line_y - 30), (w - 40, line_y + 30), (0, 255, 0), 2, tipLength=0.4)
        cv2.putText(annotated_frame, "IN", (w - 30, line_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        
        cv2.arrowedLine(annotated_frame, (w - 70, line_y + 30), (w - 70, line_y - 30), (0, 165, 255), 2, tipLength=0.4)
        cv2.putText(annotated_frame, "OUT", (w - 100, line_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
        
        if results.boxes is not None and len(results.boxes) > 0:
            boxes = results.boxes.xyxy.cpu().numpy()
            confidences = results.boxes.conf.cpu().numpy()
            track_ids = results.boxes.id.cpu().numpy().astype(int) if results.boxes.id is not None else []
            
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                c = float(confidences[i])
                tid = int(track_ids[i]) if len(track_ids) > i else None
                
                # Điểm chân / tâm đáy của người
                cx = int((x1 + x2) / 2)
                cy = int(y2)
                
                # Lưu điểm tích lũy vẽ Heatmap
                if len(self.heatmap_points) < self.max_heatmap_points:
                    self.heatmap_points.append((cx, cy))
                    
                current_detected_people.append({
                    'id': tid,
                    'confidence': round(c, 3),
                    'box': [x1, y1, x2, y2],
                    'centroid': [cx, cy]
                })
                
                # Xử lý Logic Kẻ vạch 2 chiều (Line Crossing)
                if tid is not None:
                    current_frame_ids.append(tid)
                    prev_points = self.track_history[tid]
                    
                    if len(prev_points) > 0:
                        prev_cx, prev_cy = prev_points[-1]
                        
                        # 1. Hướng ĐI VÀO (Di chuyển từ trên xuống dưới qua vạch)
                        if prev_cy < line_y <= cy:
                            if tid not in self.counted_in_ids:
                                self.total_in += 1
                                self.counted_in_ids.add(tid)
                                # Hiệu ứng nháy xanh khi vừa vượt vạch IN
                                cv2.circle(annotated_frame, (cx, line_y), 15, (0, 255, 0), -1)
                        
                        # 2. Hướng ĐI RA (Di chuyển từ dưới lên trên qua vạch)
                        elif prev_cy > line_y >= cy:
                            if tid not in self.counted_out_ids:
                                self.total_out += 1
                                self.counted_out_ids.add(tid)
                                # Hiệu ứng nháy cam khi vừa vượt vạch OUT
                                cv2.circle(annotated_frame, (cx, line_y), 15, (0, 165, 255), -1)
                    
                    self.track_history[tid].append((cx, cy))
                    
                    # Vẽ vệt đuôi quỹ đạo di chuyển (Trajectory Trail)
                    points = list(self.track_history[tid])
                    for p in range(1, len(points)):
                        thickness = int(np.sqrt(16 / float(p + 1)) * 1.5)
                        cv2.line(annotated_frame, points[p - 1], points[p], (0, 255, 255), thickness)
                
                # Vẽ Bounding Box người
                box_color = (0, 255, 128)  # Xanh ngọc
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, 2)
                
                # Nhãn người + ID
                label = f"ID:{tid} ({c:.0%})" if tid is not None else f"Person {c:.0%}"
                (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated_frame, (x1, y1 - 22), (x1 + lw + 8, y1), box_color, -1)
                cv2.putText(annotated_frame, label, (x1 + 4, y1 - 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        
        current_count = len(current_detected_people)
        self.peak_count = max(self.peak_count, current_count)
        occupancy = max(0, self.total_in - self.total_out)
        
        # Đánh giá mức độ mật độ (Crowd Density Level)
        is_alert = current_count >= self.alert_threshold
        if current_count < 5:
            density_level = "LOW"
            density_color = (0, 255, 0)      # Xanh lá
        elif current_count <= 15:
            density_level = "MODERATE"
            density_color = (0, 255, 255)    # Vàng
        elif current_count <= 25:
            density_level = "HIGH"
            density_color = (0, 165, 255)    # Cam
        else:
            density_level = "CRITICAL"
            density_color = (0, 0, 255)      # Đỏ
            
        # Vẽ HUD BANNER trên đầu khung hình (Hi-tech CCTV Style)
        hud_h = 42
        hud_overlay = annotated_frame.copy()
        cv2.rectangle(hud_overlay, (0, 0), (w, hud_h), (20, 20, 25), -1)
        cv2.addWeighted(hud_overlay, 0.75, annotated_frame, 0.25, 0, annotated_frame)
        
        # Các chỉ số trên HUD
        hud_text = f"CURRENT: {current_count:02d} | IN: {self.total_in:03d} | OUT: {self.total_out:03d} | OCCUPANCY: {occupancy:03d}"
        cv2.putText(annotated_frame, hud_text, (15, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
        
        # Trạng thái an ninh bên phải HUD
        status_text = f"DENSITY: {density_level}" if not is_alert else f"ALERT: OVERCROWDED ({current_count})!"
        status_color = (0, 0, 255) if is_alert else density_color
        cv2.putText(annotated_frame, status_text, (w - 280, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2, cv2.LINE_AA)
        
        # Nếu đang Overcrowded, nháy viền đỏ cảnh báo
        if is_alert:
            cv2.rectangle(annotated_frame, (0, 0), (w - 1, h - 1), (0, 0, 255), 4)
            
        processing_time = round(time.time() - start_time, 3)
        
        return {
            'annotated_frame': annotated_frame,
            'current_count': current_count,
            'total_in': self.total_in,
            'total_out': self.total_out,
            'occupancy': occupancy,
            'peak_count': self.peak_count,
            'density_level': density_level,
            'is_alert': is_alert,
            'alert_threshold': self.alert_threshold,
            'processing_time': processing_time,
            'detected_people': current_detected_people
        }

    def generate_heatmap(self, base_image):
        """
        Tạo bản đồ nhiệt (Crowd Heatmap) dựa trên các tọa độ người tích lũy
        """
        h, w = base_image.shape[:2]
        heatmap_mask = np.zeros((h, w), dtype=np.float32)
        
        if not self.heatmap_points:
            return base_image
            
        # Vẽ các điểm tích lũy
        radius = int(max(h, w) * 0.05)
        for (cx, cy) in self.heatmap_points:
            if 0 <= cx < w and 0 <= cy < h:
                cv2.circle(heatmap_mask, (cx, cy), radius, 1.0, -1)
                
        # Làm mượt (Gaussian Blur)
        ksize = int(radius * 2) | 1
        heatmap_mask = cv2.GaussianBlur(heatmap_mask, (ksize, ksize), 0)
        
        # Chuẩn hóa về 0-255
        if np.max(heatmap_mask) > 0:
            heatmap_norm = np.uint8(255 * (heatmap_mask / np.max(heatmap_mask)))
        else:
            heatmap_norm = np.zeros((h, w), dtype=np.uint8)
            
        # Áp dụng bảng màu nhiệt JET
        color_heatmap = cv2.applyColorMap(heatmap_norm, cv2.COLORMAP_JET)
        
        # Phủ lên ảnh gốc
        output = cv2.addWeighted(base_image, 0.6, color_heatmap, 0.4, 0)
        
        # Tiêu đề Heatmap
        cv2.putText(output, "CROWD TRAFFIC HEATMAP ACCUMULATION", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(output, f"Total Data Points Tracked: {len(self.heatmap_points)}", (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
        
        return output

# Khởi tạo singleton service
crowd_tracker = CrowdTrackerService()
