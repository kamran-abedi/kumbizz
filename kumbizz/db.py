import sqlite3

conn = sqlite3.connect("kumbizz.db", check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventory (
        telegram_id INTEGER,
        item_name TEXT,
        quantity INTEGER DEFAULT 1,
        PRIMARY KEY (telegram_id, item_name)
    )
    """)
    conn.commit()

def add_user(telegram_id):
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))
    conn.commit()

def get_balance(telegram_id):
    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

def update_balance(telegram_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?", (amount, telegram_id))
    conn.commit()

def add_item(telegram_id, item_name):
    from items import shop_items
    item = shop_items.get(item_name)
    default_hp = item.get("hp", 100) if item else 100

    cursor.execute("""
        INSERT INTO inventory (telegram_id, item_name, quantity, hp)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(telegram_id, item_name)
        DO UPDATE SET quantity = quantity + 1
    """, (telegram_id, item_name, default_hp))
    conn.commit()

def get_inventory(telegram_id):
    cursor.execute("SELECT item_name, quantity, hp FROM inventory WHERE telegram_id=?", (telegram_id,))
    return cursor.fetchall()  # [(item_name, qty, hp), ...]

def xp_required(level):
    return ((level*level)*100) - ((level-1)*100)

def add_xp(telegram_id, xp_amount):
    cursor.execute("SELECT xp, level FROM users WHERE telegram_id=?", (telegram_id,))
    xp, level = cursor.fetchone()
    
    xp += xp_amount
    while xp >= xp_required(level):
        xp -= xp_required(level)
        level += 1
        register_mission_action(telegram_id, "level")
    
    cursor.execute("UPDATE users SET xp=?, level=? WHERE telegram_id=?", (xp, level, telegram_id))
    conn.commit()

def get_level(telegram_id):
    cursor.execute("SELECT level, xp FROM users WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    return result if result else (1, 0)

def has_item(telegram_id, item_name):
    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE telegram_id=? AND item_name=?;
    """, (telegram_id, item_name))
    result = cursor.fetchone()
    return result[0] > 0 if result else False

def add_catch(telegram_id, name, quantity=1):
    cursor.execute("""
        INSERT INTO inventory (telegram_id, item_name, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id, item_name) DO UPDATE SET quantity = quantity + ?
    """, (telegram_id, name, quantity, quantity))
    conn.commit()

def get_best_item_by_type(telegram_id, item_type):
    from items import shop_items
    inventory = get_inventory(telegram_id)
    best_item = None
    best_score = 0

    for name, qty, hp in inventory:  # ← اینجا باید ۳ تا مقدار بگیری
        if qty <= 0 or hp is None or hp <= 0:
            continue
        item = shop_items.get(name)
        if item and item.get("type") == item_type:
            try:
                multiplier = float(item.get("multiplier", 1.0))
                chance = int(item.get("chance", 0))
                score = multiplier * chance
                if score > best_score:
                    best_score = score
                    best_item = (name, item)
            except:
                continue

    return best_item

def reduce_item_hp(telegram_id, item_name, amount):
    cursor.execute("SELECT quantity, hp FROM inventory WHERE telegram_id=? AND item_name=?", (telegram_id, item_name))
    result = cursor.fetchone()
    if not result:
        return

    quantity, current_hp = result
    new_hp = current_hp - amount

    if new_hp <= 0:
        if quantity > 1:
            # یکی از آیتم‌ها خراب شده
            from items import shop_items
            item = shop_items.get(item_name)
            default_hp = item.get("hp", 100) if item else 100
            cursor.execute("""
                UPDATE inventory
                SET quantity = quantity - 1, hp = ?
                WHERE telegram_id=? AND item_name=?
            """, (default_hp, telegram_id, item_name))
        else:
            # فقط یکی بوده، کل آیتم حذف بشه
            cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=?", (telegram_id, item_name))
    else:
        # فقط hp کم می‌شه
        cursor.execute("UPDATE inventory SET hp=? WHERE telegram_id=? AND item_name=?", (new_hp, telegram_id, item_name))

    conn.commit()

