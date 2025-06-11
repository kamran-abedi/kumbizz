import sqlite3

conn = sqlite3.connect("kumbizz.db", check_same_thread=False)

def init_db():
    with conn:
        cursor = conn.cursor()
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

def get_data():
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM businesses")
        biz_count = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(balance) FROM users")
        total_balance = cursor.fetchone()[0]

    msg = (
        f"📈 آمار بازی:\n"
        f"👥 کاربران: {users}\n"
        f"🏭 بیزینس‌ها: {biz_count}\n"
        f"💰 مجموع کامکوین‌ها: {total_balance:,}"
    )
    return msg

def register_invite(invited, inviter):
    with conn:
        conn.execute("INSERT OR IGNORE INTO invites (invited_id, inviter_id) VALUES (?, ?)", (invited, inviter))

def increment_invite_count(inviter):
    with conn:
        conn.execute("UPDATE invites SET invite_count = invite_count + 1 WHERE telegram_id=?", (inviter,))

def user_exists(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE telegram_id=?", (telegram_id,))
        return cursor.fetchone() is not None
    
def get_invite_count(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT invite_count FROM invites WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        return row[0] if row else 0

def add_user(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))

def get_balance(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
        result = cursor.fetchone()
        return result[0] if result else 0

def update_balance(telegram_id, amount):
    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?", (amount, telegram_id))

def add_item(telegram_id, item_name):
    from items import shop_items
    item = shop_items.get(item_name)
    default_hp = item.get("hp", 100) if item else 100

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory (telegram_id, item_name, quantity, hp)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(telegram_id, item_name)
            DO UPDATE SET quantity = quantity + 1
        """, (telegram_id, item_name, default_hp))
        

def get_inventory(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, quantity, hp FROM inventory WHERE telegram_id=?", (telegram_id,))
        return cursor.fetchall()  # [(item_name, qty, hp), ...]

def xp_required(level):
    return ((level*level)*100) - ((level-1)*100)

def add_xp(telegram_id, xp_amount):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM users WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()

    if not row:
        # اگر کاربر وجود نداشت، یه مقدار پیش‌فرض تعریف کن
        xp, level = 0, 1
    else:
        xp, level = row

    xp += xp_amount
    while xp >= xp_required(level):
        xp -= xp_required(level)
        level += 1
        register_mission_action(telegram_id, "level")

    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET xp=?, level=? WHERE telegram_id=?", (xp, level, telegram_id))

def get_level(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT level, xp FROM users WHERE telegram_id=?", (telegram_id,))
        result = cursor.fetchone()
        return result if result else (1, 0)

def has_item(telegram_id, item_name):
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT quantity FROM inventory
            WHERE telegram_id=? AND item_name=?;
        """, (telegram_id, item_name))
        result = cursor.fetchone()
        return result[0] > 0 if result else False

def add_catch(telegram_id, name, quantity=1):
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO inventory (telegram_id, item_name, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id, item_name) DO UPDATE SET quantity = quantity + ?
        """, (telegram_id, name, quantity, quantity))

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
    with conn:
        cursor = conn.cursor()
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
            with conn:
                conn.execute("""
                    UPDATE inventory
                    SET quantity = quantity - 1, hp = ?
                    WHERE telegram_id=? AND item_name=?
                """, (default_hp, telegram_id, item_name))
        else:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=?", (telegram_id, item_name))
    else:
        with conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE inventory SET hp=? WHERE telegram_id=? AND item_name=?", (new_hp, telegram_id, item_name))

def sell_item(telegram_id, item_name, quantity, price_per_unit):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM inventory WHERE telegram_id=? AND item_name=?", (telegram_id, item_name))
        result = cursor.fetchone()
        if not result or result[0] < quantity:
            return False

        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE telegram_id=? AND item_name=?", (quantity, telegram_id, item_name))
        cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=? AND quantity <= 0", (telegram_id, item_name))
    update_balance(telegram_id, price_per_unit * quantity)
    return True

def transfer_item(sender_id, receiver_id, item_name, quantity):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT quantity FROM inventory WHERE telegram_id=? AND item_name=?", (sender_id, item_name))
        result = cursor.fetchone()
        if not result or result[0] < quantity:
            return False
                
        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE telegram_id=? AND item_name=?", (quantity, sender_id, item_name))
        cursor.execute("DELETE FROM inventory WHERE telegram_id=? AND item_name=? AND quantity <= 0", (sender_id, item_name))

    # اضافه کردن به گیرنده (quantity عدد)
    add_user(receiver_id)
    for _ in range(quantity):
        add_item(receiver_id, item_name)

    return True

def give_special_item(telegram_id, item_name):
    add_item(telegram_id, item_name)
    
def get_bank_info(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance, bank_balance, bank_capacity FROM users WHERE telegram_id=?", (telegram_id,))
        return cursor.fetchone()

def deposit(telegram_id, amount):
    balance, bank_balance, bank_capacity = get_bank_info(telegram_id)

    if amount > balance:
        return False, "موجودی کافی نداری."

    if bank_balance + amount > bank_capacity:
        return False, "ظرفیت حساب بانکیت پره."

    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ?, bank_balance = bank_balance + ? WHERE telegram_id=?",
                       (amount, amount, telegram_id))
        
    return True, f"{amount} KUM⛀ به حساب بانکیت واریز شد."

def withdraw(telegram_id, amount):
    _, bank_balance, _ = get_bank_info(telegram_id)

    if amount > bank_balance:
        return False, "موجودی حساب بانکیت کافی نیست."

    with conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET bank_balance = bank_balance - ?, balance = balance + ? WHERE telegram_id=?",
                       (amount, amount, telegram_id))

    return True, f"{amount} KUM⛀ از حساب بانکیت برداشت شد."

def upgrade_bank(telegram_id, cost):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance, bank_capacity FROM users WHERE telegram_id=?", (telegram_id,))
        result = cursor.fetchone()
        if not result or result[0] < cost:
            return False, "موجودی کافی نداری."

    new_capacity = result[1] + (cost * 10)
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET balance = balance - ?, bank_capacity = ?
            WHERE telegram_id = ?
        """, (cost, new_capacity, telegram_id))

    return True, f"ظرفیت حساب بانکیت {cost * 10} واحد افزایش پیدا کرد!"

