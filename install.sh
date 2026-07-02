#!/bin/bash
echo "==================================="
echo "Instalando TikTok Auto Poster"
echo "==================================="

# Criar pastas
mkdir -p output/videos output/logs

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Python não encontrado! Instale em: https://python.org"
    exit 1
fi

# Instalar dependências
pip3 install moviepy Pillow apscheduler

echo ""
echo "==================================="
echo "Instalação concluída!"
echo "Execute: python3 tiktok_bot.py"
echo "==================================="