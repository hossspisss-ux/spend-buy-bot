import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from functools import wraps
import requests
from database import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'local-key-2024'

PASSWORD = "6157447"
BOT_TOKEN = "8712920851:AAEFNPFNStslDFGSl1YWuHC9-DeNa9oOk4M"
API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
CHANNEL = "@why_trickovich"

def notify(uid, code, status, price=None):
    icon = db.get_status_icon(status)
    
    msg = f"🔔 **СТАТУС ЗАКАЗА ИЗМЕНЕН**\n\n"
    msg += f"┌ **Заказ №{code}**\n"
    msg += f"├ {icon} **Новый статус:** {status}\n"
    if price:
        msg += f"├ 💰 **Сумма:** {price} ₽\n"
    msg += f"└ 🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    try:
        requests.post(API, json={'chat_id': uid, 'text': msg, 'parse_mode': 'Markdown'})
    except:
        pass

def need_auth(f):
    @wraps(f)
    def wrap(*a, **k):
        if not session.get('auth'):
            return redirect(url_for('login'))
        return f(*a, **k)
    return wrap

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        if request.form.get('pass') == PASSWORD:
            session['auth'] = True
            return redirect(url_for('dashboard'))
        error = 'Неверный пароль'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@need_auth
def dashboard():
    items = db.get_all_orders()
    total = len(items)
    clients = len(set([i['user_id'] for i in items if i['user_id']]))
    active = len([i for i in items if i['status'] != 'В ПВЗ СДЭК'])
    return render_template('main.html', orders=items[:5], total=total, clients=clients, active=active)

@app.route('/orders')
@need_auth
def orders():
    orders_list = db.get_all_orders()
    statuses = db.get_all_statuses()
    return render_template('orders.html', orders=orders_list, statuses=statuses)

@app.route('/users')
@need_auth
def users():
    items = db.get_all_orders()
    data = {}
    
    for i in items:
        uid = i['user_id']
        if uid:
            if uid not in data:
                data[uid] = {
                    'id': uid,
                    'count': 0,
                    'total': 0,
                    'list': []
                }
            data[uid]['count'] += 1
            data[uid]['total'] += i['price'] or 0
            data[uid]['list'].append({
                'code': i['code'],
                'product': i['product'],
                'status': i['status'],
                'price': i['price'],
                'date': i['created']
            })
    
    return render_template('users.html', users=list(data.values()))

@app.route('/order/add', methods=['POST'])
@need_auth
def add():
    code = request.form.get('code', '').strip().upper()
    product = request.form.get('product', '').strip()
    status = request.form.get('status', 'Выкуплен')
    
    try:
        price = int(float(request.form.get('price', 0)))
    except:
        price = 0
    
    if not code or not product:
        flash('Заполните поля', 'error')
        return redirect(url_for('orders'))
    
    if db.get_order(code):
        flash(f'Заказ {code} уже есть', 'error')
        return redirect(url_for('orders'))
    
    if db.add_order(code, product, status, price):
        flash(f'✓ Заказ {code} добавлен', 'success')
    else:
        flash('Ошибка', 'error')
    
    return redirect(url_for('orders'))

@app.route('/order/update/<code>', methods=['POST'])
@need_auth
def update(code):
    new = request.form.get('status', '')
    
    if not new:
        flash('Выберите статус', 'error')
        return redirect(url_for('orders'))
    
    order = db.get_order(code)
    if not order:
        flash(f'Заказ {code} не найден', 'error')
        return redirect(url_for('orders'))
    
    user = order['user_id']
    
    result = db.update_status(code, new)
    
    if result is not None:
        flash(f'✓ Статус {code} обновлен', 'success')
        if user:
            notify(user, code, new, order['price'])
    else:
        flash('Ошибка', 'error')
    
    return redirect(url_for('orders'))

@app.route('/order/delete/<code>', methods=['POST'])
@need_auth
def delete(code):
    user = db.delete_order(code)
    
    if user:
        flash(f'✓ Заказ {code} удален', 'success')
        try:
            msg = f"❌ **ЗАКАЗ УДАЛЕН**\n\nЗаказ №{code}"
            requests.post(API, json={'chat_id': user, 'text': msg, 'parse_mode': 'Markdown'})
        except:
            pass
    else:
        flash(f'Заказ {code} не найден', 'error')
    
    return redirect(url_for('orders'))

@app.route('/settings')
@need_auth
def settings():
    currency = db.get_currency()
    delivery = db.get_delivery()
    statuses = db.get_all_statuses()
    return render_template('settings.html', currency=currency, delivery=delivery, statuses=statuses)

@app.route('/currency/update/<name>', methods=['POST'])
@need_auth
def update_currency(name):
    try:
        val = float(request.form.get('value', 0))
    except:
        val = 0
    
    if val <= 0:
        flash('Введите число', 'error')
        return redirect(url_for('settings'))
    
    if db.update_currency(name, val):
        flash(f'✓ {name} обновлен', 'success')
    else:
        flash('Ошибка', 'error')
    
    return redirect(url_for('settings'))

@app.route('/delivery/update/<int:delivery_id>', methods=['POST'])
@need_auth
def update_delivery(delivery_id):
    try:
        price = int(request.form.get('price', 0))
        days_min = int(request.form.get('days_min', 0))
        days_max = int(request.form.get('days_max', 0))
    except:
        flash('Введите корректные числа', 'error')
        return redirect(url_for('settings'))
    
    if price <= 0 or days_min <= 0 or days_max <= 0 or days_min > days_max:
        flash('Проверьте введенные данные', 'error')
        return redirect(url_for('settings'))
    
    if db.update_delivery(delivery_id, price, days_min, days_max):
        flash(f'✓ Доставка обновлена', 'success')
    else:
        flash('Ошибка', 'error')
    
    return redirect(url_for('settings'))

@app.route('/ping')
def ping():
    return 'pong', 200

@app.route('/api/version')
def api_version():
    return jsonify({'v': db.get_version()})

@app.route('/api/orders')
def api_orders():
    return jsonify(db.get_all_orders())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)