import datetime

def apply_daily_interest(telegram_id):
    with conn:
        cursor = conn.cursor()
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

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET bank_balance = bank_balance + ?, last_interest = ?
            WHERE telegram_id = ?
        """, (interest, today, telegram_id))
        
    return True, f"سود روزانه به حسابت واریز شد: {interest} KUM⛀!"

def init_rob_table():
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rob_cooldown (
                telegram_id INTEGER PRIMARY KEY,
                last_rob TEXT
            )
        """)

import datetime

def can_rob(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_rob FROM rob_cooldown WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()

        if not row:
            return True  # اولین بارشه

        last_time = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
    now = datetime.datetime.utcnow()
    diff = now - last_time

    return diff.total_seconds() >= 14400  # 4 ساعت

def register_rob(telegram_id):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO rob_cooldown (telegram_id, last_rob)
            VALUES (?, ?)
        """, (telegram_id, now))


def consume_item(telegram_id, item_name):
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE inventory SET quantity = quantity - 1
            WHERE telegram_id = ? AND item_name = ?
        """, (telegram_id, item_name))
        cursor.execute("""
            DELETE FROM inventory WHERE telegram_id = ? AND item_name = ? AND quantity <= 0
        """, (telegram_id, item_name))

def buy_mine(telegram_id):
    with conn:
        cursor = conn.cursor()
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

def upgrade_mine(telegram_id, current_level):
    if current_level >= 6:
        return False, "⛏ معدن شما در بالاترین سطحه."

    next_level = current_level + 1
    price = mine_data[next_level]["level_price"]
    balance = get_balance(telegram_id)

    if balance < price:
        return False, f"💰 برای ارتقا به سطح {next_level} نیاز به {price} سکه داری."

    update_balance(telegram_id, -price)
    with conn:
        conn.execute("UPDATE users SET mine_level=? WHERE telegram_id=?", (next_level, telegram_id))
    return True, f"✅ معدن شما به سطح {next_level} ارتقا یافت!"

import random
import time
from mine_items import mine_data, mine_drops

