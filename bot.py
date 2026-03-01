import asyncio
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from database import db

TOKEN = "8712920851:AAEFNPFNStslDFGSl1YWuHC9-DeNa9oOk4M"
ADMINS = [8087828990, 905347840]
PHOTO = "welcome.jpg"
CHANNEL = "https://t.me/why_trickovich"

COUNTRIES = ["Япония", "Китай", "Корея", "США"]
COUNTRY_TO = {
    "Япония": "JPY",
    "Китай": "CNY", 
    "Корея": "KRW",
    "США": "USD"
}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class CheckOrder(StatesGroup):
    code = State()

class Calculate(StatesGroup):
    country = State()
    price = State()

def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 МОИ ЗАКАЗЫ", callback_data="my")],
        [InlineKeyboardButton(text="🔍 ПРОВЕРИТЬ ЗАКАЗ", callback_data="check")],
        [InlineKeyboardButton(text="🧮 КАЛЬКУЛЯТОР", callback_data="calc")],
        [InlineKeyboardButton(text="💱 КУРСЫ ВАЛЮТ", callback_data="kurs")],
        [InlineKeyboardButton(text="📦 ТАРИФЫ ДОСТАВКИ", callback_data="dost")],
        [InlineKeyboardButton(text="🛍️ ЗАКАЗАТЬ", url=CHANNEL)]
    ])
    return kb

def country_menu():
    btns = []
    for c in COUNTRIES:
        if c == "Япония":
            f = "🇯🇵"
        elif c == "Китай":
            f = "🇨🇳"
        elif c == "Корея":
            f = "🇰🇷"
        else:
            f = "🇺🇸"
        btns.append([InlineKeyboardButton(text=f"{f} {c}", callback_data=f"cnt_{c}")])
    
    btns.append([InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=btns)

def admin_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 АДМИНКА", url="https://spend-buy-bot.onrender.com")],
        [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
    ])
    return kb

def is_admin(uid):
    return uid in ADMINS

def format_date(d):
    try:
        dt = datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%d.%m.%Y %H:%M')
    except:
        return str(d)

@dp.message(F.text == "/start")
async def start(m: Message):
    try:
        name = m.from_user.first_name or "Друг"
        text = f"✨ **Привет, {name}!** ✨\n\n"
        text += f"Добро пожаловать в бот [Spend Buy]({CHANNEL})\n"
        text += "Я помогу тебе отслеживать заказы и рассчитывать стоимость покупок\n\n"
        text += "📌 **Выбери действие в меню:**"
        
        if os.path.exists(PHOTO):
            pic = FSInputFile(PHOTO)
            await m.answer_photo(photo=pic, caption=text, parse_mode='Markdown', reply_markup=main_menu())
        else:
            await m.answer(text, parse_mode='Markdown', reply_markup=main_menu())
    except Exception as e:
        log.error(f"Ошибка: {e}")

@dp.message(F.text == "admin_panel228")
async def admin(m: Message):
    if not is_admin(m.from_user.id):
        await m.answer("⛔ Нет доступа")
        return
    
    text = "👑 **АДМИН ПАНЕЛЬ** 👑\n\n"
    text += "🌐 Админка: https://spend-buy-bot.onrender.com\n"
    text += "🔑 Пароль: 6157447"
    
    await m.answer(text, parse_mode='Markdown', reply_markup=admin_menu())

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.message.delete()
    await c.message.answer("📌 **Меню:**", parse_mode='Markdown', reply_markup=main_menu())
    await c.answer()

@dp.callback_query(F.data == "my")
async def my_orders(c: CallbackQuery):
    uid = c.from_user.id
    items = db.get_user_orders(uid)
    
    if not items:
        await c.message.answer("📭 **У вас пока нет заказов**")
        await c.answer()
        return
    
    text = "📋 **ТВОИ ЗАКАЗЫ**\n\n"
    for i in items:
        icon = db.get_status_icon(i['status'])
        d = format_date(i['created'])
        text += f"┌ **Заказ №{i['code']}**\n"
        text += f"├ 📦 Товар: {i['product']}\n"
        text += f"├ {icon} Статус: {i['status']}\n"
        if i['price']:
            text += f"├ 💰 Цена: {i['price']} ₽\n"
        text += f"└ 📅 Дата: {d}\n\n"
    
    await c.message.answer(text, parse_mode='Markdown')
    await c.answer()

