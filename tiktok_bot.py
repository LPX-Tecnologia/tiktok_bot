#!/usr/bin/env python3
"""
TIKTOK BOT - Sistema de Automação
Versão: 1.0
Repositório: https://github.com/LPX-Tecnologia/tiktok_bot
"""

import os
import json
import random
import threading
import time
from datetime import datetime
from pathlib import Path

# ============================================
# CONFIGURAÇÕES
# ============================================
class Config:
    OUTPUT_DIR = "output"
    POSTS_PER_DAY = 3
    
    TOPICS = [
        "Dicas de produtividade",
        "Fatos surpreendentes",
        "Motivação diária",
        "Curiosidades tech",
        "Truques de vida",
        "Histórias inspiradoras",
        "Dicas de estudo",
        "Fatos históricos"
    ]

# ============================================
# GERADOR DE CONTEÚDO
# ============================================
class ContentGenerator:
    def generate(self):
        topic = random.choice(Config.TOPICS)
        
        titles = [
            f"🔥 {topic.upper()} - Você Não Vai Acreditar!",
            f"😱 O SEGREDO sobre {topic}",
            f"✨ {topic}: O Guia DEFINITIVO",
            f"💡 {topic} - Isso Muda Tudo!"
        ]
        
        scripts = [
            f"Você sabia que {topic.lower()} pode transformar seu dia? "
            f"Hoje vou te mostrar como isso funciona na prática. "
            f"Presta atenção nessa dica porque vai fazer toda diferença. "
            f"Compartilha com alguém que precisa ver isso!",
            
            f"Atenção para essa informação sobre {topic.lower()}! "
            f"Isso é algo que muita gente não conhece mas deveria. "
            f"Fica comigo até o final que você vai se surpreender. "
            f"Não esquece de curtir e seguir para mais conteúdos!"
        ]
        
        descriptions = [
            f"Gostou? Deixa o like! 🔥 #fyp #viral #tiktok #brasil",
            f"Incrível né? Comenta o que achou! 💬 #fyp #viral #tiktok"
        ]
        
        return {
            'topic': topic,
            'title': random.choice(titles),
            'script': random.choice(scripts),
            'description': random.choice(descriptions),
            'timestamp': datetime.now().isoformat()
        }

# ============================================
# GERADOR DE VÍDEOS
# ============================================
class VideoGenerator:
    def __init__(self):
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def create_video(self, content):
        video_id = f"tiktok_{random.randint(10000, 99999)}"
        
        try:
            from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
            
            colors = [
                (255, 100, 100), (100, 255, 100), 
                (100, 100, 255), (255, 255, 100)
            ]
            
            background = ColorClip(
                size=(1080, 1920), 
                color=random.choice(colors), 
                duration=60
            )
            
            txt_clip = TextClip(
                content['script'],
                fontsize=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(900, None)
            ).set_position('center').set_duration(60)
            
            final_video = CompositeVideoClip([background, txt_clip])
            output_path = f"{Config.OUTPUT_DIR}/{video_id}.mp4"
            
            final_video.write_videofile(
                output_path,
                fps=24,
                codec='libx264',
                audio=False,
                verbose=False
            )
            
            return output_path
            
        except ImportError:
            # Criar placeholder se moviepy não estiver disponível
            output_path = f"{Config.OUTPUT_DIR}/{video_id}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"Vídeo Placeholder\n")
                f.write(f"Título: {content['title']}\n")
                f.write(f"Script: {content['script']}\n")
                f.write(f"Descrição: {content['description']}\n")
            return output_path

