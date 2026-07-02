#!/usr/bin/env python3
"""
TikTok Bot - Versão Web Online
Otimizado para deploy em Render/Railway
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from datetime import datetime

# Configuração
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tiktok-bot-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tiktok_bot.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================
# MODELOS
# ============================================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    type = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================
# ROTAS
# ============================================
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
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não conferem!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Usuário já existe!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============================================
# API
# ============================================
@app.route('/api/user/info')
@login_required
def api_user_info():
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'config': {
            'posts_per_day': current_user.posts_per_day,
            'preferred_topic': current_user.preferred_topic,
            'video_duration': current_user.video_duration
        }
    })

@app.route('/api/stats')
@login_required
def api_stats():
    today = datetime.utcnow().date()
    total = Video.query.filter_by(user_id=current_user.id).count()
    queued = Video.query.filter_by(user_id=current_user.id, status='queued').count()
    posted = Video.query.filter_by(user_id=current_user.id, status='posted').count()
    today_count = Video.query.filter(
        Video.user_id == current_user.id,
        db.func.date(Video.created_at) == today
    ).count()
    
    return jsonify({
        'total_videos': total,
        'videos_queued': queued,
        'videos_posted': posted,
        'videos_today': today_count,
        'posts_per_day': current_user.posts_per_day,
        'is_running': False
    })

@app.route('/api/videos')
@login_required
def api_videos():
    status = request.args.get('status', 'all')
    query = Video.query.filter_by(user_id=current_user.id)
    
    if status != 'all':
        query = query.filter_by(status=status)
    
    videos = query.order_by(Video.created_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': v.id,
        'title': v.title,
        'topic': v.topic,
        'category': v.category,
        'status': v.status,
        'created_at': v.created_at.isoformat() if v.created_at else None,
        'processed_at': v.processed_at.isoformat() if v.processed_at else None
    } for v in videos])

@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    topics = {
        "motivação": ["Dicas de motivação", "Como manter o foco", "Histórias de superação"],
        "tecnologia": ["Novidades tech", "Dicas de programação", "Fatos surpreendentes"],
        "dicas": ["Dicas de produtividade", "Truques diários", "Life hacks"],
        "humor": ["Situações engraçadas", "Memes do momento", "Comédia"],
        "curiosidades": ["Fatos surpreendentes", "Você sabia?", "Curiosidades"]
    }
    
    data = request.json or {}
    topic_pref = data.get('topic', current_user.preferred_topic)
    
    if topic_pref == 'auto' or topic_pref not in topics:
        category = random.choice(list(topics.keys()))
    else:
        category = topic_pref
    
    topic = random.choice(topics[category])
    title = f"🔥 {topic} - Você Não Vai Acreditar!"
    script = f"Conteúdo incrível sobre {topic.lower()}! Assista até o final para descobrir tudo!"
    description = f"Gostou? Deixa o like! 🔥 #fyp #viral #tiktok #{category}"
    
    video = Video(
        user_id=current_user.id,
        title=title,
        topic=topic,
        category=category,
        script=script,
        description=description,
        video_path=f"output/video_{random.randint(1000,9999)}.txt",
        status='queued'
    )
    db.session.add(video)
    
    log = Log(user_id=current_user.id, message=f"Vídeo gerado: {title}", type='success')
    db.session.add(log)
    db.session.commit()
    
    return jsonify({
        'status': 'ok',
        'video': {
            'id': video.id,
            'title': title,
            'topic': topic,
            'category': category,
            'description': description
        }
    })

@app.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    data = request.json or {}
    
    if 'posts_per_day' in data:
        current_user.posts_per_day = int(data['posts_per_day'])
    if 'preferred_topic' in data:
        current_user.preferred_topic = data['preferred_topic']
    if 'video_duration' in data:
        current_user.video_duration = int(data['video_duration'])
    
    db.session.commit()
    return jsonify({'status': 'ok'})

@app.route('/api/logs')
@login_required
def api_logs():
    logs = Log.query.filter_by(user_id=current_user.id)\
                   .order_by(Log.created_at.desc())\
                   .limit(50).all()
    
    return jsonify([{
        'message': l.message,
        'type': l.type,
        'created_at': l.created_at.isoformat()
    } for l in logs])

# ============================================
# INICIALIZAÇÃO
# ============================================
def init_db():
    with app.app_context():
        db.create_all()
        
        # Criar admin se não existir
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@tiktokbot.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado: admin / admin123")

# Inicializar banco
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
