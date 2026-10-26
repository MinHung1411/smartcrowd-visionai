from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app, send_file, flash
from flask_login import login_required, current_user
from app.models.user import User
from app.models.detection import Detection, db
from sqlalchemy import func
import json
import os
import cv2
import numpy as np

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Lấy dữ liệu theo phân quyền (Admin thấy toàn bộ, User thấy của mình)
    if current_user.is_admin():
        detections = Detection.query.order_by(Detection.timestamp.desc()).all()
    else:
        detections = Detection.query.filter_by(user_id=current_user.id).order_by(Detection.timestamp.desc()).all()
        
    total_events = len(detections)
    total_in = sum(d.in_count or 0 for d in detections)
    total_out = sum(d.out_count or 0 for d in detections)
    current_occupancy = max(0, total_in - total_out)
    
    # Lưu lượng người đỉnh điểm (Peak crowd size)
    peak_crowd = max((d.current_count or len(d.get_objects_detected()) for d in detections), default=0)
    
    # Tổng số lượt phát hiện người
    total_people_detected = sum(d.current_count or len(d.get_objects_detected()) for d in detections)
    
    # Số lần kích hoạt cảnh báo quá tải
    alert_count = sum(1 for d in detections if d.alert_triggered or (d.density_level or '').upper() == 'CRITICAL')
    
    # Phân phối lưu lượng theo 24 giờ (0h - 23h) cho biểu đồ Line Chart
    hourly_people = [0] * 24
    hourly_in = [0] * 24
    hourly_out = [0] * 24
    
    # Phân phối cấp độ mật độ (Donut Chart)
    density_counts = {'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
    
    # Phân phối theo 4 ca làm việc (Shift Bar Chart)
    shift_counts = {'Sáng (6h-12h)': 0, 'Chiều (12h-17h)': 0, 'Tối (17h-22h)': 0, 'Đêm (22h-6h)': 0}
    
    for d in detections:
        if d.timestamp:
            h = d.timestamp.hour
            p_count = d.current_count or len(d.get_objects_detected()) or 0
            hourly_people[h] += p_count
            hourly_in[h] += (d.in_count or 0)
            hourly_out[h] += (d.out_count or 0)
            
            if 6 <= h < 12:
                shift_counts['Sáng (6h-12h)'] += 1
            elif 12 <= h < 17:
                shift_counts['Chiều (12h-17h)'] += 1
            elif 17 <= h < 22:
                shift_counts['Tối (17h-22h)'] += 1
            else:
                shift_counts['Đêm (22h-6h)'] += 1
                
        lvl = (d.density_level or 'LOW').upper()
        if lvl in density_counts:
            density_counts[lvl] += 1
        else:
            density_counts['LOW'] += 1
            
    recent_events = detections[:8]
    
    return render_template('dashboard.html', 
                           total_events=total_events,
                           total_in=total_in,
                           total_out=total_out,
                           total_people_detected=total_people_detected,
                           current_occupancy=current_occupancy,
                           peak_crowd=peak_crowd,
                           alert_count=alert_count,
                           hourly_people=hourly_people,
                           hourly_in=hourly_in,
                           hourly_out=hourly_out,
                           density_counts=density_counts,
                           shift_counts=shift_counts,
                           recent_events=recent_events)

@main_bp.route('/api/generate_ai_report', methods=['POST'])
@login_required
def generate_ai_report():
    """Tự động tổng hợp và sinh báo cáo ca làm việc thông minh bằng AI"""
    try:
        from datetime import datetime
        detections = Detection.query.order_by(Detection.timestamp.desc()).all()
        
        total_records = len(detections)
        total_in = sum(d.in_count or 0 for d in detections)
        total_out = sum(d.out_count or 0 for d in detections)
        peak_crowd = max((d.current_count or 0 for d in detections), default=0)
        alerts = sum(1 for d in detections if d.alert_triggered or (d.density_level or '').upper() == 'CRITICAL')
        
        # Tìm giờ cao điểm nhất
        hour_counter = [0] * 24
        for d in detections:
            if d.timestamp:
                hour_counter[d.timestamp.hour] += (d.current_count or 0)
        peak_hour = hour_counter.index(max(hour_counter)) if any(hour_counter) else 17
        
        now_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        report_text = f"""### 📋 BÁO CÁO TỔNG QUAN LƯU LƯỢNG ĐÁM ĐÔNG & AN NINH
**Thời gian xuất báo cáo:** {now_str}  
**Hệ thống:** SmartCrowd AI Intelligence Platform (YOLOv11m + Databricks Lakehouse)  
**Phân quyền kiểm toán:** {current_user.username} ({current_user.role.upper()})

---

#### 1. Các Chỉ Số Lưu Lượng Trọng Yếu (KPIs):
- **Tổng số phiên giám sát ghi nhận:** `{total_records}` sự kiện.
- **Tổng lượt người đi vào (IN):** `{total_in}` lượt.
- **Tổng lượt người đi ra (OUT):** `{total_out}` lượt.
- **Lưu lượng hiện diện ước tính (Net Occupancy):** `{max(0, total_in - total_out)}` người.
- **Mật độ người tập trung cao nhất (Peak Density):** `{peak_crowd}` người/khung hình.
- **Khung giờ cao điểm nhất trong ngày:** `{peak_hour:02d}:00 - {peak_hour+1:02d}:00`.

#### 2. Đánh Giá An Toàn & Cảnh Báo Mật Độ:
- **Số lần vượt ngưỡng an toàn (Overcrowded Incidents):** `{alerts}` lần.
- **Mức độ tuân thủ quy định giãn cách:** {'🟢 Rất Tốt (Không có vi phạm)' if alerts == 0 else f'⚠️ Cần chú ý (Ghi nhận {alerts} lần vượt ngưỡng)'}.

#### 3. Khuyến Nghị Vận Hành Từ Hệ Thống AI:
1. **Phân bổ nhân sự:** Tăng cường 1-2 nhân viên giám sát tại khu vực cổng chính vào khung giờ cao điểm ({peak_hour:02d}:00).
2. **Điều phối luồng di chuyển:** Duy trì vạch kẻ hướng dẫn một chiều tại các cửa ngõ có tỷ lệ In/Out chênh lệch lớn.
3. **Đồng bộ hóa dữ liệu:** Toàn bộ log dữ liệu trên đã được nạp vào tầng **Bronze** và phân tích tại tầng **Gold** trên **Databricks Unity Catalog**.

*Báo cáo được tự động khởi tạo bởi SmartCrowd Analytics Engine.*"""

        return jsonify({'success': True, 'report': report_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    detections = Detection.query.filter_by(user_id=current_user.id)\
                               .order_by(Detection.timestamp.desc())\
                               .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('history.html', detections=detections)

@main_bp.route('/api/detection-details/<int:detection_id>')
@login_required
def get_detection_details(detection_id):
    detection = Detection.query.filter_by(id=detection_id, user_id=current_user.id).first()
    if not detection:
        return jsonify({'success': False, 'error': 'Detection not found'}), 404
    
    # Get and process objects
    raw_objects = detection.get_objects_detected()
    processed_objects = []
    
    for obj in raw_objects:
        if isinstance(obj, dict):
            processed_objects.append(obj)
        elif isinstance(obj, str):
            # Try to parse if it's a JSON string
            try:
                import json
                parsed_obj = json.loads(obj)
                processed_objects.append(parsed_obj)
            except:
                # If it's just a string, create object structure
                processed_objects.append({
                    'en': obj,
                    'vi': obj,
                    'confidence': 'N/A'
                })
        else:
            # Handle other types
            processed_objects.append({
                'en': str(obj),
                'vi': str(obj),
                'confidence': 'N/A'
            })
    
    # Check for annotated image (image with detection results)
    annotated_image_url = None
    if detection.image_path:
        # Try to find annotated image (usually prefixed with 'annotated_')
        import os
        base_filename = os.path.splitext(detection.image_path)[0]
        extension = os.path.splitext(detection.image_path)[1]
        annotated_filename = f"annotated_{base_filename}{extension}"
        annotated_path = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
        
        if os.path.exists(annotated_path):
            annotated_image_url = url_for('detection.uploaded_file', filename=annotated_filename)
        else:
            # Fallback to original image
            annotated_image_url = url_for('detection.uploaded_file', filename=detection.image_path)
    
    return jsonify({
        'success': True,
        'detection_type': detection.detection_type,
        'timestamp': detection.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'processing_time': detection.processing_time,
        'image_url': url_for('detection.uploaded_file', filename=detection.image_path) if detection.image_path else None,
        'annotated_image_url': annotated_image_url,
        'objects': processed_objects
    })

@main_bp.route('/api/delete-detection/<int:detection_id>', methods=['DELETE'])
@login_required
def delete_detection_api(detection_id):
    print(f"Attempting to delete detection {detection_id} for user {current_user.id}")
    detection = Detection.query.filter_by(id=detection_id, user_id=current_user.id).first()
    if not detection:
        print(f"Detection {detection_id} not found for user {current_user.id}")
        return jsonify({'success': False, 'error': 'Detection not found'}), 404
    
    try:
        print(f"Found detection {detection_id}: {detection.detection_type}")
        # Delete image file if exists
        if detection.image_path:
            import os
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete detection from database
        db.session.delete(detection)
        db.session.commit()
        
        # Trigger background pipeline update to sync Silver and Gold tables
        try:
            from threading import Thread
            from app.services.db_service import trigger_pipeline_update
            Thread(target=trigger_pipeline_update).start()
        except Exception as te:
            print(f"DEBUG: Failed to trigger background pipeline update: {te}")
        
        print(f"Successfully deleted detection {detection_id}")
        return jsonify({'success': True, 'message': 'Detection deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting detection {detection_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/delete-all-detections', methods=['DELETE'])
@login_required
def delete_all_detections_api():
    try:
        # Get all user detections
        detections = Detection.query.filter_by(user_id=current_user.id).all()
        
        # Delete all image files
        import os
        for detection in detections:
            if detection.image_path:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
        
        # Delete all detections from database in bulk
        Detection.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
        db.session.commit()
        
        # Trigger background pipeline update to sync Silver and Gold tables
        try:
            from threading import Thread
            from app.services.db_service import trigger_pipeline_update
            Thread(target=trigger_pipeline_update).start()
        except Exception as te:
            print(f"DEBUG: Failed to trigger background pipeline update: {te}")
        
        return jsonify({'success': True, 'message': 'All detections deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/export-detection/<int:detection_id>')
@login_required
def export_single_detection(detection_id):
    try:
        import csv
        from io import StringIO
        from flask import Response
        
        detection = Detection.query.filter_by(id=detection_id, user_id=current_user.id).first()
        if not detection:
            return jsonify({'success': False, 'error': 'Detection not found'}), 404
        
        # Get objects
        objects = detection.get_objects_detected()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Detection Details'])
        writer.writerow(['ID', detection.id])
        writer.writerow(['Type', detection.detection_type])
        writer.writerow(['Timestamp', detection.timestamp.strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Processing Time (s)', detection.processing_time or 0])
        writer.writerow(['Objects Count', len(objects)])
        writer.writerow([])
        writer.writerow(['Detected Objects'])
        writer.writerow(['No.', 'English Name', 'Vietnamese Name', 'Confidence (%)'])
        
        # Write objects - handle different formats like in details API
        for i, obj in enumerate(objects, 1):
            object_name = ''
            vietnamese_name = ''
            confidence = 'N/A'
            
            if obj and isinstance(obj, dict):
                # Handle different object formats
                if 'class' in obj and 'name' in obj and 'confidence' in obj:
                    # Object Detection format: {class: 'airplane', name: {...}, confidence: 0.91}
                    object_name = obj.get('class', 'Unknown')
                    if isinstance(obj.get('name'), dict):
                        vietnamese_name = obj['name'].get('vi') or obj['name'].get('en') or obj.get('class', 'Unknown')
                    else:
                        vietnamese_name = obj.get('name') or obj.get('class', 'Unknown')
                    confidence = obj.get('confidence')
                    if confidence and isinstance(confidence, (int, float)):
                        confidence = f"{(confidence * 100):.1f}"
                    else:
                        confidence = 'N/A'
                elif 'name' in obj and 'hex' in obj and 'percentage' in obj:
                    # Color Detection format: {name: 'Dark Gray', hex: '#2c3240', percentage: 5.26}
                    object_name = obj.get('name', 'Unknown')
                    vietnamese_name = obj.get('name', 'Unknown')
                    percentage = obj.get('percentage')
                    confidence = f"{percentage:.1f}" if percentage else 'N/A'
                elif 'en' in obj or 'vi' in obj:
                    # Standard format: {en: 'Person', vi: 'Người', confidence: 95.2}
                    object_name = obj.get('en') or obj.get('name') or obj.get('class_name') or obj.get('label') or 'Unknown'
                    vietnamese_name = obj.get('vi') or obj.get('name') or obj.get('class_name') or obj.get('label') or 'Unknown'
                    confidence = obj.get('confidence') or obj.get('score') or obj.get('probability') or 'N/A'
                else:
                    # Fallback
                    object_name = obj.get('name') or obj.get('class') or obj.get('label') or str(obj)
                    vietnamese_name = obj.get('name') or obj.get('class') or obj.get('label') or str(obj)
                    confidence = obj.get('confidence') or obj.get('score') or obj.get('percentage') or 'N/A'
            elif isinstance(obj, str):
                object_name = obj
                vietnamese_name = obj
                confidence = 'N/A'
            else:
                object_name = str(obj)
                vietnamese_name = str(obj)
                confidence = 'N/A'
            
            writer.writerow([i, object_name, vietnamese_name, confidence])
        
        # Create response
        output.seek(0)
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=detection_{detection_id}_details.csv'
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/export-detections')
@login_required
def export_detections():
    try:
        import csv
        from io import StringIO
        from flask import Response
        
        # Get all user detections
        detections = Detection.query.filter_by(user_id=current_user.id).order_by(Detection.timestamp.desc()).all()
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['ID', 'Loại Giám Sát', 'Thời Gian', 'Thời Gian Xử Lý (s)', 'Số Người Hiện Diện', 'Lượt Vào (IN)', 'Lượt Ra (OUT)', 'Mật Độ', 'Cảnh Báo Quá Tải'])
        
        # Write data
        for detection in detections:
            writer.writerow([
                detection.id,
                detection.detection_type,
                detection.timestamp.strftime('%Y-%m-%d %H:%M:%S') if detection.timestamp else '',
                detection.processing_time or 0,
                detection.current_count or len(detection.get_objects_detected()),
                detection.in_count or 0,
                detection.out_count or 0,
                detection.density_level or 'LOW',
                'CÓ' if detection.alert_triggered else 'KHÔNG'
            ])
        
        # Create response
        output.seek(0)
        response = Response(output.getvalue(), mimetype='text/csv')
        response.headers['Content-Disposition'] = 'attachment; filename=detection_history.csv'
        
        return response
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/activity')
@login_required
def activity():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all recent activities
    recent_detections = Detection.query.order_by(Detection.timestamp.desc()).limit(50).all()
    recent_users = User.query.order_by(User.last_login.desc()).limit(20).all()
    
    return render_template('activity.html', 
                         recent_detections=recent_detections,
                         recent_users=recent_users)

@main_bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@main_bp.route('/api/recent-detections')
def api_recent_detections():
    """Get recent detections for display"""
    detection_type = request.args.get('type', 'all')
    
    query = Detection.query
    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            query = query.filter_by(user_id=current_user.id)
        else:
            query = query.filter_by(user_id=1)  # Default user
    except:
        query = query.filter_by(user_id=1)  # Default user
    
    if detection_type != 'all':
        query = query.filter_by(detection_type=detection_type)
    
    recent_detections = query.order_by(Detection.timestamp.desc()).limit(12).all()
    
    detections_data = []
    for detection in recent_detections:
        objects_detected = detection.get_objects_detected()
        
        # Extract dominant info for face detections
        dominant_info = None
        confidence = 0
        
        if (detection.detection_type == 'face' or detection.detection_type == 'face_camera') and objects_detected:
            # Get the face with highest confidence
            dominant_info_obj = max(objects_detected, key=lambda x: x.get('confidence', 0))
            dominant_info = dominant_info_obj.get('name', 'Unknown')
            confidence = dominant_info_obj.get('confidence', 0)
        
        detections_data.append({
            'id': detection.id,
            'image_path': detection.image_path,
            'detection_type': detection.detection_type,
            'processing_time': detection.processing_time,
            'timestamp': detection.timestamp.isoformat(),
            'objects_detected': detection.objects_detected,
            'confidence_scores': detection.confidence_scores,
            'dominant_info': dominant_info,  # Add for face detection
            'confidence': confidence  # Add for face detection
        })
    
    return jsonify({
        'success': True,
        'detections': detections_data,
        'count': len(detections_data)
    })

@main_bp.route('/api/detection/<int:detection_id>/delete', methods=['DELETE'])
@login_required
def delete_detection(detection_id):
    """Delete a specific detection"""
    detection = Detection.query.filter_by(id=detection_id, user_id=current_user.id).first()
    
    if not detection:
        return jsonify({'error': 'Detection not found'}), 404
    
    # Delete image file
    try:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
    except Exception as e:
        print(f"Error deleting image file: {e}")
    
    # Delete database record
    db.session.delete(detection)
    db.session.commit()
    
    # Trigger background pipeline update to sync Silver and Gold tables
    try:
        from threading import Thread
        from app.services.db_service import trigger_pipeline_update
        Thread(target=trigger_pipeline_update).start()
    except Exception as te:
        print(f"DEBUG: Failed to trigger background pipeline update: {te}")
    
    return jsonify({'success': True, 'message': 'Detection deleted successfully'})

@main_bp.route('/api/detections/delete-all', methods=['DELETE'])
@login_required
def delete_all_detections():
    """Delete all detections for current user"""
    detection_type = request.args.get('type', 'all')
    
    query = Detection.query.filter_by(user_id=current_user.id)
    
    if detection_type != 'all':
        query = query.filter_by(detection_type=detection_type)
    
    detections = query.all()
    
    # Delete all image files
    for detection in detections:
        try:
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error deleting image file {detection.image_path}: {e}")
    
    # Delete all database records in bulk to prevent transaction conflicts in Databricks
    if detection_type != 'all':
        Detection.query.filter_by(user_id=current_user.id, detection_type=detection_type).delete(synchronize_session=False)
    else:
        Detection.query.filter_by(user_id=current_user.id).delete(synchronize_session=False)
    
    db.session.commit()
    
    # Trigger background pipeline update to sync Silver and Gold tables
    try:
        from threading import Thread
        from app.services.db_service import trigger_pipeline_update
        Thread(target=trigger_pipeline_update).start()
    except Exception as te:
        print(f"DEBUG: Failed to trigger background pipeline update: {te}")
    
    return jsonify({'success': True, 'message': f'All {detection_type} detections deleted successfully'})

@main_bp.route('/api/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
def toggle_user_admin(user_id):
    """Toggle admin rights for a user"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    # Prevent self-modification
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot modify your own admin rights'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    try:
        data = request.get_json()
        print(f"DEBUG: Raw request data: {data}")
        print(f"DEBUG: Request content type: {request.content_type}")
        print(f"DEBUG: Request form: {request.form}")
        
        make_admin = data.get('make_admin', False)
        print(f"DEBUG: Parsed make_admin: {make_admin}")
        print(f"DEBUG: Type of make_admin: {type(make_admin)}")
        
        print(f"DEBUG: Toggling admin rights for user {user_id}")
        print(f"DEBUG: Current user role: {user.role}")
        print(f"DEBUG: Make admin: {make_admin}")
        
        user.role = 'admin' if make_admin else 'user'
        print(f"DEBUG: New user role: {user.role}")
        
        db.session.commit()
        print(f"DEBUG: Database committed")
        
        # Verify the change
        db.session.refresh(user)
        print(f"DEBUG: Verified user role after commit: {user.role}")
        print(f"DEBUG: user.is_admin(): {user.is_admin()}")
        
        action = 'granted' if make_admin else 'removed'
        return jsonify({
            'success': True, 
            'message': f'Admin rights {action} successfully',
            'user_role': user.role,
            'user_is_admin': user.is_admin(),
            'make_admin_received': make_admin
        })
        
    except Exception as e:
        print(f"Error toggling admin rights for user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/users/<int:user_id>/delete', methods=['DELETE'])
@login_required
def delete_user_account(user_id):
    """Delete user account and all associated data"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    # Prevent self-deletion
    if user_id == current_user.id:
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    try:
        print(f"DEBUG: Deleting user {user_id} ({user.username})")
        
        # Get all detections for this user
        detections = Detection.query.filter_by(user_id=user_id).all()
        print(f"DEBUG: Found {len(detections)} detections for user {user_id}")
        
        # Delete all detection image files
        deleted_files = 0
        for detection in detections:
            try:
                image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
                if os.path.exists(image_path):
                    os.remove(image_path)
                    deleted_files += 1
                    print(f"DEBUG: Deleted image file: {image_path}")
            except Exception as e:
                print(f"DEBUG: Error deleting image file {image_path}: {e}")
        
        # Delete all detection records in bulk to prevent transaction conflicts in Databricks
        Detection.query.filter_by(user_id=user_id).delete(synchronize_session=False)
        
        # Delete user account
        db.session.delete(user)
        db.session.commit()
        
        # Trigger background pipeline update to sync Silver and Gold tables
        try:
            from threading import Thread
            from app.services.db_service import trigger_pipeline_update
            Thread(target=trigger_pipeline_update).start()
        except Exception as te:
            print(f"DEBUG: Failed to trigger background pipeline update: {te}")
        
        print(f"DEBUG: Successfully deleted user {user_id} and {len(detections)} detections")
        print(f"DEBUG: Deleted {deleted_files} image files")
        
        return jsonify({
            'success': True, 
            'message': f'Account for "{user.username}" deleted successfully',
            'deleted_detections': len(detections),
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        print(f"Error deleting user account {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        
        print(f"DEBUG: Updating profile for user {current_user.id}")
        print(f"DEBUG: Profile data received: {data}")
        
        # Update birth_date if provided
        birth_date = data.get('birth_date')
        if birth_date:
            from datetime import datetime
            try:
                current_user.birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
                print(f"DEBUG: Updated birth_date to {current_user.birth_date}")
            except ValueError as e:
                print(f"DEBUG: Invalid birth_date format: {e}")
                return jsonify({'success': False, 'error': 'Invalid birth date format'}), 400
        
        # Update location if provided
        location = data.get('location')
        if location is not None:
            current_user.location = location.strip() if location.strip() else None
            print(f"DEBUG: Updated location to {current_user.location}")
        
        # Save changes
        db.session.commit()
        print(f"DEBUG: Profile updated successfully")
        
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'birth_date': current_user.birth_date.strftime('%Y-%m-%d') if current_user.birth_date else None,
            'location': current_user.location
        })
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/detection/<int:detection_id>/download')
@login_required
def download_detection_image(detection_id):
    """Download detection image with bounding boxes"""
    try:
        detection = Detection.query.filter_by(
            id=detection_id,
            user_id=current_user.id
        ).first()
        
        if not detection:
            return jsonify({'error': 'Detection not found'}), 404
        
        # Get image path
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], detection.image_path)
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Load original image
        img = cv2.imread(image_path)
        
        if img is None:
            return jsonify({'error': 'Cannot load image'}), 500
        
        # Get detection results
        objects_detected = detection.get_objects_detected()
        confidence_scores = detection.get_confidence_scores()
        
        # Draw bounding boxes on image
        annotated_img = _draw_detection_boxes(img, objects_detected, confidence_scores)
        
        # Create temporary file for annotated image
        temp_filename = f'annotated_{detection_id}_{detection.detection_type}.jpg'
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], temp_filename)
        cv2.imwrite(temp_path, annotated_img)
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f'detection_{detection_id}_{detection.detection_type}_annotated.jpg'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _draw_detection_boxes(img, objects_detected, confidence_scores):
    """Draw simple labels with object names and confidence on image"""
    annotated_img = img.copy()
    
    # Add title at the top
    cv2.putText(annotated_img, "Detection Results", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Draw object names and confidence
    y_position = 70
    for i, (obj, confidence) in enumerate(zip(objects_detected, confidence_scores)):
        # Handle different object formats
        if isinstance(obj, dict):
            if 'name' in obj and isinstance(obj['name'], dict):
                # Upload detection format (new)
                name_dict = obj['name']
                label = name_dict.get('en', name_dict.get('vi', f'Object {i+1}'))
            elif 'name' in obj:
                # Camera detection format
                label = obj.get('name', f'Object {i+1}')
            elif 'en' in obj or 'vi' in obj:
                # Old format
                label = obj.get('en', obj.get('vi', f'Object {i+1}'))
            else:
                # Fallback
                label = obj.get('class', f'Object {i+1}')
        elif isinstance(obj, str):
            # Simple string format
            label = obj
        else:
            # Other format - skip
            continue
        
        # Create label text
        confidence_percent = f"{confidence * 100:.1f}"
        label_text = f"{i+1}. {label}: {confidence_percent}%"
        
        # Draw text
        cv2.putText(annotated_img, label_text, (10, y_position), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        y_position += 30
    
    return annotated_img

