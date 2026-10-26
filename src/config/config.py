import os
from datetime import timedelta
from dotenv import load_dotenv

# Load .env file trước khi đọc biến môi trường
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    # Databricks Unity Catalog connection (required - set DATABASE_URL in .env)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is not set. Please configure it in .env file.")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Engine options for Databricks (higher timeout for cloud connection)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'connect_args': {
            '_socket_timeout': 60,
        }
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # YOLO model settings
    YOLO_MODEL_PATH = os.environ.get('YOLO_MODEL_PATH') or 'yolov8n.pt'
    
    # Bilingual labels
    OBJECT_LABELS = {
        'person': {'en': 'person', 'vi': 'Người'},
        'bicycle': {'en': 'bicycle', 'vi': 'Xe đạp'},
        'car': {'en': 'car', 'vi': 'Ô tô'},
        'motorcycle': {'en': 'motorcycle', 'vi': 'Xe máy'},
        'airplane': {'en': 'airplane', 'vi': 'Máy bay'},
        'bus': {'en': 'bus', 'vi': 'Xe buýt'},
        'train': {'en': 'train', 'vi': 'Tàu hỏa'},
        'truck': {'en': 'truck', 'vi': 'Xe tải'},
        'boat': {'en': 'boat', 'vi': 'Thuyền'},
        'traffic light': {'en': 'traffic light', 'vi': 'Đèn giao thông'},
        'fire hydrant': {'en': 'fire hydrant', 'vi': 'Vòi cứu hỏa'},
        'stop sign': {'en': 'stop sign', 'vi': 'Biển báo dừng'},
        'parking meter': {'en': 'parking meter', 'vi': 'Máy đỗ xe'},
        'bench': {'en': 'bench', 'vi': 'Ghế dài'},
        'bird': {'en': 'bird', 'vi': 'Chim'},
        'cat': {'en': 'cat', 'vi': 'Mèo'},
        'dog': {'en': 'dog', 'vi': 'Chó'},
        'horse': {'en': 'horse', 'vi': 'Ngựa'},
        'sheep': {'en': 'sheep', 'vi': 'Cừu'},
        'cow': {'en': 'cow', 'vi': 'Bò'},
        'elephant': {'en': 'elephant', 'vi': 'Voi'},
        'bear': {'en': 'bear', 'vi': 'Gấu'},
        'zebra': {'en': 'zebra', 'vi': 'Ngựa vằn'},
        'giraffe': {'en': 'giraffe', 'vi': 'Hươu cao cổ'},
        'backpack': {'en': 'backpack', 'vi': 'Balo'},
        'umbrella': {'en': 'umbrella', 'vi': 'Ô'},
        'handbag': {'en': 'handbag', 'vi': 'Túi xách'},
        'tie': {'en': 'tie', 'vi': 'Cà vạt'},
        'suitcase': {'en': 'suitcase', 'vi': 'Vali'},
        'frisbee': {'en': 'frisbee', 'vi': 'Đĩa bay'},
        'skis': {'en': 'skis', 'vi': 'Trượt tuyết'},
        'snowboard': {'en': 'snowboard', 'vi': 'Ván trượt tuyết'},
        'sports ball': {'en': 'sports ball', 'vi': 'Bóng thể thao'},
        'kite': {'en': 'kite', 'vi': 'Diều'},
        'baseball bat': {'en': 'baseball bat', 'vi': 'Gậy bóng chày'},
        'baseball glove': {'en': 'baseball glove', 'vi': 'Găng tay bóng chày'},
        'skateboard': {'en': 'skateboard', 'vi': 'Ván trượt'},
        'surfboard': {'en': 'surfboard', 'vi': 'Ván lướt sóng'},
        'tennis racket': {'en': 'tennis racket', 'vi': 'Vợt tennis'},
        'bottle': {'en': 'bottle', 'vi': 'Chai'},
        'wine glass': {'en': 'wine glass', 'vi': 'Ly rượu'},
        'cup': {'en': 'cup', 'vi': 'Cốc'},
        'fork': {'en': 'fork', 'vi': 'Nĩa'},
        'knife': {'en': 'knife', 'vi': 'Dao'},
        'spoon': {'en': 'spoon', 'vi': 'Thìa'},
        'bowl': {'en': 'bowl', 'vi': 'Tô'},
        'banana': {'en': 'banana', 'vi': 'Chuối'},
        'apple': {'en': 'apple', 'vi': 'Táo'},
        'sandwich': {'en': 'sandwich', 'vi': 'Bánh sandwich'},
        'orange': {'en': 'orange', 'vi': 'Cam'},
        'broccoli': {'en': 'broccoli', 'vi': 'Súp lơ'},
        'carrot': {'en': 'carrot', 'vi': 'Cà rốt'},
        'hot dog': {'en': 'hot dog', 'vi': 'Xúc xích'},
        'pizza': {'en': 'pizza', 'vi': 'Pizza'},
        'donut': {'en': 'donut', 'vi': 'Bánh rán'},
        'cake': {'en': 'cake', 'vi': 'Bánh ngọt'},
        'chair': {'en': 'chair', 'vi': 'Cái ghế'},
        'couch': {'en': 'couch', 'vi': 'Sô pha'},
        'potted plant': {'en': 'potted plant', 'vi': 'Cây cảnh'},
        'bed': {'en': 'bed', 'vi': 'Giường'},
        'dining table': {'en': 'dining table', 'vi': 'Bàn ăn'},
        'toilet': {'en': 'toilet', 'vi': 'Nhà vệ sinh'},
        'tv': {'en': 'tv', 'vi': 'Tivi'},
        'laptop': {'en': 'laptop', 'vi': 'Máy tính xách tay'},
        'mouse': {'en': 'mouse', 'vi': 'Chuột máy tính'},
        'remote': {'en': 'remote', 'vi': 'Điều khiển'},
        'keyboard': {'en': 'keyboard', 'vi': 'Bàn phím'},
        'cell phone': {'en': 'cell phone', 'vi': 'Điện thoại'},
        'microwave': {'en': 'microwave', 'vi': 'Lò vi sóng'},
        'oven': {'en': 'oven', 'vi': 'Lò nướng'},
        'toaster': {'en': 'toaster', 'vi': 'Máy nướng bánh'},
        'sink': {'en': 'sink', 'vi': 'Bồn rửa'},
        'refrigerator': {'en': 'refrigerator', 'vi': 'Tủ lạnh'},
        'book': {'en': 'book', 'vi': 'Sách'},
        'clock': {'en': 'clock', 'vi': 'Đồng hồ'},
        'vase': {'en': 'vase', 'vi': 'Bình hoa'},
        'scissors': {'en': 'scissors', 'vi': 'Kéo'},
        'teddy bear': {'en': 'teddy bear', 'vi': 'Gấu bông'},
        'hair drier': {'en': 'hair drier', 'vi': 'Máy sấy tóc'},
        'toothbrush': {'en': 'toothbrush', 'vi': 'Bàn chải đánh răng'}
    }
