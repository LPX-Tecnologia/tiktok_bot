cat > app.py << 'EOF'
#!/usr/bin/env python3
"""TikTok Bot - Servidor Web"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
import random
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações
class Config:
    OUTPUT_DIR = "output"
    POSTS_PER_DAY = 3
    PREFERRED_TOPIC = "auto"
    VIDEO_DURATION = 60
    
    TOPICS = {
        "motivação": ["Dicas de motivação", "Como manter o foco", "Histórias de superação"],
        "tecnologia": ["Novidades tech", "Dicas de programação", "Fatos surpreendentes"],
        "dicas": ["Dicas de produtividade", "Truques diários", "Life hacks"],
        "humor": ["Situações engraçadas", "Memes do momento", "Comédia"],
        "curiosidades": ["Fatos surpreendentes", "Você sabia?", "Curiosidades"]
    }

os.makedirs(Config.OUTPUT_DIR, exist_ok=True)

# Sistema de Fila
class QueueSystem:
    def __init__(self):
        self.queue = []
        self.history = []
        self.is_running = False
        self.load_state()
    
    def add_post(self, post_data):
        post_data['id'] = len(self.history) + len(self.queue) + 1
        post_data['status'] = 'queued'
        post_data['added_at'] = datetime.now().isoformat()
        self.queue.append(post_data)
        self.save_state()
        return len(self.queue)
    
    def get_next(self):
        if self.queue:
            post = self.queue.pop(0)
            post['status'] = 'processed'
            post['processed_at'] = datetime.now().isoformat()
            self.history.append(post)
            self.save_state()
            return post
        return None
    
    def get_status(self):
        today = datetime.now().date()
        processed_today = len([h for h in self.history 
                              if datetime.fromisoformat(h.get('processed_at', '')).date() == today])
        
        return {
            'in_queue': len(self.queue),
            'processed_today': processed_today,
            'total_processed': len(self.history),
            'is_running': self.is_running,
            'queue': list(self.queue)[:10],
            'history': self.history[-10:]
        }
    
    def save_state(self):
        try:
            data = {
                'queue': self.queue,
                'history': self.history[-100:],
                'config': {
                    'posts_per_day': Config.POSTS_PER_DAY,
                    'preferred_topic': Config.PREFERRED_TOPIC,
                    'video_duration': Config.VIDEO_DURATION
                }
            }
            with open('bot_state.json', 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def load_state(self):
        try:
            if os.path.exists('bot_state.json'):
                with open('bot_state.json', 'r') as f:
                    data = json.load(f)
                    self.queue = data.get('queue', [])
                    self.history = data.get('history', [])
                    config = data.get('config', {})
                    Config.POSTS_PER_DAY = config.get('posts_per_day', 3)
                    Config.PREFERRED_TOPIC = config.get('preferred_topic', 'auto')
                    Config.VIDEO_DURATION = config.get('video_duration', 60)
        except:
            pass

queue_system = QueueSystem()

# Gerador de Conteúdo
def generate_content(topic_preference="auto", duration=60):
    if topic_preference == "auto" or topic_preference not in Config.TOPICS:
        category = random.choice(list(Config.TOPICS.keys()))
    else:
        category = topic_preference
    
    topic = random.choice(Config.TOPICS[category])
    
    titles = [
        f"🔥 {topic.upper()} - Você Não Vai Acreditar!",
        f"😱 O SEGREDO sobre {topic}",
        f"✨ {topic}: O Guia DEFINITIVO",
        f"💡 {topic} - Isso Muda Tudo!"
    ]
    
    scripts = [
        f"Você sabia que {topic.lower()} pode transformar seu dia? "
        f"Hoje vou te mostrar como isso funciona. "
        f"Presta atenção que vai fazer diferença. "
        f"Compartilha com quem precisa ver! 🔥",
        
        f"Atenção para essa informação sobre {topic.lower()}! "
        f"Isso é algo que muita gente não conhece. "
        f"Fica até o final que você vai se surpreender. "
        f"Já deixa o like! ✨"
    ]
    
    descriptions = [
        f"Gostou? Deixa o like! 🔥 #fyp #viral #tiktok #{category}",
        f"Incrível né? Comenta o que achou! 💬 #fyp #viral #{category}"
    ]
    
    content = {
        'topic': topic,
        'category': category,
        'title': random.choice(titles),
        'script': random.choice(scripts),
        'description': random.choice(descriptions),
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    # Criar arquivo do vídeo
    video_id = f"tiktok_{random.randint(10000, 99999)}"
    video_path = f"{Config.OUTPUT_DIR}/{video_id}.txt"
    
    with open(video_path, 'w', encoding='utf-8') as f:
        f.write(f"VÍDEO GERADO PELO TIKTOK BOT\n")
        f.write(f"{'='*40}\n")
        f.write(f"Título: {content['title']}\n")
        f.write(f"Tópico: {content['topic']}\n")
        f.write(f"Duração: {content['duration']}s\n")
        f.write(f"{'='*40}\n")
        f.write(f"Script:\n{content['script']}\n")
        f.write(f"{'='*40}\n")
        f.write(f"Descrição:\n{content['description']}\n")
    
    content['video_path'] = video_path
    content['video_id'] = video_id
    
    return content

# Scheduler Background
def scheduler_loop():
    while queue_system.is_running:
        now = datetime.now()
        
        if now.hour == 6 and now.minute == 0:
            print(f"[{datetime.now()}] Gerando posts do dia...")
            for i in range(Config.POSTS_PER_DAY):
                content = generate_content(Config.PREFERRED_TOPIC, Config.VIDEO_DURATION)
                queue_system.add_post(content)
        
        if now.hour in [8, 12, 16, 20] and now.minute == 0:
            status = queue_system.get_status()
            if status['processed_today'] < Config.POSTS_PER_DAY:
                post = queue_system.get_next()
                if post:
                    print(f"[{datetime.now()}] Post processado: {post['title']}")
        
        time.sleep(30)

# Rotas da API
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/status')
def get_status():
    return jsonify(queue_system.get_status())

@app.route('/api/start')
def start_system():
    if not queue_system.is_running:
        queue_system.is_running = True
        threading.Thread(target=scheduler_loop, daemon=True).start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already_running'})

@app.route('/api/stop')
def stop_system():
    queue_system.is_running = False
    return jsonify({'status': 'stopped'})

@app.route('/api/generate', methods=['POST'])
def generate_now():
    data = request.json or {}
    topic = data.get('topic', Config.PREFERRED_TOPIC)
    duration = data.get('duration', Config.VIDEO_DURATION)
    
    content = generate_content(topic, duration)
    position = queue_system.add_post(content)
    
    return jsonify({
        'status': 'ok',
        'position': position,
        'content': content
    })

@app.route('/api/settings', methods=['POST'])
def update_settings():
    data = request.json or {}
    
    if 'posts_per_day' in data:
        Config.POSTS_PER_DAY = int(data['posts_per_day'])
    if 'topic' in data:
        Config.PREFERRED_TOPIC = data['topic']
    if 'duration' in data:
        Config.VIDEO_DURATION = int(data['duration'])
    
    queue_system.save_state()
    
    return jsonify({
        'status': 'ok',
        'config': {
            'posts_per_day': Config.POSTS_PER_DAY,
            'preferred_topic': Config.PREFERRED_TOPIC,
            'video_duration': Config.VIDEO_DURATION
        }
    })

@app.route('/api/queue/clear', methods=['POST'])
def clear_queue():
    queue_system.queue = []
    queue_system.save_state()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════╗
║   🤖 TIKTOK BOT - WEB CONTROLE         ║
║   Tudo pelo navegador!                  ║
╠══════════════════════════════════════════╣
║   Acesse: http://localhost:5000         ║
║   Pressione Ctrl+C para parar           ║
╚══════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