@dp.callback_query(F.data == "check")
async def check_start(c: CallbackQuery, state: FSMContext):
    await c.message.answer("🔍 **Введите номер заказа:**\n\nНапример: `5252`", parse_mode='Markdown')
    await state.set_state(CheckOrder.code)
    await c.answer()

@dp.message(CheckOrder.code)
async def check_go(m: Message, state: FSMContext):
    code = m.text.strip().upper()
    uid = m.from_user.id
    
    wait = await m.answer("⏳ Проверяю...")
    
    order = db.get_order(code)
    
    await wait.delete()
    
    if not order:
        await m.answer(f"❌ Заказ **{code}** не найден", parse_mode='Markdown')
        await state.clear()
        return
    
    if order['user_id'] is None:
        db.bind_order(code, uid)
        msg = "✅ Заказ привязан к твоему аккаунту"
    elif order['user_id'] != uid:
        await m.answer("⛔ Этот заказ принадлежит другому пользователю", parse_mode='Markdown')
        await state.clear()
        return
    else:
        msg = "✅ Заказ найден"
    
    icon = db.get_status_icon(order['status'])
    d = format_date(order['created'])
    text = f"{msg}\n\n"
    text += f"┌ **Заказ №{order['code']}**\n"
    text += f"├ 📦 Товар: {order['product']}\n"
    text += f"├ {icon} Статус: {order['status']}\n"
    if order['price']:
        text += f"├ 💰 Цена: {order['price']} ₽\n"
    text += f"└ 📅 Дата: {d}"
    
    await m.answer(text, parse_mode='Markdown')
    await state.clear()

@dp.callback_query(F.data == "kurs")
async def kurs(c: CallbackQuery):
    currencies = db.get_currency()
    
    text = "💱 **КУРСЫ ВАЛЮТ**\n\n"
    for curr in currencies:
        if curr['name'] == 'CNY':
            text += f"🇨🇳 Китай: {curr['value']} {curr['symbol']}/₽\n"
        elif curr['name'] == 'JPY':
            text += f"🇯🇵 Япония: {curr['value']} {curr['symbol']}/₽\n"
        elif curr['name'] == 'KRW':
            text += f"🇰🇷 Корея: {curr['value']} {curr['symbol']}/₽\n"
        elif curr['name'] == 'USD':
            text += f"🇺🇸 США: {curr['value']} {curr['symbol']}/₽\n"
    
    await c.message.answer(text, parse_mode='Markdown')
    await c.answer()

@dp.callback_query(F.data == "dost")
async def dost(c: CallbackQuery):
    """Отображение тарифов доставки с типами и ценой за кг"""
    delivery = db.get_delivery()
    
    text = "📦 **ТАРИФЫ ДОСТАВКИ**\n\n"
    
    # Группируем по странам
    countries = {}
    for d in delivery:
        if d['country'] not in countries:
            countries[d['country']] = []
        countries[d['country']].append(d)
    
    # Отображаем каждую страну
    for country, options in countries.items():
        if country == "Япония":
            flag = "🇯🇵"
        elif country == "Китай":
            flag = "🇨🇳"
        elif country == "Корея":
            flag = "🇰🇷"
        else:
            flag = "🇺🇸"
        
        text += f"{flag} **{country}**\n"
        
        for opt in options:
            if country == "Китай":
                # Для Китая показываем тип доставки
                text += f"  • {opt['type']}: {opt['price_per_kg']} ₽/кг ({opt['days_min']}-{opt['days_max']} дн)\n"
            else:
                # Для других стран показываем просто сроки
                text += f"  • {opt['days_min']}-{opt['days_max']} дней: {opt['price_per_kg']} ₽/кг\n"
        text += "\n"
    
    await c.message.answer(text, parse_mode='Markdown')
    await c.answer()

