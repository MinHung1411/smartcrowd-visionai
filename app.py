import os
import sys

# Thêm đường dẫn src/ vào sys.path để nạp app, views, models
sys.path.insert(0, os.path.abspath('src'))
from run import app

if __name__ == '__main__':
    # Hugging Face Spaces mặc định điều hướng tới cổng 7860
    port = int(os.environ.get('PORT', 7860))
    print("==================================================")
    print(f"  SmartCrowd VisionAI - Flask Full-Stack Platform")
    print(f"  Running on port {port} with 16GB RAM capability")
    print("==================================================")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
