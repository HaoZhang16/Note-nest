from flask import Flask
from config import SECRET_KEY, UPLOAD_FOLDER
from routes.home import home_bp
from routes.auth import auth_bp
from routes.book import book_bp
from routes.note import note_bp
from routes.review import review_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 注册蓝图
app.register_blueprint(home_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(book_bp)
app.register_blueprint(note_bp)
app.register_blueprint(review_bp)

if __name__ == "__main__":
    app.run(debug=True)