def sell_item(telegram_id, item_name, quantity, price_per_unit):
    cursor.execute("SELECT quantity FROM inventory WHERE telegram_id=? AND item_name=?", (telegram_id, item_name))
    result = cursor.fetchone()
    if not result or result[0] < quantity:
        return False

    cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE telegram_id=? AND item_name=?", (quantity, telegram_id, item_name))
    cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=? AND quantity <= 0", (telegram_id, item_name))
    update_balance(telegram_id, price_per_unit * quantity)
    conn.commit()
    return True

def transfer_item(sender_id, receiver_id, item_name, quantity):
    cursor.execute("SELECT quantity FROM inventory WHERE telegram_id=? AND item_name=?", (sender_id, item_name))
    result = cursor.fetchone()
    if not result or result[0] < quantity:
        return False

    # کم کردن از فرستنده
    cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE telegram_id=? AND item_name=?", (quantity, sender_id, item_name))
    cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=? AND quantity <= 0", (sender_id, item_name))

    # اضافه کردن به گیرنده (quantity عدد)
    add_user(receiver_id)
    for _ in range(quantity):
        add_item(receiver_id, item_name)

    conn.commit()
    return True

def give_special_item(telegram_id, item_name):
    add_item(telegram_id, item_name)
    
def get_bank_info(telegram_id):
    cursor.execute("SELECT balance, bank_balance, bank_capacity FROM users WHERE telegram_id=?", (telegram_id,))
    return cursor.fetchone()

def deposit(telegram_id, amount):
    balance, bank_balance, bank_capacity = get_bank_info(telegram_id)

    if amount > balance:
        return False, "موجودی کافی نداری."

    if bank_balance + amount > bank_capacity:
        return False, "ظرفیت حساب بانکیت پره."

    cursor.execute("UPDATE users SET balance = balance - ?, bank_balance = bank_balance + ? WHERE telegram_id=?",
                   (amount, amount, telegram_id))
    conn.commit()
    return True, f"{amount} کوین به حساب بانکیت واریز شد."

def withdraw(telegram_id, amount):
    _, bank_balance, _ = get_bank_info(telegram_id)

    if amount > bank_balance:
        return False, "موجودی حساب بانکیت کافی نیست."

    cursor.execute("UPDATE users SET bank_balance = bank_balance - ?, balance = balance + ? WHERE telegram_id=?",
                   (amount, amount, telegram_id))
    conn.commit()
    return True, f"{amount} کوین از حساب بانکیت برداشت شد."

def upgrade_bank(telegram_id, cost):
    cursor.execute("SELECT balance, bank_capacity FROM users WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    if not result or result[0] < cost:
        return False, "موجودی کافی نداری."

    new_capacity = result[1] + (cost * 10)
    cursor.execute("""
        UPDATE users
        SET balance = balance - ?, bank_capacity = ?
        WHERE telegram_id = ?
    """, (cost, new_capacity, telegram_id))
    conn.commit()
    return True, f"ظرفیت حساب بانکیت {cost * 10} واحد افزایش پیدا کرد!"

import datetime

def apply_daily_interest(telegram_id):
    cursor.execute("SELECT bank_balance, last_interest FROM users WHERE telegram_id=?", (telegram_id,))
    result = cursor.fetchone()
    if not result:
        return False, "کاربر پیدا نشد."

    bank_balance, last_interest = result
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    if last_interest == today:
        return False, "امروز سودت رو دریافت کردی."

    interest = int(bank_balance * 0.02)
    if interest <= 0:
        return False, "حساب بانکی‌ات خالیه!"

    cursor.execute("""
        UPDATE users
        SET bank_balance = bank_balance + ?, last_interest = ?
        WHERE telegram_id = ?
    """, (interest, today, telegram_id))
    conn.commit()
    return True, f"سود روزانه به حسابت واریز شد: {interest} کوین!"

def init_rob_table():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rob_cooldown (
            telegram_id INTEGER PRIMARY KEY,
            last_rob TEXT
        )
    """)
    conn.commit()

import datetime

def can_rob(telegram_id):
    cursor.execute("SELECT last_rob FROM rob_cooldown WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()

    if not row:
        return True  # اولین بارشه

    last_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.utcnow()
    diff = now - last_time

    return diff.total_seconds() >= 86400  # 24 ساعت

def register_rob(telegram_id):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO rob_cooldown (telegram_id, last_rob)
        VALUES (?, ?)
    """, (telegram_id, now))
    conn.commit()

