from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
import cv2
import numpy as np
import base64
import os
import uuid
from datetime import datetime
from app.models.detection import Detection, db
from app.services.db_service import save_detection
from werkzeug.utils import secure_filename

color_detection_bp = Blueprint('color_detection', __name__, url_prefix='/color-detection')

@color_detection_bp.route('/')
@login_required
def color_detection():
    return render_template('color_detection/index.html')

@color_detection_bp.route('/detect', methods=['POST'])
@login_required
def detect_colors():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Resize image for better processing
        height, width = img.shape[:2]
        if max(height, width) > 800:
            scale = 800 / max(height, width)
            img = cv2.resize(img, (int(width * scale), int(height * scale)))
        
        # Detect colors
        colors = detect_dominant_colors(img)
        
        # Create annotated image
        annotated_img = draw_color_palette(img, colors)
        
        # Save original image
        filename = f'color_{uuid.uuid4()}.jpg'
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
            detection_type='color',
            objects_detected=colors,
            confidence_scores=[color['percentage'] for color in colors],
            image=img,
            image_prefix='color',
            processing_time=0.0
        )
        detection_id = detection.id if detection else None
        
        return jsonify({
            'success': True,
            'colors': colors,
            'annotated_image': f'data:image/jpeg;base64,{annotated_image_data}',
            'detection_id': detection_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def detect_dominant_colors(img, k=5):
    """Detect dominant colors using K-means clustering"""
    # Reshape image to be a list of pixels
    pixels = img.reshape(-1, 3)
    
    # Convert to float32
    pixels = np.float32(pixels)
    
    # Define criteria and apply K-means
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # Convert back to uint8
    centers = np.uint8(centers)
    
    # Calculate percentages
    total_pixels = len(pixels)
    color_counts = {}
    
    for label in labels.flatten():
        if label not in color_counts:
            color_counts[label] = 0
        color_counts[label] += 1
    
    # Format results
    colors = []
    for i, center in enumerate(centers):
        if i in color_counts:
            b, g, r = center
            percentage = (color_counts[i] / total_pixels) * 100
            
            # Convert RGB to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            
            # Get color name
            color_name = get_color_name(r, g, b)
            
            colors.append({
                'rgb': [int(r), int(g), int(b)],
                'hex': hex_color,
                'name': color_name,
                'percentage': min(100.0, round(percentage, 2))  # Cap at 100%
            })
    
    # Sort by percentage
    colors.sort(key=lambda x: x['percentage'], reverse=True)
    
    return colors

def get_color_name(r, g, b):
    """Get color name from RGB values - Enhanced version"""
    # Calculate color intensity and differences
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val
    
    # Grayscale detection
    if diff < 30:
        if max_val > 200:
            return "White"
        elif max_val > 150:
            return "Light Gray"
        elif max_val > 80:
            return "Gray"
        else:
            return "Dark Gray"
    
    # Dominant color detection with better ranges
    if r > g and r > b:
        # Red dominant
        if g > 150 and b > 150:
            return "Pink"
        elif g > 100 and b < 100:
            return "Orange"
        elif g < 100 and b > 100:
            return "Purple"
        elif g > 100 and b > 100:
            return "Brown"
        else:
            return "Red"
    
    elif g > r and g > b:
        # Green dominant
        if r > 150 and b < 100:
            return "Yellow-Green"
        elif r < 100 and b > 150:
            return "Cyan"
        elif r > 100 and b < 100:
            return "Lime"
        elif r > 100 and b > 100:
            return "Olive"
        else:
            return "Green"
    
    elif b > r and b > g:
        # Blue dominant
        if r > 150 and g < 100:
            return "Violet"
        elif r > 150 and g > 150:
            return "Light Blue"
        elif r < 100 and g > 100:
            return "Teal"
        elif r > 100 and g > 100:
            return "Navy"
        else:
            return "Blue"
    
    # If no clear dominant, use weighted average
    total = r + g + b
    r_ratio = r / total
    g_ratio = g / total
    b_ratio = b / total
    
    if r_ratio > 0.4:
        if g_ratio > 0.3:
            return "Yellow-Orange"
        elif b_ratio > 0.3:
            return "Purple-Red"
        else:
            return "Red"
    elif g_ratio > 0.4:
        if r_ratio > 0.3:
            return "Yellow-Green"
        elif b_ratio > 0.3:
            return "Cyan"
        else:
            return "Green"
    elif b_ratio > 0.4:
        if r_ratio > 0.3:
            return "Purple-Blue"
        elif g_ratio > 0.3:
            return "Teal"
        else:
            return "Blue"
    
    # Final fallback with more specific options
    if r > g and r > b:
        return "Reddish"
    elif g > r and g > b:
        return "Greenish"
    else:
        return "Bluish"

def draw_color_palette(img, colors):
    """Draw color palette on image"""
    annotated_img = img.copy()
    height, width = annotated_img.shape[:2]
    
    # Create palette area at bottom
    palette_height = 100
    palette_y = height - palette_height
    
    # Draw black background for palette
    cv2.rectangle(annotated_img, (0, palette_y), (width, height), (0, 0, 0), -1)
    
    # Draw color swatches
    swatch_width = width // len(colors)
    
    for i, color in enumerate(colors):
        x1 = i * swatch_width
        x2 = (i + 1) * swatch_width
        
        # Draw color swatch
        rgb = color['rgb']
        cv2.rectangle(annotated_img, (x1, palette_y), (x2, height), rgb, -1)
        
        # Draw color name and percentage
        text = f"{color['name']}: {color['percentage']}%"
        text_y = palette_y + 30
        
        # Choose text color based on background
        text_color = (255, 255, 255) if sum(rgb) < 400 else (0, 0, 0)
        
        cv2.putText(annotated_img, text, (x1 + 10, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)
        
        # Draw hex code
        hex_text = color['hex']
        cv2.putText(annotated_img, hex_text, (x1 + 10, text_y + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1)
    
    # Add title
    cv2.putText(annotated_img, "Color Detection Results", (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return annotated_img

@color_detection_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_file(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