@dp.callback_query(F.data == "calc")
async def calc_start(c: CallbackQuery, state: FSMContext):
    text = "🧮 **КАЛЬКУЛЯТОР СТОИМОСТИ**\n\n"
    text += "Я помогу рассчитать стоимость товара в рублях\n"
    text += "Доставка рассчитывается отдельно по тарифам\n\n"
    text += "**Выбери страну:**"
    
    await c.message.answer(text, parse_mode='Markdown', reply_markup=country_menu())
    await state.set_state(Calculate.country)
    await c.answer()

@dp.callback_query(Calculate.country, lambda c: c.data.startswith('cnt_'))
async def calc_country(c: CallbackQuery, state: FSMContext):
    country = c.data.replace('cnt_', '')
    await state.update_data(country=country)
    
    curr_name = COUNTRY_TO[country]
    currencies = db.get_currency()
    curr = next((c for c in currencies if c['name'] == curr_name), None)
    
    if not curr:
        await c.message.answer("❌ Ошибка получения курса")
        await state.clear()
        return
    
    rate = curr['value']
    symbol = curr['symbol']
    
    flag = "🇯🇵" if country == "Япония" else "🇨🇳" if country == "Китай" else "🇰🇷" if country == "Корея" else "🇺🇸"
    text = f"{flag} **{country}**\n\n"
    text += f"💱 Курс: {rate} {symbol}/₽\n\n"
    text += f"✏️ **Введите цену товара в {symbol}:**"
    
    await state.update_data(rate=rate, symbol=symbol)
    await state.set_state(Calculate.price)
    await c.message.answer(text, parse_mode='Markdown')
    await c.answer()

@dp.message(Calculate.price)
async def calc_price(m: Message, state: FSMContext):
    try:
        data = await state.get_data()
        country = data.get('country')
        rate = data.get('rate')
        symbol = data.get('symbol')
        
        if not all([country, rate, symbol]):
            await m.answer("❌ Ошибка. Начни заново", reply_markup=main_menu())
            await state.clear()
            return
        
        price = float(m.text.strip().replace(',', '.'))
        if price <= 0:
            await m.answer("❌ Введите положительное число")
            return
        
        rub = price * rate
        kom = rub * 0.1
        total = rub + kom
        
        flag = "🇯🇵" if country == "Япония" else "🇨🇳" if country == "Китай" else "🇰🇷" if country == "Корея" else "🇺🇸"
        text = "📊 **ИТОГ**\n\n"
        text += f"┌ {flag} **{country}**\n"
        text += f"├ 💰 **Цена:** {price:.2f} {symbol}\n"
        text += f"├ 💱 **Курс:** {rate} {symbol}/₽\n"
        text += f"├ ─────────────────\n"
        text += f"├ **В рублях:** {rub:.2f} ₽\n"
        text += f"├ **Комиссия 10%:** +{kom:.2f} ₽\n"
        text += f"├ ─────────────────\n"
        text += f"└ **ИТОГО:** {total:.2f} ₽\n\n"
        text += "📦 **Доставка оплачивается отдельно**\n"
        text += "Тарифы в разделе 📦 ТАРИФЫ ДОСТАВКИ"
        
        await m.answer(text, parse_mode='Markdown', reply_markup=main_menu())
        await state.clear()
        
    except ValueError:
        await m.answer("❌ Введите число")
    except Exception as e:
        log.error(f"Ошибка: {e}")
        await m.answer("❌ Ошибка расчета", reply_markup=main_menu())
        await state.clear()

async def main():
    print('\n' + '='*40)
    print(' 🤖 SPEND BUY BOT 2.1')
    print('='*40)
    print(' Команда: admin_panel228')
    print(' Тест: 5252, 5252213')
    print(' Новые статусы: 9 этапов')
    print('='*40 + '\n')
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())