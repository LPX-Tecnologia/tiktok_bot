#!/usr/bin/env python3
"""
TikTok Bot - Sistema Web Completo
Com autenticação, banco de dados e painel de controle
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import json
import random
import threading
import time
from datetime import datetime, timedelta

# ============================================
# CONFIGURAÇÃO DO APP
# ============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tiktok_bot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============================================
# MODELOS DO BANCO DE DADOS
# ============================================

class User(UserMixin, db.Model):
    """Tabela de usuários"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Configurações do usuário
    posts_per_day = db.Column(db.Integer, default=3)
    preferred_topic = db.Column(db.String(50), default='auto')
    video_duration = db.Column(db.Integer, default=60)
    
    # Relacionamentos
    videos = db.relationship('Video', backref='author', lazy=True)
    logs = db.relationship('Log', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_config(self):
        return {
            'posts_per_day': self.posts_per_day,
            'preferred_topic': self.preferred_topic,
            'video_duration': self.video_duration
        }

class Video(db.Model):
    """Tabela de vídeos gerados"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    topic = db.Column(db.String(100))
    category = db.Column(db.String(50))
    script = db.Column(db.Text)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(300))
    status = db.Column(db.String(20), default='queued')  # queued, processing, posted, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'topic': self.topic,
            'category': self.category,
            'script': self.script,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class Log(db.Model):
    """Tabela de logs"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text)
    type = db.Column(db.String(20))  # info, success, error, warning
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# CONFIGURAÇÕES DO SISTEMA
# ============================================
class SystemConfig:
    OUTPUT_DIR = "output"
    TOPICS = {
        "motivação": [
            "Dicas de motivação diária",
            "Como manter o foco nos objetivos",
            "Histórias de superação",
            "Mindset de sucesso",
            "Hábitos matinais"
        ],
        "tecnologia": [
            "Novidades em tecnologia",
            "Dicas de programação",
            "Fatos tech surpreendentes",
            "Inteligência Artificial",
            "Futuro da tecnologia"
        ],
        "dicas": [
            "Dicas de produtividade",
            "Truques para o dia a dia",
            "Life hacks úteis",
            "Organização pessoal",
            "Dicas de estudo"
        ],
        "humor": [
            "Situações engraçadas",
            "Memes do momento",
            "Comédia cotidiana",
            "Fails engraçados",
            "Humor corporativo"
        ],
        "curiosidades": [
            "Fatos surpreendentes",
            "Você sabia?",
            "Curiosidades do mundo",
            "Recordes mundiais",
            "Histórias incríveis"
        ]
    }

os.makedirs(SystemConfig.OUTPUT_DIR, exist_ok=True)

# ============================================
# FUNÇÕES AUXILIARES
# ============================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def add_log(user_id, message, log_type='info'):
    """Adiciona log ao banco de dados"""
    log = Log(user_id=user_id, message=message, type=log_type)
    db.session.add(log)
    db.session.commit()

def generate_content(topic_preference="auto", duration=60):
    """Gera conteúdo para um vídeo"""
    
    if topic_preference == "auto" or topic_preference not in SystemConfig.TOPICS:
        category = random.choice(list(SystemConfig.TOPICS.keys()))
    else:
        category = topic_preference
    
    topic = random.choice(SystemConfig.TOPICS[category])
    
    # Títulos virais
    titles = [
        f"🔥 {topic.upper()} - Você Não Vai Acreditar!",
        f"😱 O SEGREDO sobre {topic}",
        f"✨ {topic}: O Guia DEFINITIVO",
        f"💡 {topic} - Isso Muda Tudo!",
        f"🚀 {topic} - Assista Até o Final!",
        f"🎯 {topic} - Dica RÁPIDA que Funciona!"
    ]
    
    # Scripts para narração
    scripts = [
        f"Você sabia que {topic.lower()} pode transformar seu dia? "
        f"Hoje vou te mostrar como isso funciona na prática. "
        f"Presta atenção nessa dica porque vai fazer toda diferença. "
        f"Compartilha com alguém que precisa ver isso! "
        f"Não esquece de curtir e seguir para mais conteúdos! 🔥",
        
        f"Atenção para essa informação sobre {topic.lower()}! "
        f"Isso é algo que muita gente não conhece mas deveria. "
        f"Fica comigo até o final que você vai se surpreender. "
        f"Já vai deixando o like e compartilhando! ✨",
        
        f"Olha só que incrível: {topic.lower()}! "
        f"Eu também não acreditava até descobrir isso. "
        f"Vou te explicar tim-tim por tim-tim. "
        f"Salva esse vídeo para não esquecer! 💾",
        
        f"Para tudo que eu vou te contar sobre {topic.lower()}! "
        f"Isso vai mudar completamente sua visão. "
        f"Presta muita atenção nos detalhes. "
        f"Depois me conta nos comentários o que achou! 💬"
    ]
    
    # Descrições com hashtags
    descriptions = [
        f"Gostou dessa dica sobre {topic}? "
        f"Deixa o like e compartilha! 🔥 "
        f"#fyp #viral #tiktok #brasil #{category} #dicas",
        
        f"Incrível né? {topic} é realmente fascinante! "
        f"Me conta nos comentários o que você achou! 💬 "
        f"#fyp #viral #{category} #aprenda #tiktok",
        
        f"Quer mais dicas como essa? Me segue! 🚀 "
        f"#fyp #viral #tiktok #{category} #dicas #conhecimento",
        
        f"Essa é daquelas dicas que todo mundo deveria saber! 💡 "
        f"Compartilha com os amigos! #fyp #{category} #viral"
    ]
    
    content = {
        'topic': topic,
        'category': category,
        'title': random.choice(titles),
        'script': random.choice(scripts),
        'description': random.choice(descriptions),
        'duration': duration,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Gerar arquivo do vídeo (placeholder)
    video_id = f"tiktok_{random.randint(10000, 99999)}_{int(time.time())}"
    video_path = f"{SystemConfig.OUTPUT_DIR}/{video_id}.txt"
    
    with open(video_path, 'w', encoding='utf-8') as f:
        f.write(f"VÍDEO GERADO PELO TIKTOK BOT\n")
        f.write(f"{'='*50}\n")
        f.write(f"Título: {content['title']}\n")
        f.write(f"Tópico: {content['topic']}\n")
        f.write(f"Categoria: {content['category']}\n")
        f.write(f"Duração: {content['duration']} segundos\n")
        f.write(f"Data: {content['timestamp']}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"SCRIPT PARA NARRAÇÃO:\n")
        f.write(f"{content['script']}\n\n")
        f.write(f"{'='*50}\n")
        f.write(f"DESCRIÇÃO PARA O POST:\n")
        f.write(f"{content['description']}\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"⚠️ Para gerar vídeos MP4 reais, instale:\n")
        f.write(f"   pip install moviepy Pillow gTTS\n")
    
    content['video_path'] = video_path
    content['video_id'] = video_id
    
    return content

# ============================================
# AGENDADOR GLOBAL
# ============================================
class GlobalScheduler:
    def __init__(self):
        self.is_running = False
        self.thread = None
    
    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
    
    def stop(self):
        self.is_running = False
    
    def _run(self):
        while self.is_running:
            with app.app_context():
                try:
                    now = datetime.utcnow()
                    
                    # Gerar posts às 6h
                    if now.hour == 6 and now.minute == 0:
                        users = User.query.filter_by(is_active=True).all()
                        for user in users:
                            for i in range(user.posts_per_day):
                                content = generate_content(user.preferred_topic, user.video_duration)
                                video = Video(
                                    user_id=user.id,
                                    title=content['title'],
                                    topic=content['topic'],
                                    category=content['category'],
                                    script=content['script'],
                                    description=content['description'],
                                    video_path=content['video_path'],
                                    status='queued'
                                )
                                db.session.add(video)
                                db.session.commit()
                                add_log(user.id, f"Vídeo gerado automaticamente: {content['title']}", 'success')
                    
                    # Processar fila nos horários
                    if now.hour in [8, 12, 16, 20] and now.minute == 0:
                        videos = Video.query.filter_by(status='queued').all()
                        for video in videos[:10]:  # Processar até 10 por vez
                            video.status = 'processing'
                            video.processed_at = datetime.utcnow()
                            db.session.commit()
                            add_log(video.user_id, f"Vídeo processado: {video.title}", 'info')
                            
                            # Simular postagem
                            time.sleep(1)
                            video.status = 'posted'
                            db.session.commit()
                            add_log(video.user_id, f"Vídeo postado com sucesso! ✅", 'success')
                    
                except Exception as e:
                    print(f"Erro no scheduler: {e}")
                
                time.sleep(30)

global_scheduler = GlobalScheduler()

# ============================================
# ROTAS DE AUTENTICAÇÃO
# ============================================

@app.route('/')
def index():
    """Redireciona para login ou dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            add_log(user.id, f"Login realizado com sucesso", 'info')
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validações
        if password != confirm_password:
            flash('As senhas não conferem!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('A senha deve ter no mínimo 6 caracteres!', 'error')
            return render_template('register.html')
        
        # Criar usuário
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        add_log(user.id, "Conta criada com sucesso!", 'success')
        flash('Conta criada com sucesso! Faça login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout do usuário"""
    add_log(current_user.id, "Logout realizado", 'info')
    logout_user()
    return redirect(url_for('login'))

# ============================================
# ROTAS DO PAINEL
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Painel principal"""
    return render_template('dashboard.html')

# ============================================
# API REST
# ============================================

@app.route('/api/user/info')
@login_required
def api_user_info():
    """Retorna informações do usuário"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email,
        'config': current_user.get_config(),
        'created_at': current_user.created_at.isoformat()
    })

@app.route('/api/stats')
@login_required
def api_stats():
    """Retorna estatísticas do usuário"""
    today = datetime.utcnow().date()
    
    total_videos = Video.query.filter_by(user_id=current_user.id).count()
    videos_today = Video.query.filter(
        Video.user_id == current_user.id,
        db.func.date(Video.created_at) == today
    ).count()
    videos_queued = Video.query.filter_by(user_id=current_user.id, status='queued').count()
    videos_posted = Video.query.filter_by(user_id=current_user.id, status='posted').count()
    
    return jsonify({
        'total_videos': total_videos,
        'videos_today': videos_today,
        'videos_queued': videos_queued,
        'videos_posted': videos_posted,
        'posts_per_day': current_user.posts_per_day,
        'is_running': global_scheduler.is_running
    })

@app.route('/api/videos')
@login_required
def api_videos():
    """Retorna lista de vídeos"""
    status_filter = request.args.get('status', 'all')
    
    query = Video.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    videos = query.order_by(Video.created_at.desc()).limit(50).all()
    
    return jsonify([video.to_dict() for video in videos])

@app.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    """Gera novo conteúdo"""
    data = request.json or {}
    topic = data.get('topic', current_user.preferred_topic)
    duration = data.get('duration', current_user.video_duration)
    
    content = generate_content(topic, duration)
    
    # Salvar no banco
    video = Video(
        user_id=current_user.id,
        title=content['title'],
        topic=content['topic'],
        category=content['category'],
        script=content['script'],
        description=content['description'],
        video_path=content['video_path'],
        status='queued'
    )
    db.session.add(video)
    db.session.commit()
    
    add_log(current_user.id, f"Vídeo gerado: {content['title']}", 'success')
    
    return jsonify({
        'status': 'ok',
        'video': video.to_dict()
    })

@app.route('/api/generate-batch', methods=['POST'])
@login_required
def api_generate_batch():
    """Gera múltiplos vídeos"""
    data = request.json or {}
    count = min(int(data.get('count', 5)), 50)  # Máximo 50
    
    videos = []
    for i in range(count):
        content = generate_content(current_user.preferred_topic, current_user.video_duration)
        video = Video(
            user_id=current_user.id,
            title=content['title'],
            topic=content['topic'],
            category=content['category'],
            script=content['script'],
            description=content['description'],
            video_path=content['video_path'],
            status='queued'
        )
        db.session.add(video)
        db.session.commit()
        videos.append(video.to_dict())
    
    add_log(current_user.id, f"Gerados {count} vídeos em lote", 'success')
    
    return jsonify({
        'status': 'ok',
        'count': count,
        'videos': videos
    })

@app.route('/api/video/<int:video_id>/delete', methods=['DELETE'])
@login_required
def api_delete_video(video_id):
    """Deleta um vídeo"""
    video = Video.query.filter_by(id=video_id, user_id=current_user.id).first()
    
    if video:
        # Remover arquivo
        if os.path.exists(video.video_path):
            os.remove(video.video_path)
        
        db.session.delete(video)
        db.session.commit()
        add_log(current_user.id, f"Vídeo deletado: {video.title}", 'warning')
        return jsonify({'status': 'ok'})
    
    return jsonify({'status': 'error', 'message': 'Vídeo não encontrado'}), 404

@app.route('/api/settings', methods=['POST'])
@login_required
def api_settings():
    """Atualiza configurações do usuário"""
    data = request.json or {}
    
    if 'posts_per_day' in data:
        current_user.posts_per_day = int(data['posts_per_day'])
    if 'preferred_topic' in data:
        current_user.preferred_topic = data['preferred_topic']
    if 'video_duration' in data:
        current_user.video_duration = int(data['video_duration'])
    
    db.session.commit()
    add_log(current_user.id, "Configurações atualizadas", 'info')
    
    return jsonify({
        'status': 'ok',
        'config': current_user.get_config()
    })

@app.route('/api/system/start')
@login_required
def api_system_start():
    """Inicia o agendador global"""
    global_scheduler.start()
    add_log(current_user.id, "Sistema iniciado", 'success')
    return jsonify({'status': 'started'})

@app.route('/api/system/stop')
@login_required
def api_system_stop():
    """Para o agendador global"""
    global_scheduler.stop()
    add_log(current_user.id, "Sistema parado", 'info')
    return jsonify({'status': 'stopped'})

@app.route('/api/logs')
@login_required
def api_logs():
    """Retorna logs do usuário"""
    logs = Log.query.filter_by(user_id=current_user.id)\
                   .order_by(Log.created_at.desc())\
                   .limit(100).all()
    
    return jsonify([{
        'message': log.message,
        'type': log.type,
        'created_at': log.created_at.isoformat()
    } for log in logs])

@app.route('/api/queue/clear', methods=['POST'])
@login_required
def api_clear_queue():
    """Limpa fila de vídeos"""
    Video.query.filter_by(user_id=current_user.id, status='queued').delete()
    db.session.commit()
    add_log(current_user.id, "Fila de vídeos limpa", 'warning')
    return jsonify({'status': 'ok'})

# ============================================
# INICIALIZAÇÃO
# ============================================

def init_db():
    """Inicializa o banco de dados"""
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin se não existir
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@tiktokbot.com',
                posts_per_day=5
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Usuário admin criado (admin / admin123)")

if __name__ == '__main__':
    init_db()
    
    print("""
╔══════════════════════════════════════════════╗
║   🤖 TIKTOK BOT - SISTEMA WEB COMPLETO     ║
║   Com autenticação e banco de dados         ║
╠══════════════════════════════════════════════╣
║   Acesse: http://localhost:5000             ║
║   Admin: admin / admin123                   ║
║   Pressione Ctrl+C para parar               ║
╚══════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)