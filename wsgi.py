import sys
import os

# Thêm src vào đường dẫn hệ thống
sys.path.insert(0, os.path.abspath('src'))
from run import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
