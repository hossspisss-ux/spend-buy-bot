@echo off
chcp 65001 >nul
title 📤 ЗАГРУЗКА НА GITHUB
color 0A

echo ========================================
echo    📤 ЗАГРУЗКА НА GITHUB
echo ========================================
echo.

:: Проверка наличия Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Git не найден!
    echo     Установите Git: https://git-scm.com/download/win
    pause
    exit /b
)
echo [✅] Git найден

:: Проверка, что мы в репозитории
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌] Это не Git-репозиторий!
    echo     Сначала выполните git init
    pause
    exit /b
)

:: Добавление всех изменений
echo [1/4] Добавление файлов...
git add .
if %errorlevel% equ 0 (
    echo [✅] Файлы добавлены
) else (
    echo [❌] Ошибка при добавлении
    pause
    exit /b
)

:: Создание коммита
echo [2/4] Создание коммита...
set /p commit_msg="Введите описание изменений: "
if "%commit_msg%"=="" set commit_msg=Автоматическое обновление %date%

git commit -m "%commit_msg%"
if %errorlevel% equ 0 (
    echo [✅] Коммит создан
) else (
    echo [❌] Ошибка при создании коммита
    pause
    exit /b
)

:: Отправка на GitHub
echo [3/4] Отправка на GitHub...
git push origin master
if %errorlevel% equ 0 (
    echo [✅] Код отправлен на GitHub
) else (
    echo [❌] Ошибка при отправке
    echo.
    echo Возможные причины:
    echo 1. Нет подключения к интернету
    echo 2. Неправильные учетные данные
    echo 3. Ветка называется не master, а main
    echo.
    echo Попробуйте: git push origin main
    pause
    exit /b
)

:: Итог
echo [4/4] Проверка...
echo.
echo ========================================
echo [✅] ГОТОВО!
echo ========================================
echo.
echo 📦 Ваш код на GitHub:
echo https://github.com/hossspisss-ux/spend-buy-bot
echo.
echo 📝 Описание коммита: %commit_msg%
echo ========================================
echo.

pause
exit