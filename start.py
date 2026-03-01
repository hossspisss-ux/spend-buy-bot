import subprocess
import sys
import os
import time

def main():
    print('\n' + '='*40)
    print(' 🚀 ЗАПУСК SPEND BUY BOT 2.1')
    print('='*40)
    
    files = ['database.py', 'admin.py', 'bot.py']
    missing = []
    
    for f in files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print('\n❌ Нет файлов:')
        for f in missing:
            print(f'   - {f}')
        print('\nСоздайте файлы и запустите снова')
        input('\nНажмите Enter')
        return
    
    print('\n✓ Все файлы на месте')
    
    if os.path.exists('data.db'):
        os.remove('data.db')
        print('✓ Новая база данных создана')
    
    print('\n🚀 Запуск компонентов...\n')
    
    subprocess.Popen([sys.executable, 'admin.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
    print('🌐 Админ панель запущена')
    time.sleep(2)
    
    subprocess.Popen([sys.executable, 'bot.py'], creationflags=subprocess.CREATE_NEW_CONSOLE)
    print('🤖 Бот запущен')
    
    print('\n' + '='*40)
    print('✅ ВСЁ ГОТОВО!')
    print('='*40)
    print('\n🌐 Админка: http://localhost:5000')
    print('🔑 Пароль: 6157447')
    print('📱 Бот: /start')
    print('👑 Секретная команда: admin_panel228')
    print('📦 Тестовые заказы: 5252, 5252213')
    print('\n' + '='*40)
    
    input('\nНажмите Enter для выхода...')

if __name__ == '__main__':
    main()