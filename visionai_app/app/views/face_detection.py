from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import cv2
import numpy as np
import base64
import os
import uuid
import pickle
from datetime import datetime
from app.models.detection import Detection, db
from app.services.db_service import save_detection
from werkzeug.utils import secure_filename

face_detection_bp = Blueprint('face_detection', __name__, url_prefix='/face-detection')

# Global variables for face recognition
known_faces = {}
known_face_names = []

@face_detection_bp.route('/')
@login_required
def face_detection():
    return render_template('face_detection/index.html')

@face_detection_bp.route('/upload')
@login_required
def face_upload():
    return render_template('face_detection/upload.html')

@face_detection_bp.route('/camera')
@login_required
def face_camera():
    return render_template('face_detection/camera.html')

@face_detection_bp.route('/detect-upload', methods=['POST'])
@login_required
def detect_faces_upload():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Load known faces for recognition
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data_loaded = pickle.load(f)
                known_faces = data_loaded.get('faces', {})
                known_face_names = data_loaded.get('names', [])
        
        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Load face cascade classifier
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Process detected faces and recognize if possible
        face_data = []
        recognized_names = []
        confidence_scores = []
        
        for (x, y, w, h) in faces:
            face_info = {
                'box': [int(x), int(y), int(w), int(h)],  # Convert numpy int32 to Python int
                'confidence': 1.0,
                'name': 'Unknown'
            }
            
            # Try to recognize face
            face_roi = gray[y:y+h, x:x+w]
            name, confidence = recognize_face(face_roi)
            if name:
                face_info['name'] = name
                face_info['confidence'] = confidence
                recognized_names.append(name)
                confidence_scores.append(confidence)
            else:
                recognized_names.append('Unknown')
                confidence_scores.append(0.0)
            
            face_data.append(face_info)
        
        # Create annotated image
        annotated_img = draw_face_boxes(img, faces, recognized_names, confidence_scores)
        
        # Save original image
        filename = f'face_upload_{uuid.uuid4()}.jpg'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, img)
        
        # Save annotated image
        annotated_filename = f'annotated_{filename}'
        annotated_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_filepath, annotated_img)
        
        # Convert annotated image back to base64
        _, buffer = cv2.imencode('.jpg', annotated_img)
        annotated_image_data = base64.b64encode(buffer).decode('utf-8')
        
        # Save detection to Databricks via db_service
        detection = save_detection(
            detection_type='face_upload',
            objects_detected=face_data,
            confidence_scores=[face['confidence'] for face in face_data],
            image=img,
            image_prefix='face_upload',
            processing_time=0.0
        )
        detection_id = detection.id if detection else None
        
        return jsonify({
            'success': True,
            'faces': face_data,
            'face_count': len(face_data),
            'recognized_count': len([n for n in recognized_names if n != 'Unknown']),
            'annotated_image': f'data:image/jpeg;base64,{annotated_image_data}',
            'detection_id': detection_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@face_detection_bp.route('/detect-camera', methods=['POST'])
@login_required
def detect_faces_camera():
    try:
        print("DEBUG: Camera detection request received")
        data = request.get_json()
        image_data = data.get('image')
        
        print(f"DEBUG: Camera detection - has_image: {bool(image_data)}")
        
        if not image_data:
            print("DEBUG: No image data provided")
            return jsonify({'error': 'No image data provided'}), 400
        
        # Load known faces for recognition
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        print(f"DEBUG: Loading faces from {faces_file}")
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data_loaded = pickle.load(f)
                known_faces = data_loaded.get('faces', {})
                known_face_names = data_loaded.get('names', [])
                print(f"DEBUG: Loaded {len(known_faces)} known faces")
        
        # Decode base64 image
        print("DEBUG: Decoding base64 image")
        if ',' in image_data:
            image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        print("DEBUG: Converting to numpy array")
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("DEBUG: Failed to decode image")
            return jsonify({'error': 'Invalid image data'}), 400
        
        print(f"DEBUG: Image decoded successfully - shape: {img.shape}")
        
        # Load face cascade classifier
        print("DEBUG: Loading face cascade")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale for face detection
        print("DEBUG: Converting to grayscale")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        print("DEBUG: Detecting faces")
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        print(f"DEBUG: Found {len(faces)} faces")
        
        # Process detected faces and recognize if possible
        face_data = []
        recognized_names = []
        confidence_scores = []
        
        for (x, y, w, h) in faces:
            face_info = {
                'box': [int(x), int(y), int(w), int(h)],  # Convert numpy int32 to Python int
                'confidence': 1.0,
                'name': 'Unknown'
            }
            
            # Try to recognize face
            face_roi = gray[y:y+h, x:x+w]
            name, confidence = recognize_face(face_roi)
            if name:
                face_info['name'] = name
                face_info['confidence'] = confidence
                recognized_names.append(name)
                confidence_scores.append(confidence)
            else:
                recognized_names.append('Unknown')
                confidence_scores.append(0.0)
            
            face_data.append(face_info)
        
        print(f"DEBUG: Processed {len(face_data)} faces, recognized {len([n for n in recognized_names if n != 'Unknown'])}")
        
        # Create annotated image
        print("DEBUG: Creating annotated image")
        annotated_img = draw_face_boxes(img, faces, recognized_names, confidence_scores)
        
        # Save original image
        print("DEBUG: Saving original image")
        filename = f'face_camera_{uuid.uuid4()}.jpg'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, img)
        
        # Save annotated image
        print("DEBUG: Saving annotated image")
        annotated_filename = f'annotated_{filename}'
        annotated_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], annotated_filename)
        cv2.imwrite(annotated_filepath, annotated_img)
        
        # Convert annotated image back to base64
        print("DEBUG: Converting to base64")
        _, buffer = cv2.imencode('.jpg', annotated_img)
        annotated_image_data = base64.b64encode(buffer).decode('utf-8')
        
        # Save detection to Databricks via db_service
        detection = save_detection(
            detection_type='face_camera',
            objects_detected=face_data,
            confidence_scores=[face['confidence'] for face in face_data],
            image=img,
            image_prefix='face_camera',
            processing_time=0.0
        )
        detection_id = detection.id if detection else None
        
        print("[detect_faces_camera] Saved to DB | faces=%d | id=%s" % (len(face_data), detection_id))
        return jsonify({
            'success': True,
            'faces': face_data,
            'face_count': len(face_data),
            'recognized_count': len([n for n in recognized_names if n != 'Unknown']),
            'annotated_image': f'data:image/jpeg;base64,{annotated_image_data}',
            'detection_id': detection_id
        })
        
    except Exception as e:
        print(f"DEBUG: Error in detect_faces_camera: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@face_detection_bp.route('/add-face', methods=['POST'])
def add_face():
    try:
        data = request.get_json()
        image_data = data.get('image')
        name = data.get('name', '').strip()
        
        print(f"DEBUG: Add face request - name: {name}, has_image: {bool(image_data)}")
        
        if not image_data:
            print("DEBUG: No image data provided")
            return jsonify({'error': 'No image data provided'}), 400
        
        if not name:
            print("DEBUG: No name provided")
            return jsonify({'error': 'Name is required'}), 400
        
        # Load existing faces first
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        print(f"DEBUG: Loading faces from {faces_file}")
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data_loaded = pickle.load(f)
                known_faces = data_loaded.get('faces', {})
                known_face_names = data_loaded.get('names', [])
                print(f"DEBUG: Loaded {len(known_faces)} known faces")
        
        # Check if name already exists
        if name in known_faces:
            print(f"DEBUG: Face {name} already exists")
            return jsonify({'error': f'Face "{name}" already exists'}), 400
        
        # Decode base64 image
        print("DEBUG: Decoding base64 image")
        if ',' in image_data:
            image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        print("DEBUG: Converting to numpy array")
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            print("DEBUG: Failed to decode image")
            return jsonify({'error': 'Invalid image data'}), 400
        
        print(f"DEBUG: Image decoded successfully - shape: {img.shape}")
        
        # Load face cascade classifier
        print("DEBUG: Loading face cascade")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Convert to grayscale for face detection
        print("DEBUG: Converting to grayscale")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        print("DEBUG: Detecting faces")
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        print(f"DEBUG: Found {len(faces)} faces")
        
        if len(faces) == 0:
            print("DEBUG: No faces detected")
            return jsonify({'error': 'No face detected in the image'}), 400
        
        # Select the largest face (usually the clearest)
        largest_face_idx = 0
        max_area = 0
        for i, (x, y, w, h) in enumerate(faces):
            area = w * h
            if area > max_area:
                max_area = area
                largest_face_idx = i
        
        print(f"DEBUG: Selected face {largest_face_idx + 1} (largest) from {len(faces)} faces")
        
        # Extract face features from the largest face
        x, y, w, h = faces[largest_face_idx]
        print("DEBUG: Extracting face features")
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize face to standard size
        print("DEBUG: Resizing face")
        face_roi = cv2.resize(face_roi, (100, 100))
        
        # Add to known faces
        print("DEBUG: Adding face to database")
        known_faces[name] = face_roi
        known_face_names.append(name)
        
        # Save face data
        print("DEBUG: Saving face data")
        save_known_faces()
        
        # Save the face image
        print("DEBUG: Saving face image")
        filename = f'known_face_{name}_{uuid.uuid4()}.jpg'
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        cv2.imwrite(filepath, img)
        
        print(f"DEBUG: Face {name} added successfully")
        return jsonify({
            'success': True,
            'message': f'Face "{name}" has been added successfully',
            'name': name,
            'total_faces': len(known_faces),
            'faces_detected': len(faces),
            'selected_face': largest_face_idx + 1
        })
        
    except Exception as e:
        print(f"DEBUG: Error in add_face: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@face_detection_bp.route('/get-known-faces', methods=['GET'])
@login_required
def get_known_faces():
    try:
        # Load known faces in application context
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data = pickle.load(f)
                known_faces = data.get('faces', {})
                known_face_names = data.get('names', [])
        else:
            known_faces = {}
            known_face_names = []
        
        return jsonify({
            'success': True,
            'faces': list(known_faces.keys()),
            'total_faces': len(known_faces)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@face_detection_bp.route('/remove-face', methods=['POST'])
@login_required
def remove_face():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        # Load existing faces first
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data_loaded = pickle.load(f)
                known_faces = data_loaded.get('faces', {})
                known_face_names = data_loaded.get('names', [])
        
        if name in known_faces:
            del known_faces[name]
            known_face_names = [n for n in known_face_names if n != name]
            save_known_faces()
            
            return jsonify({
                'success': True,
                'message': f'Face "{name}" has been removed successfully',
                'total_faces': len(known_faces)
            })
        else:
            return jsonify({'error': 'Face not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def recognize_face(face_roi):
    """Recognize face using simple template matching"""
    global known_faces, known_face_names
    
    # Load known faces if empty
    if len(known_faces) == 0:
        try:
            faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
            if os.path.exists(faces_file):
                with open(faces_file, 'rb') as f:
                    data_loaded = pickle.load(f)
                    known_faces = data_loaded.get('faces', {})
                    known_face_names = data_loaded.get('names', [])
        except Exception as e:
            print(f"Error loading known faces for recognition: {e}")
            return None, 0.0
    
    if len(known_faces) == 0:
        return None, 0.0
    
    # Resize face to standard size
    face_roi = cv2.resize(face_roi, (100, 100))
    
    best_match = None
    best_score = float('inf')
    best_confidence = 0.0
    
    for name, known_face in known_faces.items():
        # Calculate similarity using normalized correlation
        result = cv2.matchTemplate(face_roi, known_face, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        
        # Use 1 - max_val as distance (lower is better)
        distance = 1 - max_val
        confidence = max_val  # Higher is better for confidence
        
        if distance < best_score and distance < 0.3:  # Threshold for recognition
            best_score = distance
            best_match = name
            best_confidence = confidence
    
    return best_match, best_confidence

def draw_face_boxes(img, faces, recognized_names=None, confidence_scores=None):
    """Draw bounding boxes around detected faces with names and confidence"""
    annotated_img = img.copy()
    
    # Add title
    cv2.putText(annotated_img, "Face Detection Results", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Draw face count
    face_count_text = f"Faces detected: {len(faces)}"
    cv2.putText(annotated_img, face_count_text, (10, 60), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    if recognized_names:
        recognized_text = f"Recognized: {len(recognized_names)}"
        cv2.putText(annotated_img, recognized_text, (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Draw bounding boxes for each face
    for i, (x, y, w, h) in enumerate(faces):
        # Choose color based on recognition
        if recognized_names and i < len(recognized_names) and recognized_names[i] != "Unknown":
            color = (0, 255, 0)  # Green for recognized
            status = "Recognized"
        else:
            color = (0, 0, 255)  # Red for unknown
            status = "Unknown"
        
        # Draw rectangle around face
        cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
        
        # Create label with name and confidence
        if recognized_names and i < len(recognized_names):
            name = recognized_names[i]
            if confidence_scores and i < len(confidence_scores):
                confidence = confidence_scores[i]
                label = f"{name} ({confidence:.1%})"
            else:
                label = name
        else:
            label = f"Face {i + 1}"
        
        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(annotated_img, 
                     (x, y - 30), 
                     (x + label_size[0] + 10, y), 
                     color, -1)
        
        # Draw label text
        cv2.putText(annotated_img, label, 
                   (x + 5, y - 8), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add status text below face
        status_text = status
        cv2.putText(annotated_img, status_text, 
                   (x, y + h + 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        # Add face dimensions
        face_info = f"{w}x{h}px"
        cv2.putText(annotated_img, face_info, 
                   (x, y + h + 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    
    return annotated_img

def save_known_faces():
    """Save known faces to file"""
    try:
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        with open(faces_file, 'wb') as f:
            pickle.dump({'faces': known_faces, 'names': known_face_names}, f)
    except Exception as e:
        print(f"Error saving known faces: {e}")

def load_known_faces():
    """Load known faces from file"""
    try:
        global known_faces, known_face_names
        faces_file = os.path.join(current_app.config['UPLOAD_FOLDER'], 'known_faces.pkl')
        if os.path.exists(faces_file):
            with open(faces_file, 'rb') as f:
                data = pickle.load(f)
                known_faces = data.get('faces', {})
                known_face_names = data.get('names', [])
    except Exception as e:
        print(f"Error loading known faces: {e}")
        known_faces = {}
        known_face_names = []

@face_detection_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))

# Initialize known faces data
def init_known_faces():
    """Initialize known faces when app starts"""
    global known_faces, known_face_names
    known_faces = {}
    known_face_names = []
