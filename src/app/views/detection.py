from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.detection import Detection, db
from app.services.db_service import save_detection, save_annotated_image
from app.services.crowd_service import crowd_tracker
import cv2
import os
import time
import base64
import numpy as np
import uuid

detection_bp = Blueprint('detection', __name__)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@detection_bp.route('/camera')
@login_required
def camera():
    """Trang giám sát Camera Real-time: Đếm người & Kẻ vạch 2 chiều IN/OUT"""
    return render_template('detection/camera.html',
                           alert_threshold=crowd_tracker.alert_threshold,
                           line_ratio=crowd_tracker.line_ratio)

@detection_bp.route('/upload')
@login_required
def upload():
    """Trang tải ảnh hoặc video để phân tích đám đông"""
    return render_template('detection/upload.html')

@detection_bp.route('/track_frame', methods=['POST'])
@detection_bp.route('/detect_camera', methods=['POST'])
@login_required
def track_frame():
    """
    API xử lý từng frame từ Webcam/CCTV stream:
    - Nhận diện người qua YOLOv11m CrowdHuman
    - Tracking gán ID đa đối tượng bằng ByteTrack
    - Đếm người cắt qua vạch 2 chiều (IN / OUT)
    - Trả về frame đã vẽ Bounding Box, Quỹ đạo, Vạch đếm và HUD
    """
    data = request.get_json() or {}
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Nhận các tham số cấu hình động từ client (nếu có)
        conf = float(data.get('conf', crowd_tracker.conf_threshold))
        line_ratio = float(data.get('line_ratio', crowd_tracker.line_ratio))
        alert_threshold = int(data.get('alert_threshold', crowd_tracker.alert_threshold))
        crowd_tracker.update_config(conf=conf, line_ratio=line_ratio, alert_threshold=alert_threshold)
        
        # Giải mã ảnh base64
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Xử lý frame qua Crowd Tracker Service
        results = crowd_tracker.process_frame(
            frame,
            custom_conf=conf,
            custom_line_ratio=line_ratio
        )
        
        annotated_frame = results['annotated_frame']
        
        # Chuyển frame kết quả sang Base64 gửi về frontend
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Lưu vào Database (Lưu mẫu ngẫu nhiên hoặc khi có cảnh báo/có người để không quá tải DB)
        detection_id = None
        should_save = data.get('save_log', False) or (results['is_alert'] and int(time.time()) % 10 == 0)
        
        if should_save:
            detection = save_detection(
                detection_type='crowd_live',
                objects_detected=results['detected_people'],
                confidence_scores=[p['confidence'] for p in results['detected_people']],
                image=annotated_frame,
                image_prefix='crowd',
                processing_time=results['processing_time'],
                current_count=results['current_count'],
                in_count=results['total_in'],
                out_count=results['total_out'],
                density_level=results['density_level'],
                alert_triggered=results['is_alert']
            )
            if detection:
                detection_id = detection.id
                
        return jsonify({
            'success': True,
            'annotated_image': f'data:image/jpeg;base64,{annotated_base64}',
            'current_count': results['current_count'],
            'total_in': results['total_in'],
            'total_out': results['total_out'],
            'occupancy': results['occupancy'],
            'peak_count': results['peak_count'],
            'density_level': results['density_level'],
            'is_alert': results['is_alert'],
            'alert_threshold': results['alert_threshold'],
            'processing_time': results['processing_time'],
            'detection_id': detection_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@detection_bp.route('/reset_counter', methods=['POST'])
@login_required
def reset_counter():
    """Đặt lại bộ đếm IN/OUT về 0"""
    res = crowd_tracker.reset_counter()
    return jsonify(res)

@detection_bp.route('/update_config', methods=['POST'])
@login_required
def update_config():
    """Cập nhật vị trí vạch đếm hoặc ngưỡng cảnh báo"""
    data = request.get_json() or {}
    conf = data.get('conf')
    line_ratio = data.get('line_ratio')
    alert_threshold = data.get('alert_threshold')
    
    crowd_tracker.update_config(conf=conf, line_ratio=line_ratio, alert_threshold=alert_threshold)
    return jsonify({
        'success': True,
        'conf': crowd_tracker.conf_threshold,
        'line_ratio': crowd_tracker.line_ratio,
        'alert_threshold': crowd_tracker.alert_threshold
    })

@detection_bp.route('/heatmap', methods=['GET'])
@login_required
def get_heatmap():
    """Xuất bản đồ nhiệt (Crowd Heatmap) hiện tại"""
    try:
        # Tạo ảnh nền đen hoặc ảnh mẫu nếu chưa có camera
        base = np.zeros((480, 640, 3), dtype=np.uint8)
        heatmap_img = crowd_tracker.generate_heatmap(base)
        
        _, buffer = cv2.imencode('.jpg', heatmap_img)
        heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'heatmap_image': f'data:image/jpeg;base64,{heatmap_base64}',
            'points_count': len(crowd_tracker.heatmap_points)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@detection_bp.route('/detect_image', methods=['POST'])
@login_required
def detect_image():
    """Phát hiện và đếm số người trong 1 bức ảnh tải lên"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        img = cv2.imread(filepath)
        if img is None:
            return jsonify({'error': 'Invalid image file'}), 400
            
        start_time = time.time()
        model = crowd_tracker.get_model()
        results = model(img, conf=crowd_tracker.conf_threshold, imgsz=640, verbose=False)[0]
        processing_time = round(time.time() - start_time, 3)
        
        annotated_img = results.plot()
        person_count = len(results.boxes)
        
        # Mật độ
        if person_count < 5:
            density = "LOW"
        elif person_count <= 15:
            density = "MODERATE"
        elif person_count <= 25:
            density = "HIGH"
        else:
            density = "CRITICAL"
            
        # Vẽ banner thống kê lên ảnh
        cv2.putText(annotated_img, f"PEOPLE COUNT: {person_count} | DENSITY: {density}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        
        # Lưu ảnh đã vẽ
        annotated_filename = f"annotated_{filename}"
        annotated_path = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_path, annotated_img)
        
        # Lưu vào Database / Databricks
        objects_detected = [{'name': 'Person', 'box': box.xyxy[0].tolist(), 'confidence': float(box.conf[0])}
                            for box in results.boxes]
        confidence_scores = [float(box.conf[0]) for box in results.boxes]
        
        detection = save_detection(
            detection_type='crowd_image',
            objects_detected=objects_detected,
            confidence_scores=confidence_scores,
            image=annotated_img,
            image_prefix='upload',
            processing_time=processing_time,
            current_count=person_count,
            density_level=density,
            alert_triggered=(person_count >= crowd_tracker.alert_threshold)
        )
        
        return jsonify({
            'success': True,
            'person_count': person_count,
            'objects': [{'name': f'Người #{i+1}', 'confidence': c} for i, c in enumerate(confidence_scores)],
            'confidence_scores': confidence_scores,
            'density_level': density,
            'processing_time': processing_time,
            'annotated_image': f'/detection/uploads/{annotated_filename}',
            'detection_id': detection.id if detection else None
        })
        
    return jsonify({'error': 'File format not supported'}), 400

@detection_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    try:
        from flask import send_from_directory
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404