def perform_mine(telegram_id, mine_level, last_mine_time):
    now = int(time.time())
    cooldown_hours = mine_data[mine_level]["cooldown"]
    cooldown_seconds = cooldown_hours * 3600

    if now - last_mine_time < cooldown_seconds:
        remaining = cooldown_seconds - (now - last_mine_time)
        return False, f"⛏ هنوز {int(remaining // 60)} دقیقه تا نوبت بعدی مونده."

    # فیلتر منابع بر اساس سطح
    available_drops = [drop for drop in mine_drops if drop["level_required"] <= mine_level]
    total_chance = sum(d["chance"] for d in available_drops)

    mined_items = []
    for _ in range(mine_data[mine_level]["count"]):
        pick = random.randint(1, total_chance)
        current = 0
        for drop in available_drops:
            current += drop["chance"]
            if pick <= current:
                mined_items.append(drop["name"])
                add_item(telegram_id, drop["name"])
                break

    # بروزرسانی زمان آخرین استخراج
    with conn:
        conn.execute("UPDATE users SET last_mine=? WHERE telegram_id=?", (now, telegram_id))

    user_level, _ = get_level(telegram_id)
    xp_gain = 10 * user_level * mine_level
    add_xp(telegram_id, xp_gain)

    result_text = "\n".join(f"• {item}" for item in mined_items)
    return True, f"✅ استخراج موفق:\n{result_text}\n+{xp_gain}XP"

import datetime
from mine_items import mine_data, mine_drops

def get_mine_status(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mine_level, last_mine FROM users WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        if not row:
            return 1, 0  # سطح 1 و زمان پیش‌فرض
        level, last = row
        return level, int(last or 0)

def effects(effect, now, telegram_id, uses_left, expires_at):
    if "uses" in effect:
        uses_left = effect["uses"]
    elif "duration_minutes" in effect:
        expires_at = (now + datetime.timedelta(minutes=effect["duration_minutes"])).strftime("%Y-%m-%d %H:%M:%S")
    elif "duration_days" in effect:
        expires_at = (now + datetime.timedelta(days=effect["duration_days"])).strftime("%Y-%m-%d %H:%M:%S")

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO food_effects (telegram_id, effect_type, value, uses_left, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, effect["type"], effect.get("multiplier", effect.get("bonus", effect.get("bonus_percent", 0))), uses_left, expires_at))
        

def get_active_effect(telegram_id, effect_type):
    with conn:
        cursor = conn.cursor()
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
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM food_effects WHERE telegram_id=? AND effect_type=?", (telegram_id, effect_type))
            return None

    return {"value": val, "uses_left": uses}

import time

def get_cooldown(telegram_id, action):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT cooldown_until FROM cooldowns WHERE telegram_id=? AND action=?", (telegram_id, action))
        row = cursor.fetchone()
        return row[0] if row else 0

def set_cooldown(telegram_id, action, cooldown_seconds):
    cooldown_until = int(time.time()) + cooldown_seconds
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cooldowns (telegram_id, action, cooldown_until)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id, action) DO UPDATE SET cooldown_until=excluded.cooldown_until
        """, (telegram_id, action, cooldown_until))

def buy_farm_unit(telegram_id, unit_type, qty):
    from farm_data import farm_data
    data = farm_data.get(unit_type)
    if not data:
        return False, "چنین واحد مزرعه‌ای وجود نداره."

    price = data["price"]*qty

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
        balance = cursor.fetchone()[0]

    if balance < price:
        return False, "پول کافی نداری."
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO farm_units (telegram_id, unit_type, quantity, last_harvest)
            VALUES (?, ?, ?, NULL)
            ON CONFLICT(telegram_id, unit_type) DO UPDATE SET quantity = quantity + ?
        """, (telegram_id, unit_type, qty, qty))
    
        cursor.execute("UPDATE users SET balance = balance - ? WHERE telegram_id=?", (price, telegram_id))
    return True, f"{qty} واحد «{unit_type}» به مزرعه‌ات اضافه شد!"

def harvest_farm(telegram_id):
    from farm_data import farm_data
    with conn:
        cursor = conn.cursor()
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
            xp_gain += 10
        total_collected.append(f"{product} × {qty}")

        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE farm_units SET last_harvest = ?
                WHERE telegram_id=? AND unit_type=?
            """, (now.strftime("%Y-%m-%d %H:%M:%S"), telegram_id, unit_type))        

    if not total_collected:
        return False, "هنوز چیزی برای برداشت آماده نیست."

    # حالا xp بده بعد از حلقه
    farmer_level, _ = get_level(telegram_id) 
    add_xp(telegram_id, xp_gain)

    result_text = "\n".join(f"• {line}" for line in total_collected)
    return True, f"🌾 برداشت موفق:\n{result_text} +{xp_gain}XP"

def farm_status(telegram_id):
    with conn:
        cursor = conn.cursor()
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
    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO market (seller_id, item_name, quantity, price)
            VALUES (?, ?, 1, ?)
        """, (telegram_id, item_name, price))

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
    with conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
    return True, rows

