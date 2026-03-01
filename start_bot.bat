@echo off
chcp 65001 >nul
title SPEND BUY BOT 2.1
color 0A

echo ========================================
echo    ЗАПУСК SPEND BUY BOT 2.1
echo ========================================
echo.

:: Проверка наличия Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Python не найден!
    echo     Установите Python с python.org
    pause
    exit /b
)
echo [✅] Python найден

:: Проверка наличия файлов
if not exist "database.py" (
    echo [❌] Файл database.py не найден!
    pause
    exit /b
)
if not exist "admin.py" (
    echo [❌] Файл admin.py не найден!
    pause
    exit /b
)
if not exist "bot.py" (
    echo [❌] Файл bot.py не найден!
    pause
    exit /b
)
if not exist "templates" (
    echo [❌] Папка templates не найдена!
    pause
    exit /b
)
echo [✅] Все файлы на месте

:: Удаление старой базы данных (раскомментируйте если нужно)
:: if exist "data.db" (
::     del data.db
::     echo [✅] Старая база данных удалена
:: )

:: Установка зависимостей
echo.
echo [1/4] Проверка зависимостей...
pip show aiogram >nul 2>&1
if %errorlevel% neq 0 (
    echo     Установка aiogram...
    pip install aiogram==3.0.0
)
pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo     Установка flask...
    pip install flask==2.3.3
)
pip show requests >nul 2>&1
if %errorlevel% neq 0 (
    echo     Установка requests...
    pip install requests==2.31.0
)
echo [✅] Зависимости установлены

:: Запуск админ панели
echo.
echo [2/4] Запуск админ панели...
start "Spend Buy Admin" cmd /k "title Spend Buy Admin && color 0B && echo [🌐] Админ панель запущена && python admin.py"
timeout /t 3 /nobreak >nul

:: Запуск бота
echo [3/4] Запуск Telegram бота...
start "Spend Buy Bot" cmd /k "title Spend Buy Bot && color 0C && echo [🤖] Бот запущен && python bot.py"
timeout /t 2 /nobreak >nul

:: Информация
echo [4/4] Проверка...
echo.
echo ========================================
echo [✅] ВСЕ КОМПОНЕНТЫ ЗАПУЩЕНЫ
echo ========================================
echo.
echo [🌐] Админ панель: http://localhost:5000
echo [🔑] Пароль: 6157447
echo [🤖] Бот: /start
echo [👑] Секретная команда: admin_panel228
echo [📦] Тестовые заказы: 5252, 5252213
echo.
echo ========================================
echo [ℹ️]  Окна с процессами открыты отдельно
echo [ℹ️]  Не закрывайте их во время работы
echo ========================================
echo.
pause
exit