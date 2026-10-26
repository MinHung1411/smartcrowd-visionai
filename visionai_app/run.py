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
    # Tự động mở trình duyệt web sau 1.5s
    # Kiểm tra WERKZEUG_RUN_MAIN để tránh mở nhiều tab khi Flask tự động reload (debug=True)
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5000')).start()
        
    app.run(debug=True, host='0.0.0.0', port=5000)