def consume_item(telegram_id, item_name):
    cursor.execute("""
        UPDATE inventory SET quantity = quantity - 1
        WHERE telegram_id = ? AND item_name = ?
    """, (telegram_id, item_name))
    cursor.execute("""
        DELETE FROM inventory WHERE telegram_id = ? AND item_name = ? AND quantity <= 0
    """, (telegram_id, item_name))
    conn.commit()

def buy_mine(telegram_id):
    cursor.execute("SELECT balance, has_mine FROM users WHERE telegram_id=?", (telegram_id,))
    balance, has_mine = cursor.fetchone()

    if has_mine:
        return False, "تو همین حالا هم یه معدن داری!"

    price = 15000
    if balance < price:
        return False, "پول کافی برای خرید معدن نداری."

    cursor.execute("UPDATE users SET balance = balance - ?, has_mine = 1 WHERE telegram_id=?", (price, telegram_id))
    conn.commit()
    return True, "معدن با موفقیت خریداری شد! حالا می‌تونی هر ۶ ساعت یکبار دستور /mine رو بزنی."

import random, datetime
from mine_items import mine_drops

def mine_resources(telegram_id):
    cursor.execute("SELECT has_mine, last_mine FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False, "تو هنوز معدنی نخریدی!"

    last_mine = row[1]
    now = datetime.datetime.utcnow()
    cooldown = datetime.timedelta(hours=6)

    if last_mine:
        last_time = datetime.datetime.strptime(last_mine, "%Y-%m-%d %H:%M:%S")
        if now - last_time < cooldown:
            remaining = cooldown - (now - last_time)
            mins = int(remaining.total_seconds() // 60)
            return False, f"باید {mins} دقیقه دیگه صبر کنی تا دوباره بتونی استخراج کنی."

    # استخراج تصادفی آیتم
    choices = []
    for drop in mine_drops:
        choices.extend([drop["name"]] * int(drop["chance"] * 10))  # دقت بیشتر
    result = random.choice(choices)

    from items import shop_items
    if result not in shop_items:
        shop_items[result] = {
            "price": 0,
            "type": "material",
            "description": f"منبع معدنی: {result}"
        }

    add_item(telegram_id, result)

    cursor.execute("UPDATE users SET last_mine = ? WHERE telegram_id=?", (now.strftime("%Y-%m-%d %H:%M:%S"), telegram_id))
    conn.commit()
    return True, f"تو از معدنت یک «{result}» استخراج کردی!"

def upgrade_mine(telegram_id):
    cursor.execute("SELECT has_mine, mine_level, balance FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False, "اول باید معدنی داشته باشی!"

    level, balance = row[1], row[2]
    if level >= 5:
        return False, "معدنت به بالاترین سطح رسیده."

    cost = 15000 + (level * 5000)
    if balance < cost:
        return False, f"برای ارتقاء به سطح {level + 1}، به {cost} کوین نیاز داری."

    cursor.execute("UPDATE users SET balance = balance - ?, mine_level = mine_level + 1 WHERE telegram_id=?",
                   (cost, telegram_id))
    conn.commit()
    return True, f"معدنت به سطح {level + 1} ارتقاء یافت!"

from mine_items import mine_settings

def mine_resources(telegram_id):
    cursor.execute("SELECT has_mine, last_mine, mine_level FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return False, "تو هنوز معدنی نخریدی!"

    last_mine = row[1]
    mine_level = row[2] or 1
    settings = mine_settings.get(mine_level, mine_settings[1])

    now = datetime.datetime.utcnow()
    cooldown = datetime.timedelta(hours=settings["cooldown"])

    if last_mine:
        last_time = datetime.datetime.strptime(last_mine, "%Y-%m-%d %H:%M:%S")
        if now - last_time < cooldown:
            remaining = cooldown - (now - last_time)
            mins = int(remaining.total_seconds() // 60)
            return False, f"باید {mins} دقیقه دیگه صبر کنی تا دوباره استخراج کنی."

    # استخراج چندتایی
    from mine_items import mine_drops
    from items import shop_items
    collected = []

    choices = []
    for drop in mine_drops:
        choices.extend([drop["name"]] * int(drop["chance"] * 10))

    for _ in range(settings["count"]):
        result = random.choice(choices)
        add_item(telegram_id, result)
        collected.append(result)

    cursor.execute("UPDATE users SET last_mine = ? WHERE telegram_id=?", (now.strftime("%Y-%m-%d %H:%M:%S"), telegram_id))
    conn.commit()
    player_level, ksshr = get_level(telegram_id)
    xp_gain = 10 * mine_level * player_level
    add_xp(telegram_id, xp_gain)
    result_text = "\n".join(f"• {item}" for item in collected)
    return True, f"از معدنت استخراج کردی:\n{result_text} +{xp_gain}XP"

import datetime
from db import cursor
from mine_items import mine_settings, mine_drops

def get_mine_status(telegram_id):
    cursor.execute("SELECT has_mine, mine_level, last_mine FROM users WHERE telegram_id=?", (telegram_id,))
    row = cursor.fetchone()

    if not row:
        return False, "❌ شما هنوز ثبت نشده‌اید. لطفاً با /start شروع کنید."

    has_mine, mine_level, last_mine = row
    if not has_mine:
        return False, "⛏ شما هنوز معدن ندارید. برای شروع باید معدن بخرید یا ارتقا بدی."

    # اطلاعات سطح
    mine_info = mine_settings.get(mine_level)
    if not mine_info:
        return False, "❌ اطلاعات سطح معدن شما یافت نشد."

    cooldown_hours = mine_info["cooldown"]
    cooldown = datetime.timedelta(hours=cooldown_hours)
    now = datetime.datetime.utcnow()

    # محاسبه زمان باقی‌مانده
    if last_mine:
        try:
            last_time = datetime.datetime.strptime(last_mine, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, "❌ خطا در ثبت زمان آخرین استخراج."
        delta = now - last_time
        if delta < cooldown:
            remaining = cooldown - delta
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds // 60) % 60
            status = f"⏳ {hours} ساعت و {minutes} دقیقه تا استخراج بعدی"
        else:
            status = "✅ آماده استخراج"
    else:
        status = "✅ آماده استخراج"

    # محصولات نمایشی
    available_drops = []
    for drop in mine_drops:
        chance = drop.get("chance", 0)
        if chance > 0:
            available_drops.append(drop["name"])

    drops_text = ", ".join(available_drops)

    text = (
        f"⛏ <b>وضعیت معدن شما:</b>\n"
        f"• سطح: {mine_level}\n"
        f"• ظرفیت برداشت: {mine_info['count']} آیتم\n"
        f"• وضعیت: {status}\n"
        f"• محصولات ممکن: {drops_text}"
    )

    return True, text

def effects(effect, now, telegram_id, uses_left, expires_at):
    if "uses" in effect:
        uses_left = effect["uses"]
    elif "duration_minutes" in effect:
        expires_at = (now + datetime.timedelta(minutes=effect["duration_minutes"])).strftime("%Y-%m-%d %H:%M:%S")
    elif "duration_days" in effect:
        expires_at = (now + datetime.timedelta(days=effect["duration_days"])).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT OR REPLACE INTO food_effects (telegram_id, effect_type, value, uses_left, expires_at)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, effect["type"], effect.get("multiplier", effect.get("bonus", effect.get("bonus_percent", 0))), uses_left, expires_at))
    conn.commit()

def get_active_effect(telegram_id, effect_type):
    cursor.execute("""
        SELECT value, uses_left, expires_at FROM food_effects
        WHERE telegram_id=? AND effect_type=?
    """, (telegram_id, effect_type))
    row = cursor.fetchone()
    if not row:
        return None

    val, uses, expires = row
    if expires:
        now = datetime.datetime.utcnow()
        exp_time = datetime.datetime.strptime(expires, "%Y-%m-%d %H:%M:%S")
        if now > exp_time:
            cursor.execute("DELETE FROM food_effects WHERE telegram_id=? AND effect_type=?", (telegram_id, effect_type))
            conn.commit()
            return None

    return {"value": val, "uses_left": uses}

def set_cooldown(telegram_id, command):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT OR REPLACE INTO cooldowns (telegram_id, command, last_used)
        VALUES (?, ?, ?)
    """, (telegram_id, command, now))
    conn.commit()

import datetime

def is_on_cooldown(telegram_id, command, cooldown_minutes):
    cursor.execute("SELECT last_used FROM cooldowns WHERE telegram_id=? AND command=?", (telegram_id, command))
    row = cursor.fetchone()

    if not row:
        return False  # هیچ‌وقت اجرا نشده

    last_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.utcnow()
    if now - last_time < datetime.timedelta(minutes=cooldown_minutes):
        return True
    return False

def buy_farm_unit(telegram_id, unit_type):
    from farm_data import farm_data
    data = farm_data.get(unit_type)
    if not data:
        return False, "چنین واحد مزرعه‌ای وجود نداره."

    price = data["price"]

    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
    balance = cursor.fetchone()[0]

    if balance < price:
        return False, "پول کافی نداری."

    cursor.execute("""
        INSERT INTO farm_units (telegram_id, unit_type, quantity, last_harvest)
        VALUES (?, ?, 1, NULL)
        ON CONFLICT(telegram_id, unit_type) DO UPDATE SET quantity = quantity + 1
    """, (telegram_id, unit_type))

    cursor.execute("UPDATE users SET balance = balance - ? WHERE telegram_id=?", (price, telegram_id))
    conn.commit()
    return True, f"یک واحد «{unit_type}» به مزرعه‌ات اضافه شد!"

def harvest_farm(telegram_id):
    from farm_data import farm_data
    cursor.execute("SELECT unit_type, quantity, last_harvest FROM farm_units WHERE telegram_id=?", (telegram_id,))
    rows = cursor.fetchall()
    now = datetime.datetime.utcnow()

    if not rows:
        return False, "هیچ واحد مزرعه‌ای نداری."

    total_collected = []
    xp_gain = 0

    for unit_type, qty, last in rows:
        unit_info = farm_data.get(unit_type)
        if not unit_info:
            continue

        cooldown = datetime.timedelta(hours=unit_info["interval_hours"])

        if last:
            last_time = datetime.datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
            if now - last_time < cooldown:
                continue

        product = unit_info["product"]
        for i in range(qty):
            add_item(telegram_id, product)
        total_collected.append(f"{product} × {qty}")

        cursor.execute("""
            UPDATE farm_units SET last_harvest = ?
            WHERE telegram_id=? AND unit_type=?
        """, (now.strftime("%Y-%m-%d %H:%M:%S"), telegram_id, unit_type))

    if not total_collected:
        return False, "هنوز چیزی برای برداشت آماده نیست."

    # حالا xp بده بعد از حلقه
    farmer_level, _ = get_level(telegram_id) 
    xp_gain += 10 * farmer_level
    add_xp(telegram_id, xp_gain)

    conn.commit()
    result_text = "\n".join(f"• {line}" for line in total_collected)
    return True, f"🌾 برداشت موفق:\n{result_text}"

def farm_status(telegram_id):
    
    # اطلاعات مزرعه کاربر از دیتابیس بگیر
    cursor.execute("SELECT unit_type, quantity, last_harvest FROM farm_units WHERE telegram_id=?", (telegram_id,))
    rows = cursor.fetchall()

    if not rows:
        return "🚜 شما هنوز هیچ واحد مزرعه‌ای ندارید."

    # پردازش اطلاعات
    now = datetime.datetime.utcnow()
    from farm_data import farm_data  # داده‌های واحدهای مزرعه
    response = "🌾 <b>وضعیت مزرعه شما:</b>\n"
    for unit_type, qty, last_harvest in rows:
        unit_info = farm_data.get(unit_type)
        if not unit_info:
            continue

        product = unit_info["product"]
        interval_hours = unit_info["interval_hours"]

        # محاسبه زمان باقی‌مانده
        cooldown = datetime.timedelta(hours=interval_hours)
        if last_harvest:
            last_time = datetime.datetime.strptime(last_harvest, "%Y-%m-%d %H:%M:%S")
            time_remaining = max(cooldown - (now - last_time), datetime.timedelta(0))
            time_left = f"{time_remaining.seconds // 3600} ساعت و {(time_remaining.seconds // 60) % 60} دقیقه"
        else:
            time_left = "آماده برداشت"

        response += f"• {unit_type} × {qty} (محصول: {product})\n"
        response += f"  ⏳ زمان باقی‌مانده: {time_left}\n"
    return response
        
def list_in_market(telegram_id, item_name, price):

    cursor.execute("""
        INSERT INTO market (seller_id, item_name, quantity, price)
        VALUES (?, ?, 1, ?)
    """, (telegram_id, item_name, price))
    conn.commit()

def get_market_list(filter_text=None):
    filter_clause = ""
    params = []

    if filter_text:
        if filter_text.startswith("seller:"):
            try:
                seller_id = int(filter_text.split("seller:")[1])
                filter_clause = "WHERE seller_id = ?"
                params.append(seller_id)
            except:
                return False, "فرمت seller:آیدی درست نیست."
        else:
            filter_clause = "WHERE item_name LIKE ?"
            params.append(f"%{filter_text}%")

    query = f"""
        SELECT id, item_name, price, seller_id FROM market
        {filter_clause}
        ORDER BY id ASC
        LIMIT 10
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    return True, rows

def trade_from_market(telegram_id, trade_id):
    cursor.execute("SELECT item_name, price, seller_id FROM market WHERE id=?", (trade_id,))
    row = cursor.fetchone()
    if not row:
        return False, "آگهی پیدا نشد."

    item, price, seller = row

    if telegram_id == seller:
        return False, "نمی‌تونی آیتم خودتو بخری!"

    cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
    balance = cursor.fetchone()[0]
    if balance < price:
        return False, "پول کافی برای خرید نداری."

    # انتقال
    update_balance(telegram_id, -price)
    update_balance(seller, price)
    add_item(telegram_id, item)

    cursor.execute("DELETE FROM market WHERE id=?", (trade_id,))
    conn.commit()

    return True, f"آیتم «{item}» رو با {price} کوین خریدی!"

def cancel_market_item(telegram_id, trade_id):
    cursor.execute("SELECT item_name, seller_id FROM market WHERE id=?", (trade_id,))
    row = cursor.fetchone()
    if not row:
        return False, "آگهی پیدا نشد."

    item, seller = row
    if seller != telegram_id:
        return False, "فقط فروشنده می‌تونه آگهی رو حذف کنه."

    add_item(telegram_id, item)
    cursor.execute("DELETE FROM market WHERE id=?", (trade_id,))
    conn.commit()

    return True, f"آگهی مربوط به «{item}» حذف شد و آیتم بهت برگشت."

def select_daily_missions(n=3):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
    if cursor.fetchone():
        return  # امروز قبلاً ثبت شده

    cursor.execute("SELECT id FROM missions_pool")
    all_ids = [row[0] for row in cursor.fetchall()]
    selected = random.sample(all_ids, min(n, len(all_ids)))
    ids_str = ",".join(map(str, selected))
    cursor.execute("INSERT INTO daily_missions (day, mission_ids) VALUES (?, ?)", (today, ids_str))
    conn.commit()

def register_mission_action(telegram_id, action_type):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
    row = cursor.fetchone()
    if not row:
        return

    mission_ids = map(int, row[0].split(","))
    for mid in mission_ids:
        cursor.execute("SELECT action, target_value FROM missions_pool WHERE id=?", (mid,))
        m = cursor.fetchone()
        if not m:
            continue
        act, target = m
        if act != action_type:
            continue

        # ثبت پیشرفت
        cursor.execute("""
            INSERT OR IGNORE INTO user_mission_progress (telegram_id, mission_id)
            VALUES (?, ?)
        """, (telegram_id, mid))
        cursor.execute("""
            UPDATE user_mission_progress
            SET progress = progress + 1
            WHERE telegram_id = ? AND mission_id = ? AND completed = 0
        """, (telegram_id, mid))

        # چک اتمام
        cursor.execute("SELECT progress FROM user_mission_progress WHERE telegram_id=? AND mission_id=?", (telegram_id, mid))
        prog = cursor.fetchone()[0]
        if prog >= target:
            cursor.execute("UPDATE user_mission_progress SET completed = 1 WHERE telegram_id=? AND mission_id=?", (telegram_id, mid))
    conn.commit()

def get_user_missions(telegram_id):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
    row = cursor.fetchone()
    if not row:
        return []

    missions = []
    for mid in map(int, row[0].split(",")):
        cursor.execute("SELECT description, target_value FROM missions_pool WHERE id=?", (mid,))
        desc, target = cursor.fetchone()

        cursor.execute("SELECT progress, completed FROM user_mission_progress WHERE telegram_id=? AND mission_id=?", (telegram_id, mid))
        pr = cursor.fetchone()
        progress = pr[0] if pr else 0
        completed = pr[1] if pr else 0

        missions.append({
            "id": mid,
            "desc": desc,
            "progress": progress,
            "target": target,
            "completed": completed
        })

    return missions

def claim_mission_rewards(telegram_id):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")

    # دریافت لیست ماموریت‌های امروز
    cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
    row = cursor.fetchone()
    if not row:
        return False, "هیچ ماموریتی برای امروز ثبت نشده."

    mission_ids = list(map(int, row[0].split(",")))
    total_claimed = 0
    total_reward = 0
    xp_reward = 0

    for mid in mission_ids:
        # چک تکمیل بودن و نگرفتن جایزه
        cursor.execute("""
            SELECT completed FROM user_mission_progress
            WHERE telegram_id=? AND mission_id=?
        """, (telegram_id, mid))
        row = cursor.fetchone()
        if not row or not row[0]:
            continue  # کامل نشده

        cursor.execute("""
            SELECT claimed FROM mission_rewards
            WHERE telegram_id=? AND day=? AND mission_id=?
        """, (telegram_id, today, mid))
        row = cursor.fetchone()
        if row and row[0]:
            continue  # جایزه گرفته شده

        # ثبت جایزه
        cursor.execute("""
            INSERT OR REPLACE INTO mission_rewards
            (telegram_id, day, mission_id, claimed)
            VALUES (?, ?, ?, 1)
        """, (telegram_id, today, mid))

        reward = 400  # مقدار ثابت یا قابل تنظیم
        xp = 20
        update_balance(telegram_id, reward)
        add_xp(telegram_id, xp)

        total_claimed += 1
        total_reward += reward
        xp_reward += xp

    # بررسی جایزه ویژه
    if total_claimed == len(mission_ids):
        cursor.execute("""
            SELECT claimed FROM mission_rewards
            WHERE telegram_id=? AND day=? AND mission_id=-1
        """, (telegram_id, today))
        if not row or not row[0]:
            cursor.execute("""
                INSERT OR REPLACE INTO mission_rewards
                (telegram_id, day, mission_id, claimed)
                VALUES (?, ?, -1, 1)
            """, (telegram_id, today))
            bonus = 1500
            xp_bonus = 150
            update_balance(telegram_id, bonus)
            add_xp(telegram_id, xp_bonus)
            total_reward += bonus
            xp_reward += xp_bonus

    conn.commit()
    if total_claimed == 0:
        return False, "هنوز هیچ ماموریتی رو کامل نکردی یا جایزه‌شو گرفتی."
    return True, f"🎉 {total_claimed} ماموریت کامل شد!\n🏆 {total_reward} کوین + {xp_reward} XP گرفتی!"

def ensure_user(telegram_id):
    cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))
    conn.commit()
