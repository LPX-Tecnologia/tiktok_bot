import os
os.system("pip install flask flask-cors flask-login flask-sqlalchemy")

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import random
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave-secreta-tiktok-bot'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tiktok_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modelos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    posts_per_day = db.Column(db.Integer, default=3)
    preferred_topic = db.Column(db.String(50), default='auto')
    video_duration = db.Column(db.Integer, default=60)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    topic = db.Column(db.String(100))
    category = db.Column(db.String(50))
    script = db.Column(db.Text)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(300))
    status = db.Column(db.String(20), default='queued')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rotas
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error='Usuário ou senha incorretos!')
    
    return render_template_string(LOGIN_HTML)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            return render_template_string(REGISTER_HTML, error='Usuário já existe!')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return redirect(url_for('login'))
    
    return render_template_string(REGISTER_HTML)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    topics = {
        "motivação": ["Dicas de motivação", "Como manter o foco"],
        "tecnologia": ["Novidades tech", "Dicas de programação"],
        "dicas": ["Dicas de produtividade", "Truques diários"],
    }
    
    topic = random.choice(list(topics.keys()))
    title = f"🔥 {random.choice(topics[topic])}"
    script = f"Conteúdo sobre {topic}... Assista até o final!"
    description = f"Gostou? Deixa o like! #fyp #viral #{topic}"
    
    video = Video(
        user_id=current_user.id,
        title=title,
        topic=topic,
        category=topic,
        script=script,
        description=description,
        video_path=f"output/video_{random.randint(1000,9999)}.txt",
        status='queued'
    )
    db.session.add(video)
    db.session.commit()
    
    return jsonify({'status': 'ok', 'video': {'title': title, 'topic': topic}})

@app.route('/api/stats')
@login_required
def api_stats():
    total = Video.query.filter_by(user_id=current_user.id).count()
    queued = Video.query.filter_by(user_id=current_user.id, status='queued').count()
    
    return jsonify({
        'total_videos': total,
        'videos_queued': queued,
        'videos_today': 0,
        'videos_posted': 0,
        'posts_per_day': current_user.posts_per_day,
        'is_running': False
    })

# HTML Templates
LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Bot - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-box {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
        }
        h1 { color: white; text-align: center; margin-bottom: 30px; }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            color: white;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #ff0050;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            margin-top: 20px;
        }
        button:hover { background: #ff1a62; }
        .error { color: #ff4444; text-align: center; margin: 10px 0; }
        a { color: #00f2ea; text-align: center; display: block; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🤖 TikTok Bot</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit">🚀 Entrar</button>
        </form>
        <a href="/register">Criar conta</a>
        <p style="color: white; text-align: center; margin-top: 20px; font-size: 0.9em;">
            Demo: admin / admin123
        </p>
    </div>
</body>
</html>
'''

REGISTER_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Bot - Registro</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea, #764ba2);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .register-box {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            width: 90%;
            max-width: 400px;
        }
        h1 { color: white; text-align: center; margin-bottom: 30px; }
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            color: white;
        }
        button {
            width: 100%;
            padding: 14px;
            background: #00f2ea;
            color: black;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            cursor: pointer;
            margin-top: 20px;
        }
        .error { color: #ff4444; text-align: center; margin: 10px 0; }
        a { color: #ff0050; text-align: center; display: block; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="register-box">
        <h1>✨ Criar Conta</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="Usuário" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="password" name="password" placeholder="Senha" required>
            <button type="submit">Criar Conta</button>
        </form>
        <a href="/login">Já tenho conta</a>
    </div>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Bot - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: #0f0f0f;
            color: white;
        }
        .navbar {
            background: linear-gradient(135deg, #ff0050, #00f2ea);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .card {
            background: #1a1a1a;
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            margin: 5px;
            color: white;
            font-weight: bold;
        }
        .btn-generate { background: #ff0050; }
        .btn-logout { background: rgba(255,255,255,0.2); }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #1a1a1a;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            background: linear-gradient(135deg, #ff0050, #00f2ea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <span style="font-size: 1.5em; font-weight: bold;">🤖 TikTok Bot</span>
        <button class="btn btn-logout" onclick="logout()">🚪 Sair</button>
    </nav>
    
    <div class="container">
        <h2>Bem-vindo, {{ current_user.username }}!</h2>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="totalVideos">0</div>
                <div>Total de Vídeos</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="queuedVideos">0</div>
                <div>Na Fila</div>
            </div>
        </div>
        
        <div class="card">
            <h3>🎮 Controles</h3>
            <button class="btn btn-generate" onclick="generateVideo()">🎬 Gerar Vídeo</button>
        </div>
        
        <div class="card" id="lastVideo" style="display:none;">
            <h3>✅ Último Vídeo Gerado</h3>
            <p id="videoTitle"></p>
            <p id="videoTopic"></p>
        </div>
    </div>
    
    <script>
        function generateVideo() {
            fetch('/api/generate', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    document.getElementById('lastVideo').style.display = 'block';
                    document.getElementById('videoTitle').textContent = '📝 ' + data.video.title;
                    document.getElementById('videoTopic').textContent = '🏷️ ' + data.video.topic;
                    updateStats();
                });
        }
        
        function updateStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalVideos').textContent = data.total_videos;
                    document.getElementById('queuedVideos').textContent = data.videos_queued;
                });
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        updateStats();
        setInterval(updateStats, 5000);
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@tiktokbot.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
