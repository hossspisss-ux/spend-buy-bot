import sqlite3
from datetime import datetime

class Storage:
    def __init__(self, name='data.db'):
        self.name = name
        self.build()
    
    def get(self):
        conn = sqlite3.connect(self.name)
        conn.row_factory = self.pack
        return conn
    
    def pack(self, cursor, row):
        result = {}
        for i, col in enumerate(cursor.description):
            result[col[0]] = row[i]
        return result
    
    def build(self):
        conn = self.get()
        cur = conn.cursor()
        
        # Таблица заказов
        cur.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                code TEXT PRIMARY KEY,
                user_id INTEGER,
                product TEXT,
                status TEXT,
                price INTEGER DEFAULT 0,
                created TEXT DEFAULT CURRENT_TIMESTAMP,
                updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица статусов заказов
        cur.execute('''
            CREATE TABLE IF NOT EXISTS order_statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status_name TEXT UNIQUE,
                status_order INTEGER,
                icon TEXT DEFAULT '📦'
            )
        ''')
        
        # Таблица курсов валют
        cur.execute('''
            CREATE TABLE IF NOT EXISTS currency (
                name TEXT PRIMARY KEY,
                value REAL,
                symbol TEXT DEFAULT '₽',
                updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица доставки
        cur.execute('''
            CREATE TABLE IF NOT EXISTS delivery (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country TEXT,
                type TEXT,
                price_per_kg INTEGER,
                days_min INTEGER,
                days_max INTEGER,
                updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица версии
        cur.execute('''
            CREATE TABLE IF NOT EXISTS version (
                id INTEGER PRIMARY KEY DEFAULT 1,
                num INTEGER DEFAULT 0
            )
        ''')
        
        cur.execute("SELECT COUNT(*) as total FROM version")
        if cur.fetchone()['total'] == 0:
            cur.execute("INSERT INTO version (num) VALUES (0)")
        
        # Добавляем статусы заказов (9 этапов)
        cur.execute("DELETE FROM order_statuses")
        
        status_list = [
            (1, 'Выкуплен', '🛒'),
            (2, 'Едет на склад', '🚚'),
            (3, 'На складе', '📦'),
            (4, 'В пути на таможню', '✈️'),
            (5, 'На таможне', '🛃'),
            (6, 'На таможне в РФ', '🛃'),
            (7, 'Выпущен с таможни', '✅'),
            (8, 'Передан в СДЭК', '📮'),
            (9, 'В ПВЗ СДЭК', '📍')
        ]
        
        for order, name, icon in status_list:
            cur.execute('''
                INSERT OR IGNORE INTO order_statuses (status_order, status_name, icon) 
                VALUES (?, ?, ?)
            ''', (order, name, icon))
        
        # Курсы валют с символами
        currency_data = [
            ('CNY', 11, '¥'),
            ('JPY', 7, '¥'),
            ('KRW', 1, '₩'),
            ('USD', 92, '$')
        ]
        for name, val, sym in currency_data:
            cur.execute('INSERT OR IGNORE INTO currency (name, value, symbol) VALUES (?, ?, ?)', 
                       (name, val, sym))
        
        # Очищаем и добавляем доставку
        cur.execute("DELETE FROM delivery")
        
        delivery_data = [
            # Страна, тип, цена/кг, мин дней, макс дней
            ('Япония', 'Стандарт', 1500, 10, 14),
            ('Китай', 'Карго', 800, 20, 25),
            ('Китай', 'Авиа Экспресс', 2500, 1, 5),
            ('Китай', 'Авиа Стандарт', 1800, 8, 14),
            ('Корея', 'Стандарт', 1200, 7, 10),
            ('США', 'Стандарт', 2500, 10, 15)
        ]
        
        for country, typ, price, min_d, max_d in delivery_data:
            cur.execute('''
                INSERT INTO delivery (country, type, price_per_kg, days_min, days_max) 
                VALUES (?, ?, ?, ?, ?)
            ''', (country, typ, price, min_d, max_d))
        
        # Тестовые заказы
        test_orders = [
            ('5252', 'NINE CAP', 'Выкуплен', 15000),
            ('5252213', 'NINE CAP', 'На складе', 15000)
        ]
        
        for code, prod, status, price in test_orders:
            cur.execute('INSERT OR IGNORE INTO orders (code, product, status, price) VALUES (?, ?, ?, ?)',
                       (code, prod, status, price))
        
        conn.commit()
        conn.close()
        print("✓ База данных создана")
    
    # ============= МЕТОДЫ ДЛЯ СТАТУСОВ =============
    def get_all_statuses(self):
        """Получение всех статусов заказов"""
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT * FROM order_statuses ORDER BY status_order')
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def get_status_icon(self, status_name):
        """Получение иконки для статуса"""
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT icon FROM order_statuses WHERE status_name = ?', (status_name,))
        row = cur.fetchone()
        conn.close()
        return row['icon'] if row else '📦'
    
    # ============= МЕТОДЫ ДЛЯ ВАЛЮТ =============
    def get_currency(self):
        """Получение курсов валют с символами"""
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT name, value, symbol FROM currency')
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def update_currency(self, name, value):
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('UPDATE currency SET value = ?, updated = CURRENT_TIMESTAMP WHERE name = ?',
                       (value, name))
            cur.execute('UPDATE version SET num = num + 1')
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============= МЕТОДЫ ДЛЯ ДОСТАВКИ =============
    def get_delivery(self):
        """Получение всех вариантов доставки"""
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT * FROM delivery ORDER BY country, type')
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def update_delivery(self, delivery_id, price, days_min, days_max):
        """Обновление цены и сроков доставки"""
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('''
                UPDATE delivery 
                SET price_per_kg = ?, days_min = ?, days_max = ?, updated = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (price, days_min, days_max, delivery_id))
            cur.execute('UPDATE version SET num = num + 1')
            conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка обновления доставки: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    # ============= МЕТОДЫ ДЛЯ ЗАКАЗОВ =============
    def add_order(self, code, product, status='Выкуплен', price=0):
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO orders (code, product, status, price) VALUES (?, ?, ?, ?)',
                       (code, product, status, price))
            cur.execute('UPDATE version SET num = num + 1')
            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def update_status(self, code, new_status):
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('SELECT user_id FROM orders WHERE code = ?', (code,))
            order = cur.fetchone()
            if not order:
                return None
            
            user = order['user_id']
            
            cur.execute('UPDATE orders SET status = ?, updated = CURRENT_TIMESTAMP WHERE code = ?',
                       (new_status, code))
            cur.execute('UPDATE version SET num = num + 1')
            conn.commit()
            return user
        except:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def delete_order(self, code):
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('SELECT user_id FROM orders WHERE code = ?', (code,))
            row = cur.fetchone()
            user = row['user_id'] if row else None
            
            cur.execute('DELETE FROM orders WHERE code = ?', (code,))
            cur.execute('UPDATE version SET num = num + 1')
            conn.commit()
            return user
        except:
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_all_orders(self):
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders ORDER BY created DESC')
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def get_order(self, code):
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders WHERE code = ?', (code,))
        row = cur.fetchone()
        conn.close()
        return row
    
    def get_user_orders(self, user_id):
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT * FROM orders WHERE user_id = ? ORDER BY created DESC', (user_id,))
        rows = cur.fetchall()
        conn.close()
        return rows
    
    def bind_order(self, code, user_id):
        conn = self.get()
        cur = conn.cursor()
        try:
            cur.execute('UPDATE orders SET user_id = ?, updated = CURRENT_TIMESTAMP WHERE code = ? AND user_id IS NULL',
                       (user_id, code))
            conn.commit()
            return cur.rowcount > 0
        except:
            return False
        finally:
            conn.close()
    
    def get_version(self):
        conn = self.get()
        cur = conn.cursor()
        cur.execute('SELECT num FROM version WHERE id = 1')
        row = cur.fetchone()
        conn.close()
        return row['num'] if row else 0

db = Storage()