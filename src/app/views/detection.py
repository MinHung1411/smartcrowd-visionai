from flask import Blueprint, render_template, request, jsonify, current_app, send_file, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.detection import Detection, db
from app.services.db_service import save_detection, save_annotated_image
from app.services.crowd_service import crowd_tracker
from app.services.alert_service import alert_service
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
    """Trang giám sát Camera Real-time: Đếm người, Kẻ vạch 2 chiều & Vùng cấm Polygon ROI"""
    return render_template('detection/camera.html',
                           alert_threshold=crowd_tracker.alert_threshold,
                           line_ratio=crowd_tracker.line_ratio,
                           has_roi=crowd_tracker.restricted_polygon is not None)

@detection_bp.route('/video')
@login_required
def video():
    """Trang tải lên và phân tích chuyên sâu Video CCTV đám đông"""
    return render_template('detection/video.html',
                           alert_threshold=crowd_tracker.alert_threshold,
                           line_ratio=crowd_tracker.line_ratio)

@detection_bp.route('/upload')
@login_required
def upload():
    """Trang tải ảnh đơn để phân tích đám đông & mật độ"""
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
    - Giám sát xâm nhập vùng cấm (Polygon ROI)
    - Tự động phát cảnh báo quá tải / an ninh
    - Trả về frame đã vẽ Bounding Box, Quỹ đạo, Vạch đếm, Vùng cấm và HUD
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
        
        # Kích hoạt cảnh báo tự động nếu vi phạm ngưỡng hoặc có người xâm nhập
        if results['has_intrusion']:
            alert_service.trigger_alert(
                'INTRUSION',
                'Phát hiện xâm nhập vùng cấm',
                f'Có đối tượng xâm nhập vào khu vực bảo vệ nghiêm ngặt! Số người trong khung hình: {results["current_count"]}',
                count=results['current_count']
            )
        elif results['is_alert']:
            alert_service.trigger_alert(
                'OVERCROWDED',
                'Cảnh báo quá tải đám đông',
                f'Mật độ đám đông vượt ngưỡng an toàn ({results["current_count"]}/{results["alert_threshold"]}). Cần điều phối luồng người!',
                count=results['current_count'],
                threshold=results['alert_threshold']
            )
        
        # Chuyển frame kết quả sang Base64 gửi về frontend
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        annotated_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Lưu vào Database (Lưu mẫu ngẫu nhiên hoặc khi có cảnh báo/có người để không quá tải DB)
        detection_id = None
        should_save = data.get('save_log', False) or ((results['is_alert'] or results['has_intrusion']) and int(time.time()) % 10 == 0)
        
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
                alert_triggered=(results['is_alert'] or results['has_intrusion'])
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
            'has_intrusion': results['has_intrusion'],
            'has_roi': results['has_roi'],
            'intrusions_count': len(results['intrusions']),
            'alert_threshold': results['alert_threshold'],
            'processing_time': results['processing_time'],
            'detection_id': detection_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@detection_bp.route('/set_polygon_roi', methods=['POST'])
@login_required
def set_polygon_roi():
    """Thiết lập hoặc xóa vùng cấm an ninh Polygon ROI"""
    data = request.get_json() or {}
    polygon = data.get('polygon')
    
    if polygon:
        res = crowd_tracker.set_restricted_polygon(polygon)
    else:
        res = crowd_tracker.clear_restricted_polygon()
        
    return jsonify(res)

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