# ============================================
# GERENCIADOR DE FILA
# ============================================
class QueueManager:
    def __init__(self):
        self.queue = []
        self.history = []
        self.load_state()
    
    def add(self, post):
        post['id'] = len(self.history) + len(self.queue) + 1
        post['status'] = 'queued'
        post['added_at'] = datetime.now().isoformat()
        self.queue.append(post)
        self.save_state()
        return post['id']
    
    def get_next(self):
        if self.queue:
            post = self.queue.pop(0)
            post['status'] = 'processing'
            post['processed_at'] = datetime.now().isoformat()
            self.history.append(post)
            self.save_state()
            return post
        return None
    
    def get_stats(self):
        today = datetime.now().date()
        return {
            'queue_size': len(self.queue),
            'processed_today': len([
                h for h in self.history
                if datetime.fromisoformat(h.get('processed_at', '')).date() == today
            ]),
            'total_processed': len(self.history)
        }
    
    def save_state(self):
        data = {
            'queue': self.queue,
            'history': self.history[-50:]
        }
        with open('queue_state.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_state(self):
        if os.path.exists('queue_state.json'):
            with open('queue_state.json', 'r') as f:
                data = json.load(f)
                self.queue = data.get('queue', [])
                self.history = data.get('history', [])

# ============================================
# AGENDADOR
# ============================================
class Scheduler:
    def __init__(self, content_gen, video_gen, queue_mgr):
        self.content_gen = content_gen
        self.video_gen = video_gen
        self.queue = queue_mgr
        self.running = False
        self.thread = None
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            print("✅ Agendador iniciado!")
    
    def stop(self):
        self.running = False
        print("⏹ Agendador parado!")
    
    def _run(self):
        while self.running:
            now = datetime.now()
            
            # Gerar conteúdo às 6h
            if now.hour == 6 and now.minute == 0:
                self._generate_daily_content()
            
            # Postar nos horários: 8h, 14h, 20h
            if now.hour in [8, 14, 20] and now.minute == 0:
                self._process_queue()
            
            time.sleep(30)
    
    def _generate_daily_content(self):
        print(f"\n📅 Gerando conteúdo - {datetime.now()}")
        
        for i in range(Config.POSTS_PER_DAY):
            content = self.content_gen.generate()
            video_path = self.video_gen.create_video(content)
            
            post = {**content, 'video_path': video_path}
            post_id = self.queue.add(post)
            print(f"  ✅ Post {i+1} criado (ID: {post_id})")
    
    def _process_queue(self):
        stats = self.queue.get_stats()
        
        if stats['processed_today'] >= Config.POSTS_PER_DAY:
            return
        
        post = self.queue.get_next()
        if post:
            self._notify_post(post)
    
    def _notify_post(self, post):
        print(f"""
╔══════════════════════════════════════╗
║     📤 POST PRONTO PARA TIKTOK      ║
╠══════════════════════════════════════╣
║ 📝 {post['title'][:35]}...
║ 🏷️  {post['topic']}
║ 📁 {post['video_path']}
║ 📋 {post['description'][:40]}...
╠══════════════════════════════════════╣
║  🔔 ABRA O TIKTOK E PUBLIQUE!      ║
╚══════════════════════════════════════╝
        """)
        
        with open('posts_prontos.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Data: {datetime.now()}\n")
            f.write(f"Título: {post['title']}\n")
            f.write(f"Descrição: {post['description']}\n")
            f.write(f"Vídeo: {post['video_path']}\n")

# ============================================
# INTERFACE PRINCIPAL
# ============================================
class TikTokBot:
    def __init__(self):
        self.content_gen = ContentGenerator()
        self.video_gen = VideoGenerator()
        self.queue = QueueManager()
        self.scheduler = Scheduler(self.content_gen, self.video_gen, self.queue)
        
        print("""
╔══════════════════════════════════════╗
║   🤖 TIKTOK BOT v1.0               ║
║   github.com/LPX-Tecnologia         ║
╚══════════════════════════════════════╝
        """)
    
    def menu(self):
        while True:
            stats = self.queue.get_stats()
            
            print(f"""
{'='*40}
📊 Status: {stats['processed_today']}/{Config.POSTS_PER_DAY} posts hoje
📦 Fila: {stats['queue_size']} | Total: {stats['total_processed']}
{'='*40}

1. ▶️  Iniciar agendador automático
2. ⏹  Parar agendador
3. 🎬  Gerar conteúdo agora
4. 📋  Ver fila de posts
5. ⚙️  Configurar posts/dia
6. 📁  Abrir pasta de vídeos
7. 🚪  Sair

Escolha: """, end='')
            
            choice = input().strip()
            
            if choice == '1':
                self.scheduler.start()
            elif choice == '2':
                self.scheduler.stop()
            elif choice == '3':
                print("\n🎬 Gerando conteúdo...")
                content = self.content_gen.generate()
                video_path = self.video_gen.create_video(content)
                post = {**content, 'video_path': video_path}
                post_id = self.queue.add(post)
                print(f"✅ Post criado! ID: {post_id}")
                print(f"📁 Vídeo: {video_path}")
            elif choice == '4':
                print("\n📋 Fila de Posts:")
                if not self.queue.queue:
                    print("  (vazia)")
                for i, post in enumerate(self.queue.queue, 1):
                    print(f"  {i}. {post['title'][:50]}...")
            elif choice == '5':
                try:
                    n = int(input("\nPosts por dia (1-24): "))
                    if 1 <= n <= 24:
                        Config.POSTS_PER_DAY = n
                        print(f"✅ {n} posts/dia")
                except:
                    print("❌ Inválido!")
            elif choice == '6':
                path = os.path.abspath(Config.OUTPUT_DIR)
                print(f"\n📁 {path}")
                if os.name == 'nt':
                    os.system(f'explorer {path}')
                else:
                    os.system(f'open {path}')
            elif choice == '7':
                print("\n👋 Até logo!")
                self.scheduler.stop()
                break

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    print("\nVerificando dependências...")
    try:
        import moviepy
        print("✅ MoviePy OK")
    except:
        print("⚠️  MoviePy não instalado - instale com: pip install moviepy")
    
    bot = TikTokBot()
    try:
        bot.menu()
    except KeyboardInterrupt:
        print("\n\n👋 Encerrando...")
        bot.scheduler.stop()
