#!/usr/bin/env python3
"""
TIKTOK AUTO POSTER - Versão Compacta
Sistema completo de geração e agendamento de vídeos
"""

import os
import json
import random
import textwrap
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============================================
# CONFIGURAÇÕES
# ============================================
class Config:
    OUTPUT_DIR = "output"
    POSTS_PER_DAY = 3
    VIDEO_DURATION = 60  # segundos
    
    # Temas para vídeos
    TOPICS = [
        "Dicas de produtividade",
        "Fatos surpreendentes sobre tecnologia",
        "Motivação para o dia",
        "Curiosidades sobre o universo",
        "Truques de vida útil",
        "Histórias inspiradoras",
        "Dicas de estudo",
        "Fatos históricos interessantes"
    ]
    
    HASHTAGS = {
        'default': ['#fyp', '#viral', '#tiktok', '#brasil'],
        'motivação': ['#motivação', '#foco', '#determinação'],
        'tecnologia': ['#tech', '#inovação', '#futuro'],
        'dicas': ['#dicas', '#tutorial', '#aprenda'],
    }

# ============================================
# GERADOR DE CONTEÚDO (IA Simulada)
# ============================================
class ContentGenerator:
    def __init__(self):
        self.used_topics = []
    
    def generate(self):
        """Gera conteúdo completo para um post"""
        topic = random.choice(Config.TOPICS)
        
        # Gerar título viral
        titles = [
            f"🔥 {topic.upper()} - Você Não Vai Acreditar!",
            f"😱 O SEGREDO sobre {topic} que NINGUÉM te conta",
            f"✨ {topic}: O Guia DEFINITIVO",
            f"💡 {topic} - Isso vai MUDAR sua vida!",
            f"🚀 {topic} - Assista até o final!"
        ]
        
        # Gerar script
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
        
        # Gerar descrição
        descriptions = [
            f"Gostou dessa dica sobre {topic}? "
            f"Deixa o like e compartilha! 🔥 "
            f"{' '.join(random.sample(Config.HASHTAGS['default'], 4))}",
            
            f"Incrível né? {topic} é realmente fascinante! "
            f"Me conta nos comentários o que você achou! 💬 "
            f"{' '.join(random.sample(Config.HASHTAGS['default'], 4))}"
        ]
        
        return {
            'topic': topic,
            'title': random.choice(titles),
            'script': random.choice(scripts),
            'description': random.choice(descriptions),
            'timestamp': datetime.now().isoformat()
        }

# ============================================
# GERADOR DE VÍDEOS SIMPLIFICADO
# ============================================
class VideoGenerator:
    def __init__(self):
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def create_video(self, content):
        """
        Cria um vídeo simples usando moviepy
        Se moviepy não estiver disponível, cria um placeholder
        """
        video_id = f"tiktok_{random.randint(10000, 99999)}"
        
        try:
            from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
            import numpy as np
            
            # Criar fundo colorido
            color = random.choice([
                (255, 100, 100), (100, 255, 100), 
                (100, 100, 255), (255, 255, 100)
            ])
            
            background = ColorClip(
                size=(1080, 1920), 
                color=color, 
                duration=Config.VIDEO_DURATION
            )
            
            # Adicionar texto
            txt_clip = TextClip(
                content['script'],
                fontsize=50,
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(900, None)
            )
            txt_clip = txt_clip.set_position('center').set_duration(Config.VIDEO_DURATION)
            
            # Combinar
            final_video = CompositeVideoClip([background, txt_clip])
            
            # Salvar
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
            # Criar arquivo placeholder
            output_path = f"{Config.OUTPUT_DIR}/{video_id}.txt"
            with open(output_path, 'w') as f:
                f.write(f"Vídeo Placeholder\n")
                f.write(f"Título: {content['title']}\n")
                f.write(f"Script: {content['script']}\n")
            return output_path