@detection_bp.route('/process_video', methods=['POST'])
@login_required
def process_video():
    """
    Tải lên và xử lý toàn diện file video:
    - Chạy YOLOv11m + ByteTrack
    - Đếm người cắt qua vạch 2 chiều
    - Tạo video đã annotate có thể tải về
    - Tạo bản đồ nhiệt Heatmap tích lũy
    - Lưu vào Database / Databricks Lakehouse
    """
    if 'file' not in request.files:
        return jsonify({'error': 'Không có file video được gửi lên'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Chưa chọn file'}), 400
        
    if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov', 'mkv'}):
        return jsonify({'error': 'Định dạng video không được hỗ trợ (chỉ nhận .mp4, .avi, .mov)'}), 400
        
    try:
        # Lưu file tải lên
        video_uuid = str(uuid.uuid4())
        ext = file.filename.rsplit('.', 1)[1].lower()
        input_filename = f"input_{video_uuid}.{ext}"
        output_filename = f"output_{video_uuid}.mp4"
        heatmap_filename = f"heatmap_{video_uuid}.jpg"
        
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        input_path = os.path.join(upload_folder, input_filename)
        output_path = os.path.join(upload_folder, output_filename)
        heatmap_path = os.path.join(upload_folder, heatmap_filename)
        
        file.save(input_path)
        
        # Nhận tham số tùy chỉnh
        conf = float(request.form.get('conf', crowd_tracker.conf_threshold))
        frame_step = int(request.form.get('frame_step', 2))
        line_ratio = float(request.form.get('line_ratio', crowd_tracker.line_ratio))
        max_seconds = int(request.form.get('max_seconds', 180))
        
        # Xử lý video
        results = crowd_tracker.process_video_file(
            input_path=input_path,
            output_path=output_path,
            conf=conf,
            frame_step=frame_step,
            max_seconds=max_seconds,
            line_ratio=line_ratio
        )
        
        # Lưu ảnh Heatmap nếu có
        heatmap_url = None
        if results['heatmap_img'] is not None:
            cv2.imwrite(heatmap_path, results['heatmap_img'])
            heatmap_url = f'/detection/uploads/{heatmap_filename}'
            
        # Lưu kết quả vào Database / Databricks
        detection = save_detection(
            detection_type='crowd_video',
            objects_detected=[{'name': 'Person', 'count': results['unique_visitors']}],
            confidence_scores=[conf],
            image=results['heatmap_img'] if results['heatmap_img'] is not None else None,
            image_prefix='video_heat',
            processing_time=results['processing_time'],
            current_count=results['unique_visitors'],
            in_count=results['total_in'],
            out_count=results['total_out'],
            density_level="HIGH" if results['peak_in_frame'] > 20 else "MODERATE",
            alert_triggered=(results['peak_in_frame'] >= crowd_tracker.alert_threshold)
        )
        
        return jsonify({
            'success': True,
            'video_url': f'/detection/uploads/{output_filename}',
            'heatmap_url': heatmap_url,
            'total_in': results['total_in'],
            'total_out': results['total_out'],
            'net_occupancy': results['net_occupancy'],
            'peak_in_frame': results['peak_in_frame'],
            'unique_visitors': results['unique_visitors'],
            'processed_frames': results['processed_frames'],
            'total_video_frames': results['total_video_frames'],
            'processing_time': results['processing_time'],
            'processing_fps': results['processing_fps'],
            'timeline': results['timeline'],
            'detection_id': detection.id if detection else None
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
        conf = float(request.form.get('conf', 0.35))
        
        # Chế độ Remote AI Microservice (Render Cloud)
        if crowd_tracker.is_remote_enabled():
            remote_res = crowd_tracker.detect_image_remote(filepath, conf=conf)
            if remote_res is not None:
                annotated_img, person_count = remote_res
                processing_time = round(time.time() - start_time, 3)
                
                if person_count < 5:
                    density = "LOW"
                elif person_count <= 15:
                    density = "MODERATE"
                elif person_count <= 25:
                    density = "HIGH"
                else:
                    density = "CRITICAL"
                    
                cv2.putText(annotated_img, f"PEOPLE COUNT: {person_count} | DENSITY: {density}",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
                
                annotated_filename = f"annotated_{filename}"
                annotated_path = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
                cv2.imwrite(annotated_path, annotated_img)
                
                confidence_scores = [conf] * person_count
                objects_detected = [{'name': 'Person', 'confidence': conf} for _ in range(person_count)]
                
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

        # Chế độ Local AI với NMS lọc trùng lặp iou=0.45 chuẩn xác
        model = crowd_tracker.get_model()
        results = model(img, conf=conf, iou=0.45, imgsz=640, device='cpu', verbose=False)[0]
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

@detection_bp.route('/test_alert', methods=['POST'])
@login_required
def test_alert():
    """Thử nghiệm kích hoạt hệ thống phát cảnh báo (Telegram/Webhook)"""
    res = alert_service.trigger_alert(
        'TEST_ALARM',
        'Cảnh báo thử nghiệm SmartCrowd',
        'Kiểm tra kết nối và độ trễ của hệ thống thông báo sự cố tức thời.',
        count=25,
        threshold=20
    )
    return jsonify(res)

@detection_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 404