def trade_from_market(telegram_id, trade_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, price, seller_id FROM market WHERE id=?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            return False, "آگهی پیدا نشد."

    item, price, seller = row

    if telegram_id == seller:
        return False, "نمی‌تونی آیتم خودتو بخری!"

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,))
        balance = cursor.fetchone()[0]
        if balance < price:
            return False, "پول کافی برای خرید نداری."

    # انتقال
    update_balance(telegram_id, -price)
    update_balance(seller, price)
    add_item(telegram_id, item)

    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM market WHERE id=?", (trade_id,))

    return True, f"آیتم «{item}» رو با {price} کوین خریدی!"

def cancel_market_item(telegram_id, trade_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, seller_id FROM market WHERE id=?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            return False, "آگهی پیدا نشد."

    item, seller = row
    if seller != telegram_id:
        return False, "فقط فروشنده می‌تونه آگهی رو حذف کنه."

    add_item(telegram_id, item)
    with conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM market WHERE id=?", (trade_id,))

    return True, f"آگهی مربوط به «{item}» حذف شد و آیتم بهت برگشت."

def select_daily_missions(n=3):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
        if cursor.fetchone():
            return  # امروز قبلاً ثبت شده
    
        cursor.execute("SELECT id FROM missions_pool")
        all_ids = [row[0] for row in cursor.fetchall()]
        selected = random.sample(all_ids, min(n, len(all_ids)))
        ids_str = ",".join(map(str, selected))
        cursor.execute("INSERT INTO daily_missions (day, mission_ids) VALUES (?, ?)", (today, ids_str))

def register_mission_action(telegram_id, action_type):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
        row = cursor.fetchone()
        if not row:
            return

    mission_ids = map(int, row[0].split(","))
    for mid in mission_ids:
        with conn:
            cursor = conn.cursor()
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

def get_user_missions(telegram_id):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    with conn:
        cursor = conn.cursor()
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

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT mission_ids FROM daily_missions WHERE day=?", (today,))
        row = cursor.fetchone()
        if not row:
            return False, "هیچ ماموریتی برای امروز ثبت نشده."

    mission_ids = list(map(int, row[0].split(",")))
    total_claimed = 0
    total_reward = 0
    xp_reward = 0

    for mid in mission_ids:
        with conn:
            cursor = conn.cursor()
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
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT claimed FROM mission_rewards
                WHERE telegram_id=? AND day=? AND mission_id=-1
            """, (telegram_id, today))
        if not row or not row[0]:
            with conn:
                cursor = conn.cursor()
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

    if total_claimed == 0:
        return False, "هنوز هیچ ماموریتی رو کامل نکردی یا جایزه‌شو گرفتی."
    return True, f"🎉 {total_claimed} ماموریت کامل شد!\n🏆 {total_reward} کوین + {xp_reward} XP گرفتی!"

def ensure_user(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,))

import datetime

def can_claim_reward(telegram_id, reward_type):
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT last_{reward_type} FROM users WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        now = datetime.datetime.utcnow()

        if not row or not row[0]:
            return True

    last_time = datetime.datetime.strptime(row[0], "%Y-%m-%d")

    if reward_type == "daily":
        return now.date() > last_time.date()
    elif reward_type == "weekly":
        return now.isocalendar()[1] > last_time.isocalendar()[1] or now.year > last_time.year
    elif reward_type == "monthly":
        return now.month > last_time.month or now.year > last_time.year
    return False

def update_reward_claim_time(telegram_id, reward_type):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    with conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET last_{reward_type} = ? WHERE telegram_id=?", (now, telegram_id))

import time

def get_kumbizz_status(telegram_id):
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT kumbizz_level, last_kumbizz_claim FROM users WHERE telegram_id=?", (telegram_id,))
        row = cur.fetchone()
        if row:
            level, last = row
            return level or 0, last or 0
        return 0, 0

def claim_kumbizz(telegram_id):
    level, last_claim = get_kumbizz_status(telegram_id)
    now = int(time.time())

    if level == 0:
        return False, "🤖 هنوز کامبیز نداری! با دستور /upgradekumbizz اونو بساز."

    elapsed = now - last_claim
    if elapsed < 60:
        return False, f"⏳ حداقل باید ۶۰ ثانیه از برداشت قبلی گذشته باشه."

    capped = min(elapsed, 10800)  # سقف دریافت = ۳ ساعت
    income = capped * level

    update_balance(telegram_id, income)
    with conn:
        conn.execute("UPDATE users SET last_kumbizz_claim=? WHERE telegram_id=?", (now, telegram_id))
    return True, f"✅ {income} KUM⛀ از کامبیز دریافت شد! (طی {capped // 60} دقیقه)"

def upgrade_kumbizz(telegram_id):
    level, _ = get_kumbizz_status(telegram_id)
    next_level = level + 1
    price = 1000 * (2 ** level)
    balance = get_balance(telegram_id)

    if balance < price:
        return False, f"💰 برای ارتقاء به سطح {next_level} باید {price} KUM⛀ داشته باشی."

    update_balance(telegram_id, -price)
    with conn:
        conn.execute("UPDATE users SET kumbizz_level=? WHERE telegram_id=?", (next_level, telegram_id))
    return True, f"🎉 کامبیز به سطح {next_level} ارتقاء یافت! حالا در هر ثانیه {next_level} KUM⛀ تولید می‌کنه."

def start_double_or_nothing(telegram_id, amount):
    with conn:
        conn.execute("INSERT OR REPLACE INTO gamble_state (telegram_id, amount, active) VALUES (?, ?, 1)",
                     (telegram_id, amount))

def get_gamble_state(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT amount, active FROM gamble_state WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        return row if row else (0, 0)

def update_gamble_amount(telegram_id, amount):
    with conn:
        conn.execute("UPDATE gamble_state SET amount=? WHERE telegram_id=?", (amount, telegram_id))

def end_gamble(telegram_id):
    with conn:
        conn.execute("UPDATE gamble_state SET active=0 WHERE telegram_id=?", (telegram_id,))

def get_factory_status(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT product, start_time FROM factory WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        return row if row else (None, None)
    
def start_production(telegram_id, product_name):
    from factory_data import factory_levels
    from factory_data import factory_data

    has_factory, level = get_factory_info(telegram_id)
    if not has_factory:
        return False, "🏭 تو هنوز کارخونه نداری."

    cooldown = factory_levels[level]["cooldown"]
    now = int(time.time() * 1000)

    with conn:
        conn.execute("""
            INSERT OR REPLACE INTO factory (telegram_id, product, start_time)
            VALUES (?, ?, ?)
        """, (telegram_id, product_name, now))

    return True, f"✅ تولید {product_name} شروع شد! زمان تولید: {cooldown // 60} دقیقه"
    
def claim_product(telegram_id):
    from factory_data import factory_data
    product, start_time = get_factory_status(telegram_id)
    if not product or not start_time:
        return False, "🏭 تولیدی در حال انجام نیست."

    now = int(time.time() * 1000)
    build_time = factory_data[product]["time"]

    if now - start_time < build_time:
        remaining = build_time - (now - start_time)
        minutes = remaining // 60
        return False, f"⏳ محصول هنوز آماده نیست. باقی‌مانده: {minutes} دقیقه"

    add_item(telegram_id, product)
    with conn:
        conn.execute("DELETE FROM factory WHERE telegram_id=?", (telegram_id,))
    return True, f"✅ محصول {product} با موفقیت تحویل داده شد!"

def get_factory_info(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT has_factory, factory_level FROM users WHERE telegram_id=?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return 0, 0
    
def build_factory(telegram_id):
    has, _ = get_factory_info(telegram_id)
    if has:
        return False, "🏭 قبلاً کارخانه ساختی."

    from factory_data import factory_levels
    price = factory_levels[1]["price"]
    if get_balance(telegram_id) < price:
        return False, f"❌ برای ساخت کارخانه به {price} کام‌کوین نیاز داری."

    update_balance(telegram_id, -price)
    with conn:
        conn.execute("UPDATE users SET has_factory=1, factory_level=1 WHERE telegram_id=?", (telegram_id,))
    return True, "✅ کارخانه سطح ۱ ساخته شد!"

def upgrade_factory(telegram_id):
    from factory_data import factory_levels
    has, level = get_factory_info(telegram_id)
    if not has:
        return False, "🏭 اول باید کارخانه بسازی."

    next_level = level + 1
    if next_level not in factory_levels:
        return False, "🏭 کارخانه به بیشترین سطح ممکن رسیده."

    price = factory_levels[next_level]["price"]
    if get_balance(telegram_id) < price:
        return False, f"❌ برای ارتقا به سطح {next_level} به {price} کام‌کوین نیاز داری."

    update_balance(telegram_id, -price)
    with conn:
        conn.execute("UPDATE users SET factory_level=? WHERE telegram_id=?", (next_level, telegram_id))
    return True, f"✅ کارخانه به سطح {next_level} ارتقا یافت!"

def add_to_factory_queue(telegram_id, product_name):
    now = int(time.time() * 1000)
    with conn:
        conn.execute("INSERT INTO factory_queue (telegram_id, product, start_time) VALUES (?, ?, ?)",
                     (telegram_id, product_name, now))
        
def get_active_factory_slots(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM factory_queue WHERE telegram_id=?", (telegram_id,))
        return cursor.fetchone()[0]
    
def get_factory_queue(telegram_id):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT product, start_time FROM factory_queue WHERE telegram_id=?", (telegram_id,))
        return cursor.fetchall()
    
def claim_ready_products(telegram_id):
    from factory_data import factory_data
    now = int(time.time() * 1000)
    queue = get_factory_queue(telegram_id)
    delivered = []
    xp_gain = 0

    for product, start in queue:
        duration = factory_data.get(product, {}).get("time", 0)
        if now - start >= duration:
            add_item(telegram_id, product)
            delivered.append((product, start))
            xp_gain += 10

    add_xp(telegram_id, xp_gain)

    with conn:
        for product, start in delivered:
            conn.execute("DELETE FROM factory_queue WHERE telegram_id=? AND product=? AND start_time=?",
                         (telegram_id, product, start))

    return delivered, xp_gain

def buy_business(telegram_id, business_type):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM businesses WHERE telegram_id=? AND business_type=?", (telegram_id, business_type))
        if cursor.fetchone():
            return False, "🔁 این بیزینس رو قبلاً خریدی."

        cursor.execute("INSERT INTO businesses (telegram_id, business_type, level) VALUES (?, ?, 1)",
                       (telegram_id, business_type))
        return True, f"✅ بیزینس {business_type} ساخته شد!"
    
def upgrade_business(telegram_id, business_type, cost):
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT level FROM businesses WHERE telegram_id=? AND business_type=?", (telegram_id, business_type))
        row = cursor.fetchone()
        if not row:
            return False, "❌ هنوز این بیزینس رو نخریدی."
        level = row[0]

        update_balance(telegram_id, -cost)
        cursor.execute("UPDATE businesses SET level = ? WHERE telegram_id=? AND business_type=?",
                       (level + 1, telegram_id, business_type))
        return True, f"⬆️ سطح بیزینس {business_type} به {level + 1} ارتقا یافت!"
    
def run_businesses(telegram_id):
    from business_data import business_data
    inventory = dict((name, qty) for name, qty, *_ in get_inventory(telegram_id))
    now_ms = int(time.time() * 1000)
    result_lines = []

    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT business_type, level, last_run FROM businesses WHERE telegram_id=?", (telegram_id,))
        businesses = cursor.fetchall()

        for biz, level, last_run in businesses:
            data = business_data.get(biz)
            if not data:
                continue

            cooldown_ms = data.get("cooldown", 1800000)
            inputs = {k: v + (level - 1) for k, v in data["base_input"].items()}
            outputs = {k: v + (level - 1) * 4 for k, v in data["base_output"].items()}

            # بررسی زمان کول‌داون
            if last_run and now_ms - last_run < cooldown_ms:
                remaining = cooldown_ms - (now_ms - last_run)
                minutes = remaining // 60000
                seconds = (remaining % 60000) // 1000
                result_lines.append(f"⏳ {biz} (سطح {level}) - آماده نیست، زمان باقی‌مانده: {minutes}دقیقه و {seconds}ثانیه")
                continue

            # بررسی موجودی
            if any(inventory.get(item, 0) < qty for item, qty in inputs.items()):
                result_lines.append(f"❌ {biz} (سطح {level}) - مواد اولیه کافی نیست")
                continue

            # مصرف مواد اولیه
            for item, qty in inputs.items():
                for _ in range(qty):
                    consume_item(telegram_id, item)

            # تولید محصول
            for item, qty in outputs.items():
                for _ in range(qty):
                    add_item(telegram_id, item)

            gain_xp = level * 10
            add_xp(telegram_id, gain_xp)
            result_lines.append(f"+{gain_xp}XP")

            # بروزرسانی زمان اجرا
            cursor.execute(
                "UPDATE businesses SET last_run=? WHERE telegram_id=? AND business_type=?",
                (now_ms, telegram_id, biz)
            )

            result_lines.append(f"✅ {biz} (سطح {level}) - تولید انجام شد!")

    if not result_lines:
        return ["❌ هیچ بیزینسی اجرا نشد."]

    return result_lines