# ============================================
# GERENCIADOR DE FILA
# ============================================
class QueueManager:
    def __init__(self):
        self.queue = []
        self.history = []
        self.lock = threading.Lock()
        self.load_state()
    
    def add(self, post):
        with self.lock:
            post['id'] = len(self.history) + len(self.queue) + 1
            post['status'] = 'queued'
            post['added_at'] = datetime.now().isoformat()
            self.queue.append(post)
            self.save_state()
            return post['id']
    
    def get_next(self):
        with self.lock:
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
            'history': self.history[-50:]  # Últimos 50
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
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            print("✅ Agendador iniciado")
    
    def stop(self):
        self.running = False
        print("⏹ Agendador parado")
    
    def _run(self):
        while self.running:
            now = datetime.now()
            
            # Gerar conteúdo às 6h
            if now.hour == 6 and now.minute == 0:
                self._generate_daily_content()
            
            # Postar nos horários programados (8h, 14h, 20h)
            post_hours = [8, 14, 20]
            if now.hour in post_hours and now.minute == 0:
                self._process_queue()
            
            time.sleep(30)  # Verificar a cada 30 segundos
    
    def _generate_daily_content(self):
        print(f"\n📅 Gerando conteúdo do dia - {datetime.now()}")
        
        for i in range(Config.POSTS_PER_DAY):
            content = self.content_gen.generate()
            video_path = self.video_gen.create_video(content)
            
            post = {
                **content,
                'video_path': video_path,
                'scheduled_for': f"Post {i+1} do dia"
            }
            
            post_id = self.queue.add(post)
            print(f"  ✅ Post {i+1} criado (ID: {post_id})")
    
    def _process_queue(self):
        stats = self.queue.get_stats()
        
        if stats['processed_today'] >= Config.POSTS_PER_DAY:
            return
        
        post = self.queue.get_next()
        if post:
            self._notify_post_ready(post)
    
    def _notify_post_ready(self, post):
        """Notifica que um post está pronto para publicação"""
        print(f"""
╔══════════════════════════════════════╗
║     📤 POST PRONTO PARA TIKTOK      ║
╠══════════════════════════════════════╣
║ 📝 Título: {post['title'][:40]}...
║ 🏷️  Tópico: {post['topic']}
║ 📁 Vídeo: {post['video_path']}
║ 📋 Descrição: {post['description'][:50]}...
╠══════════════════════════════════════╣
║  🔔 ABRA O TIKTOK E PUBLIQUE!      ║
╚══════════════════════════════════════╝
        """)
        
        # Salvar em arquivo de notificações
        with open('posts_prontos.txt', 'a') as f:
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
║   🤖 TIKTOK AUTO POSTER v1.0       ║
║   Sistema de Automação Inteligente  ║
╚══════════════════════════════════════╝
        """)
    
    def menu(self):
        while True:
            stats = self.queue.get_stats()
            
            print(f"""
{'='*40}
📊 Status do Sistema
{'='*40}
📦 Posts na fila: {stats['queue_size']}
📤 Posts hoje: {stats['processed_today']}/{Config.POSTS_PER_DAY}
📈 Total processado: {stats['total_processed']}
{'='*40}

Opções:
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
                print("\n🎬 Gerando novo conteúdo...")
                content = self.content_gen.generate()
                video_path = self.video_gen.create_video(content)
                post = {**content, 'video_path': video_path}
                post_id = self.queue.add(post)
                print(f"✅ Post criado! ID: {post_id}")
                print(f"📁 Vídeo salvo em: {video_path}")
            
            elif choice == '4':
                print("\n📋 Fila de Posts:")
                if not self.queue.queue:
                    print("  (vazia)")
                else:
                    for i, post in enumerate(self.queue.queue, 1):
                        print(f"  {i}. {post['title'][:50]}...")
            
            elif choice == '5':
                try:
                    new_value = int(input("\nPosts por dia (1-24): "))
                    if 1 <= new_value <= 24:
                        Config.POSTS_PER_DAY = new_value
                        print(f"✅ Configurado para {new_value} posts/dia")
                    else:
                        print("❌ Valor inválido")
                except:
                    print("❌ Digite um número válido")
            
            elif choice == '6':
                path = os.path.abspath(Config.OUTPUT_DIR)
                print(f"\n📁 Pasta de vídeos: {path}")
                if os.name == 'nt':  # Windows
                    os.system(f'explorer {path}')
                else:  # Mac/Linux
                    os.system(f'open {path}')
            
            elif choice == '7':
                print("\n👋 Encerrando...")
                self.scheduler.stop()
                break

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    # Verificar dependências
    try:
        import moviepy
        print("✅ MoviePy instalado - Vídeos serão gerados")
    except ImportError:
        print("⚠️  MoviePy não instalado - Serão criados arquivos placeholder")
        print("   Para instalar: pip install moviepy")
    
    # Iniciar bot
    bot = TikTokBot()
    
    try:
        bot.menu()
    except KeyboardInterrupt:
        print("\n\n👋 Encerrando...")
        bot.scheduler.stop()