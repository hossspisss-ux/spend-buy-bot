@echo off
chcp 65001 >nul
title UPDATE SPEND BUY BOT
color 0D

echo ========================================
echo    ОБНОВЛЕНИЕ SPEND BUY BOT 2.1
echo ========================================
echo.

:: Проверка наличия Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Git не найден!
    echo     Скачайте и установите: https://git-scm.com/download/win
    pause
    exit /b
)
echo [✅] Git найден

:: Остановка бота
echo [1/4] Остановка сервисов...
call stop_bot.bat >nul
timeout /t 2 /nobreak >nul

:: Обновление кода
echo [2/4] Обновление кода с GitHub...
git pull
if %errorlevel% equ 0 (
    echo [✅] Код обновлен
) else (
    echo [⚠️] Ошибка обновления
)

:: Установка новых зависимостей
echo [3/4] Установка зависимостей...
pip install -r requirements.txt
echo [✅] Зависимости обновлены

:: Запуск бота
echo [4/4] Запуск сервисов...
call start_bot.bat

echo.
echo ========================================
echo [✅] ОБНОВЛЕНИЕ ЗАВЕРШЕНО
echo ========================================
echo.
pause
exit