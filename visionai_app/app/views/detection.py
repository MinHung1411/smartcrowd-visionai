from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.detection import Detection, db
from app.models.user import User
from app.services.db_service import save_detection, save_annotated_image
from ultralytics import YOLO
import cv2
import os
import time
import json
from datetime import datetime
import uuid

detection_bp = Blueprint('detection', __name__)

# Initialize YOLO model (lazy loading to avoid import issues during app initialization)
model = None

def get_model():
    global model
    if model is None:
        import torch
        # Monkey patch torch.load to use weights_only=False for YOLO
        original_torch_load = torch.load
        def patched_torch_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_torch_load(*args, **kwargs)
        torch.load = patched_torch_load
        
        try:
            model = YOLO('yolov8n.pt')
        finally:
            # Restore original torch.load
            torch.load = original_torch_load
    return model

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_bilingual_label(label):
    from config.config import Config
    labels = Config.OBJECT_LABELS
    if label.lower() in labels:
        return labels[label.lower()]
    else:
        # Fallback for unknown labels
        return {'en': label, 'vi': label}

@detection_bp.route('/camera')
@login_required
def camera():
    return render_template('detection/camera.html')

@detection_bp.route('/upload')
@login_required
def upload():
    return render_template('detection/upload.html')

@detection_bp.route('/detect_image', methods=['POST'])
@login_required
def detect_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read image
        img = cv2.imread(filepath)
        
        # Store original dimensions
        original_height, original_width = img.shape[:2]
        scale_factor = 1.0
        
        # Resize image for faster processing
        if max(original_height, original_width) > 640:
            scale_factor = 640 / max(original_height, original_width)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            img = cv2.resize(img, (new_width, new_height))
            cv2.imwrite(filepath, img)  # Save resized image
        
        # Perform detection
        start_time = time.time()
        detection_model = get_model()
        results = detection_model(img, verbose=False)  # Disable verbose output
        processing_time = time.time() - start_time
        
        # Process results
        objects_detected = []
        confidence_scores = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = detection_model.names[cls]
                    
                    bilingual_label = get_bilingual_label(class_name)
                    
                    # Get bounding box coordinates and scale to original image size
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    
                    # Scale coordinates back to original image size
                    if scale_factor != 1.0:
                        x1 = x1 / scale_factor
                        y1 = y1 / scale_factor
                        x2 = x2 / scale_factor
                        y2 = y2 / scale_factor
                    
                    # Store object with bounding box coordinates (like camera detection)
                    objects_detected.append({
                        'name': bilingual_label,
                        'confidence': conf,
                        'x1': x1,
                        'y1': y1,
                        'x2': x2,
                        'y2': y2,
                        'class': class_name,
                        'bilingual': bilingual_label
                    })
                    confidence_scores.append(conf)
        
        # Draw bounding boxes on image
        img_annotated = cv2.imread(filepath)
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = detection_model.names[cls]
                    cv2.rectangle(img_annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    label = f"{class_name}: {conf:.2f}"
                    cv2.putText(img_annotated, label, (x1, y1-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Save detection + original image to Databricks via db_service
        detection = save_detection(
            detection_type='upload',
            objects_detected=objects_detected,
            confidence_scores=confidence_scores,
            image=cv2.imread(filepath),
            image_prefix='upload',
            processing_time=processing_time
        )

        # Save annotated image
        annotated_filename = save_annotated_image(img_annotated,
                                                   os.path.basename(filepath))

        detection_id = detection.id if detection else None
        return jsonify({
            'success': True,
            'objects': objects_detected,
            'confidence_scores': confidence_scores,
            'processing_time': processing_time,
            'annotated_image': f'/detection/uploads/annotated_{os.path.basename(filepath)}',
            'detection_id': detection_id
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@detection_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

@detection_bp.route('/detect_camera', methods=['POST'])
@login_required
def detect_camera():
    data = request.get_json()
    image_data = data.get('image')
    
    print(f"Camera detection called for user {current_user.id}")
    
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Decode base64 image
        import base64
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        import numpy as np
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Perform detection
        start_time = time.time()
        detection_model = get_model()
        
        # Store original dimensions
        original_height, original_width = img.shape[:2]
        scale_factor = 1.0
        
        # Resize image for faster processing
        if max(original_height, original_width) > 640:
            scale_factor = 640 / max(original_height, original_width)
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            img = cv2.resize(img, (new_width, new_height))
        
        results = detection_model(img, verbose=False)  # Disable verbose output
        processing_time = time.time() - start_time
        
        # Process results
        objects_detected = []
        confidence_scores = []
        annotated_image_data = None
        bounding_boxes = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = detection_model.names[cls]
                    
                    bilingual_label = get_bilingual_label(class_name)
                    objects_detected.append(bilingual_label)
                    confidence_scores.append(conf)
                    
                    # Get bounding box coordinates and scale to original image size
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    
                    # Scale coordinates back to original image size
                    if scale_factor != 1.0:
                        x1 = x1 / scale_factor
                        y1 = y1 / scale_factor
                        x2 = x2 / scale_factor
                        y2 = y2 / scale_factor
                    
                    bounding_boxes.append({
                        'x1': x1,
                        'y1': y1, 
                        'x2': x2,
                        'y2': y2,
                        'class': class_name,
                        'confidence': conf,
                        'bilingual': bilingual_label
                    })
        
        # Draw bounding boxes on image
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    class_name = detection_model.names[cls]
                    
                    # Draw rectangle
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw label with confidence
                    label = f"{class_name}: {conf:.2f}"
                    cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Convert annotated image back to base64
        _, buffer = cv2.imencode('.jpg', img)
        annotated_image_data = base64.b64encode(buffer).decode('utf-8')
        
        # Save detection + annotated image to Databricks via db_service
        detection = save_detection(
            detection_type='camera',
            objects_detected=objects_detected,
            confidence_scores=confidence_scores,
            image=img,
            image_prefix='camera',
            processing_time=processing_time
        )

        detection_id = detection.id if detection else None
        print(f"[detect_camera] Saved to DB | objects={len(objects_detected)} | id={detection_id}")

        return jsonify({
            'success': True,
            'objects': objects_detected,
            'confidence_scores': confidence_scores,
            'processing_time': processing_time,
            'annotated_image': f'data:image/jpeg;base64,{annotated_image_data}',
            'detection_id': detection_id,
            'bounding_boxes': bounding_boxes
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@detection_bp.route('/detection/<int:detection_id>/download')
@login_required
def download_detection_image(detection_id):
    """Download detection image"""
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
        
        return send_file(
            image_path,
            as_attachment=True,
            download_name=f'detection_{detection_id}_{detection.detection_type}.jpg'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
