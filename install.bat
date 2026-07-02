@echo off
echo ===================================
echo Instalando TikTok Auto Poster
echo ===================================

echo.
echo Criando pastas...
mkdir output
mkdir output\videos
mkdir output\logs

echo.
echo Instalando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado! Instale em: https://python.org
    pause
    exit
)

echo.
echo Instalando dependencias...
pip install moviepy Pillow apscheduler

echo.
echo ===================================
echo Instalacao concluida!
echo.
echo Execute: python tiktok_bot.py
echo ===================================
pause