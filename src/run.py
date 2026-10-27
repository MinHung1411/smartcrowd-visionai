import os
import threading
import webbrowser
from app import create_app, db
from app.models.user import User

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    is_cloud = os.environ.get('RENDER') or os.environ.get('PORT')
    
    # Chỉ tự động mở trình duyệt khi chạy local
    if not is_cloud and not os.environ.get('WERKZEUG_RUN_MAIN'):
        threading.Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
        
    app.run(debug=not is_cloud, host='0.0.0.0', port=port)
