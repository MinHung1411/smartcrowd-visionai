from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
import cv2
import base64
import numpy as np
import time
import uuid
import os
from werkzeug.utils import secure_filename
from app.services.classification_service import classification_service
from app.models.detection import Detection
from app import db

classification_bp = Blueprint('classification', __name__, url_prefix='/classification')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@classification_bp.route('/object_classification')
@login_required
def object_classification():
    """Object Classification interface"""
    return render_template('classification/object_classification.html')

@classification_bp.route('/classify_upload', methods=['POST'])
@login_required
def classify_upload():
    """Classify objects from uploaded image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Read image
            image_stream = file.read()
            nparr = np.frombuffer(image_stream, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return jsonify({'error': 'Invalid image format'}), 400
            
            # Perform object classification
            start_time = time.time()
            classification_results = classification_service.classify_objects(img)
            processing_time = time.time() - start_time
            
            if not classification_results['success']:
                return jsonify({'error': classification_results['error']}), 500
            
            # Draw classification results on image
            annotated_img = img.copy()
            h, w = img.shape[:2]
            
            # Draw classification boxes and labels
            for obj in classification_results['objects']:
                if 'box' in obj:
                    x1, y1, x2, y2 = obj['box']
                    confidence = obj['confidence']
                    class_name = obj['class_name']
                    
                    # Draw bounding box
                    color = (0, 255, 0)
                    cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
                    
                    # Draw label
                    label = f"{class_name}: {confidence:.2f}"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                    cv2.rectangle(annotated_img, (x1, y1 - 25), 
                                 (x1 + label_size[0], y1), color, -1)
                    cv2.putText(annotated_img, label, (x1, y1 - 5), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            # Convert annotated image to base64
            _, buffer = cv2.imencode('.jpg', annotated_img)
            annotated_image_data = base64.b64encode(buffer).decode('utf-8')
            
            # Save classification to database
            filename = f'classification_{uuid.uuid4()}.jpg'
            cv2.imwrite(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), img)
            
            detection = Detection(
                user_id=current_user.id,
                image_path=filename,
                detection_type='classification',
                processing_time=processing_time
            )
            
            # Prepare data for database
            objects_detected = []
            confidence_scores = []
            
            for obj in classification_results['objects']:
                objects_detected.append({
                    'name': obj['class_name'],
                    'confidence': obj['confidence'],
                    'box': obj.get('box', (0, 0, 0, 0))
                })
                confidence_scores.append(obj['confidence'])
            
            detection.set_objects_detected(objects_detected)
            detection.set_confidence_scores(confidence_scores)
            
            db.session.add(detection)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'annotated_image': f"data:image/jpeg;base64,{annotated_image_data}",
                'objects': classification_results['objects'],
                'dominant_class': classification_results['dominant_class'],
                'confidence': classification_results['confidence'],
                'processing_time': processing_time,
                'detection_id': detection.id
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file format'}), 400

@classification_bp.route('/classify_camera', methods=['POST'])
@login_required
def classify_camera():
    """Classify objects from camera image"""
    data = request.get_json()
    image_data = data.get('image')
    
    if not image_data:
        return jsonify({'error': 'No image data provided'}), 400
    
    try:
        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Perform object classification
        start_time = time.time()
        classification_results = classification_service.classify_objects(img)
        processing_time = time.time() - start_time
        
        if not classification_results['success']:
            return jsonify({'error': classification_results['error']}), 500
        
        # Prepare data for database
        objects_detected = []
        confidence_scores = []
        bounding_boxes = []
        
        for obj in classification_results['objects']:
            objects_detected.append({
                'name': obj['class_name'],
                'confidence': obj['confidence'],
                'box': obj.get('box', (0, 0, 0, 0))
            })
            confidence_scores.append(obj['confidence'])
            
            if 'box' in obj:
                x1, y1, x2, y2 = obj['box']
                bounding_boxes.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'class_name': obj['class_name'],
                    'confidence': obj['confidence']
                })
        
        # Create result
        result = {
            'success': True,
            'objects': objects_detected,
            'dominant_class': classification_results['dominant_class'],
            'confidence': classification_results['confidence'],
            'processing_time': processing_time,
            'bounding_boxes': bounding_boxes
        }
        
        # Save classification to database
        filename = f'classification_camera_{uuid.uuid4()}.jpg'
        cv2.imwrite(os.path.join(current_app.config['UPLOAD_FOLDER'], filename), img)
        
        detection = Detection(
            user_id=current_user.id,
            image_path=filename,
            detection_type='classification',
            processing_time=processing_time
        )
        
        detection.set_objects_detected(objects_detected)
        detection.set_confidence_scores(confidence_scores)
        
        db.session.add(detection)
        db.session.commit()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@classification_bp.route('/api/recent-classifications')
@login_required
def get_recent_classifications():
    """Get recent object classifications for display"""
    try:
        # Get recent classification detections from database
        detections = Detection.query.filter_by(
            detection_type='classification',
            user_id=current_user.id
        ).order_by(Detection.timestamp.desc()).limit(10).all()
        
        recent_classifications = []
        for detection in detections:
            objects_detected = detection.get_objects_detected()
            if objects_detected:
                # Get dominant class
                dominant_class = max(objects_detected, key=lambda x: x.get('confidence', 0))
                
                recent_classifications.append({
                    'id': detection.id,
                    'timestamp': detection.timestamp.isoformat(),
                    'dominant_class': dominant_class.get('name', 'Unknown'),
                    'confidence': dominant_class.get('confidence', 0),
                    'processing_time': detection.processing_time,
                    'image_path': detection.image_path
                })
        
        return jsonify({
            'success': True,
            'classifications': recent_classifications,
            'count': len(recent_classifications)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@classification_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files"""
    try:
        from flask import send_from_directory
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=False
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404
