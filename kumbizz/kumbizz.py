import telebot
from db import init_db, add_user, get_balance, update_balance, add_item, get_inventory, add_xp, get_level, has_item, xp_required, get_best_item_by_type, reduce_item_hp, add_catch, sell_item, transfer_item, apply_daily_interest, upgrade_bank, withdraw, deposit, get_bank_info, init_rob_table, register_rob, can_rob, consume_item, buy_mine, upgrade_mine, effects, set_cooldown, get_cooldown, buy_farm_unit, harvest_farm, list_in_market, get_market_list, trade_from_market, cancel_market_item, get_user_missions, claim_mission_rewards, register_mission_action
from items import shop_items
from hunt_data import hunt_list
from fish_data import fish_list
from mine_items import mine_drops
import random
import datetime
import time

bot = telebot.TeleBot("7235180534:AAH_3W3R07_AaHT_QN05RsOGS9Lk5no4ar4")
init_db()
init_rob_table()

ADMIN_ID = 997816328  # آیدی عددی تلگرام خودت

from db import get_data

@bot.message_handler(commands=["stats"])
def handle_stats(message):
    if message.from_user.id != ADMIN_ID:
        return bot.reply_to(message, "⛔ این دستور فقط برای ادمین فعاله.")
    
    data = get_data()
    bot.reply_to(message, data)

def get_id(message):
    telegram_id = message.from_user.id
    return telegram_id

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
        
from db import register_invite, increment_invite_count, user_exists, get_invite_count

@bot.message_handler(commands=["start"])
def start(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    parts = message.text.split()
    if len(parts) > 1:
        inviter_id = int(parts[1])
        if inviter_id != telegram_id and user_exists(inviter_id):
            register_invite(telegram_id, inviter_id)
            increment_invite_count(inviter_id)
    bot.reply_to(message, "سلام. به دنیای کامبیز خوش اومدی! برای دیدن دستور های موجود بنویسید /commands")

@bot.message_handler(commands=["invite"])
def handle_invite(message):
    user_id = message.from_user.id
    bot.reply_to(message,
        f"📨 لینک دعوت اختصاصی شما:\n"
        f"https://t.me/kumbizz_bot?start={user_id}\n\n"
        f"📊 تعداد دعوت‌های موفق شما: {get_invite_count(user_id)}"
    )
    
@bot.message_handler(commands=["balance"])
def show_balance(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    balance, bank_balance, bank_capacity = get_bank_info(telegram_id)
    bot.reply_to(message, f"کیف پول: {balance} KUM⛀\nبانک: {bank_balance}/{bank_capacity} KUM⛀")

@bot.message_handler(commands=["beg"])
def beg(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    now = int(time.time())
    cooldown_until = get_cooldown(telegram_id, "beg")

    if now < cooldown_until:
        remaining = cooldown_until - now
        bot.reply_to(message, f"⏳ لطفاً {remaining} ثانیه دیگر صبر کن.")
        return

    set_cooldown(telegram_id, "beg", 30)
    chance = 90
    chance_percent = random.randint(1, 100)
    if(chance >= chance_percent):
        level, xp = get_level(telegram_id)
        amount = random.randint(10, 100)*(level)
        update_balance(telegram_id, amount)
        xp_gain = 5 * level
        add_xp(telegram_id, xp_gain)
        bot.reply_to(message, f"یکی دلش سوخت و بهت {amount} تا KUM⛀ داد! +5XP")
    else:
        bot.reply_to(message, "کسی دلش به حالت نسوخت!")

@bot.message_handler(commands=["shop"])
def shop(message):
    text = "فروشگاه کامبیز:\n"
    for name, info in shop_items.items():
        text += f"{name} - {info['price']} KUM⛀\n{info['description']}\n\n"
    text += "برای خرید: /buy [اسم کالا] رو بنویسید."
    bot.reply_to(message, text)

@bot.message_handler(commands=['buy'])
def buy(message):
    try:
        telegram_id = get_id(message)
        add_user(telegram_id)
        item_name = message.text.split(" ", 2)[2]
        qty_str = message.text.split(" ", 2)[1]
        if not is_int(qty_str):
            return bot.reply_to(message, "تعداد رو وارد نکردی!")
        qty = int(qty_str)
        item = shop_items.get(item_name)

        if not item:
            bot.reply_to(message, "این کالا وجود نداره.")
            return

        user_balance = get_balance(telegram_id)
        if user_balance < item["price"]*qty:
            bot.reply_to(message, "پول کافی نداری!")
            return

        update_balance(telegram_id, -(item["price"]*qty))
        for i in range(qty):
            add_item(telegram_id, item_name)
        bot.reply_to(message, f"تبریک! تو الان {qty} تا '{item_name}' داری.")
    except IndexError:
        bot.reply_to(message, "فرمت درست: /buy [تعداد] [اسم کالا]")

@bot.message_handler(commands=["inventory"])
def handle_inventory(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    items = get_inventory(telegram_id)

    if not items:
        return bot.reply_to(message, "اینونتوری‌ات خالیه!")

    response = "📦 اینونتوری تو:\n"
    for name, qty, hp in items:
        line = f"- {name} × {qty}"
        if hp is not None:
            line += f" (hp: {hp})"
        response += line + "\n"

    bot.reply_to(message, response)

@bot.message_handler(commands=["level"])
def level(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    level, xp = get_level(telegram_id)
    req = xp_required(level)
    bot.reply_to(message, f"لول فعلی: {level}\nتجربه: {xp}/{req}")


    
@bot.message_handler(commands=["work"])
def work(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    now = int(time.time())
    cooldown_until = get_cooldown(telegram_id, "work")

    if now < cooldown_until:
        remaining = cooldown_until - now
        bot.reply_to(message, f"⏳ لطفاً {remaining} ثانیه دیگر صبر کن.")
        return
    
    if not has_item(telegram_id, "کت و شلوار"):
        bot.reply_to(message, "برای کار کردن باید یه کت و شلوار بخری تا شبیه کارمندها بشی! (/shop)")
        return

    level, xp = get_level(telegram_id)
    reward = 200*level
    gain_xp = 10 * level
    update_balance(telegram_id, reward)
    add_xp(telegram_id, gain_xp)
    set_cooldown(telegram_id, "work",120)
    register_mission_action(telegram_id, "work")
    bot.reply_to(message, f"آفرین! کار کردی و {reward} KUM⛀ گرفتی. +{gain_xp}XP")

from fish_data import fish_list

@bot.message_handler(commands=["fish"])
def fish(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    result = get_best_item_by_type(telegram_id, "fishing rod")

    now = int(time.time())
    cooldown_until = get_cooldown(telegram_id, "fish")

    if now < cooldown_until:
        remaining = cooldown_until - now
        bot.reply_to(message, f"⏳ لطفاً {remaining} ثانیه دیگر صبر کن.")
        return

    if not result:
        bot.reply_to(message, "نیاز به چوب ماهیگیری داری! برو از فروشگاه بخر.")
        return

    item_name, item = result
    item_rarity = item.get("rarity", "common")
    multiplier = float(item.get("multiplier", 1.0))
    chance = item.get("chance", 50)
    set_cooldown(telegram_id, "fish", 60)

    success = random.randint(1, 100) <= chance
    if not success:
        bot.reply_to(message, f"متأسفم! با {item_name} چیزی نگرفتی.")
        return

    # فیلتر ماهی‌های مناسب بر اساس rarity
    allowed = ["common", "rare", "epic", "legendary"]
    index = allowed.index(item_rarity)
    possible_fish = [f for f in fish_list if allowed.index(f["rarity"]) <= index]

    caught = random.choice(possible_fish)
    xp_gain = int(10 * multiplier)
    add_catch(telegram_id, caught["name"])
    add_xp(telegram_id, xp_gain)
    register_mission_action(telegram_id, "fish")

    damage = random.randint(3, 7)
    reduce_item_hp(telegram_id, item_name, damage)

    bot.reply_to(message, f"با {item_name} یک {caught['name']} گرفتی! +{xp_gain} XP")

from hunt_data import hunt_list

@bot.message_handler(commands=["hunt"])
def hunt(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    result = get_best_item_by_type(telegram_id, "weapon")

    now = int(time.time())
    cooldown_until = get_cooldown(telegram_id, "hunt")

    if now < cooldown_until:
        remaining = cooldown_until - now
        bot.reply_to(message, f"⏳ لطفاً {remaining} ثانیه دیگر صبر کن.")
        return

    if not result:
        bot.reply_to(message, "نیاز به تفنگ داری! برو از فروشگاه بخر.")
        return

    item_name, item = result
    item_rarity = item.get("rarity", "common")
    multiplier = float(item.get("multiplier", 1.0))
    chance = item.get("chance", 50)
    set_cooldown(telegram_id, "hunt", 60)

    success = random.randint(1, 100) <= chance
    if not success:
        bot.reply_to(message, f"متأسفم! با {item_name} شکار فرار کرد.")
        return

    allowed = ["common", "rare", "epic", "legendary"]
    index = allowed.index(item_rarity)
    possible_hunts = [h for h in hunt_list if allowed.index(h["rarity"]) <= index]

    caught = random.choice(possible_hunts)
    xp_gain = int(12 * multiplier)
    add_catch(telegram_id, caught["name"])
    add_xp(telegram_id, xp_gain)
    register_mission_action(telegram_id, "hunt")

    damage = random.randint(3, 7)
    reduce_item_hp(telegram_id, item_name, damage)

    bot.reply_to(message, f"با {item_name} یک {caught['name']} شکار کردی! +{xp_gain} XP")

from fish_data import fish_list
from hunt_data import hunt_list
from farm_data import farm_sellable
from factory_data import factory_sellable

# ساخت دیکشنری قیمت‌ها برای lookup سریع
item_prices = {item["name"]: item["base_price"] for item in (fish_list + hunt_list + mine_drops + farm_sellable + factory_sellable)}

@bot.message_handler(commands=["sell"])
def sell(message):
    try:
        telegram_id = get_id(message)
        add_user(telegram_id)
        parts = message.text.replace("/sell", "").strip().split(" ", 1)

        if len(parts) < 2:
            bot.reply_to(message, "فرمت درست: /sell [تعداد] [نام آیتم]")
            return

        quantity_str, item_name = parts[0], parts[1].strip()
        quantity = int(quantity_str)
        if quantity <= 0:
            bot.reply_to(message, "تعداد باید بیشتر از صفر باشه.")
            return

        price = item_prices.get(item_name)
        if not price:
            bot.reply_to(message, "این آیتم قابل فروش نیست.")
            return

        success = sell_item(telegram_id, item_name, quantity, price)
        if success:
            total = price * quantity
            bot.reply_to(message, f"{quantity} عدد '{item_name}' رو به {total} KUM⛀ فروختی!")
            register_mission_action(telegram_id, "hunt")
        else:
            bot.reply_to(message, "این آیتم رو به تعداد کافی نداری.")

    except ValueError:
        bot.reply_to(message, "تعداد وارد شده عدد نیست.")
    except Exception as e:
        bot.reply_to(message, f"خطا در فروش: {e}")

@bot.message_handler(commands=["gift"])
def gift(message):
    try:
        if not message.reply_to_message:
            bot.reply_to(message, "برای هدیه دادن، باید روی پیام دوستت ریپلای کنی و بنویسی: /gift [تعداد] [نام آیتم]")
            return

        receiver_id = message.reply_to_message.from_user.id
        sender_id = get_id(message)
        add_user(sender_id)
        add_user(receiver_id)

        if receiver_id == sender_id:
            bot.reply_to(message, "نمی‌تونی به خودت هدیه بدی!")
            return

        text = message.text.replace("/gift", "").strip()
        parts = text.split(" ", 1)
        if len(parts) < 2:
            bot.reply_to(message, "فرمت درست: /gift [تعداد] [نام آیتم]")
            return

        quantity = int(parts[0])
        item_name = parts[1].strip()

        if quantity <= 0:
            bot.reply_to(message, "تعداد باید بیشتر از صفر باشه.")
            return

        success = transfer_item(sender_id, receiver_id, item_name, quantity)
        if success:
            bot.reply_to(message, f"{quantity} عدد '{item_name}' رو به [{receiver_id}](tg://user?id={receiver_id}) هدیه دادی!")
            
            telegram_id = sender_id
            register_mission_action(telegram_id, "gift")
        else:
            bot.reply_to(message, "این آیتم رو به تعداد کافی نداری.")

    except ValueError:
        bot.reply_to(message, "تعداد وارد شده عدد نیست.")
    except Exception as e:
        bot.reply_to(message, f"خطا در هدیه دادن: {e}")

@bot.message_handler(commands=["deposit"])
def handle_deposit(message):
    try:
        amount = int(message.text.split(" ")[1])
        telegram_id = get_id(message)
        add_user(telegram_id)
        success, msg = deposit(telegram_id, amount)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "فرمت درست: /deposit [مقدار]")

@bot.message_handler(commands=["withdraw"])
def handle_withdraw(message):
    try:
        amount = int(message.text.split(" ")[1])
        telegram_id = get_id(message)
        add_user(telegram_id)
        success, msg = withdraw(telegram_id, amount)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "فرمت درست: /withdraw [مقدار]")

@bot.message_handler(commands=["upgradebank"])
def handle_upgradebank(message):
    try:
        cost = int(message.text.split(" ")[1])
        telegram_id = get_id(message)
        add_user(telegram_id)
        success, msg = upgrade_bank(telegram_id, cost)
        bot.reply_to(message, msg)
    except:
        bot.reply_to(message, "فرمت درست: /upgradebank [مقدار کوینی که می‌خوای خرج کنی]")

@bot.message_handler(commands=["interest"])
def handle_interest(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = apply_daily_interest(telegram_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["rob"])
def handle_rob(message):
    from db import get_balance, update_balance, get_inventory, reduce_item_hp
    import random, datetime

    if not message.reply_to_message:
        bot.reply_to(message, "برای دزدی باید روی پیام قربانی ریپلای کنی!")
        return

    thief_id = get_id(message)
    add_user(thief_id)
    victim_id = message.reply_to_message.from_user.id
    add_user(victim_id)

    if thief_id == victim_id:
        bot.reply_to(message, "از خودت نمی‌تونی بدزدی!")
        return

    # بررسی cooldown (مثلاً در یک جدول جدا ثبت شه)
    if not can_rob(thief_id):
        bot.reply_to(message, "فعلاً نمی‌تونی دزدی کنی. باید ۲۴ ساعت صبر کنی.")
        return

    victim_balance = get_balance(victim_id)
    if victim_balance < 100:
        bot.reply_to(message, "قربانی پول زیادی نداره که دزدی کنی!")
        return

    # بررسی آیتم‌های ضد دزدی
    victim_inventory = get_inventory(victim_id)
    msg_effect = ""
    for item, qty, _ in victim_inventory:
        if item == "گاز اشک‌آور" and random.random() < 0.4:
            msg_effect = "گاز اشک‌آور قربانی باعث شد دزدی شکست بخوره!"
            consume_item(victim_id, item)
            return bot.reply_to(message, msg_effect)
        elif item == "سگ نگهبان" and random.random() < 0.2:
            msg_effect = "سگ نگهبان پارس کرد و تو رو فراری داد!"
            return bot.reply_to(message, msg_effect)
        elif item == "کیف زرهی":
            victim_balance //= 2
            msg_effect = "(کیف زرهی مقدار دزدی رو نصف کرد)"

    # محاسبه مقدار دزدی
    steal_amount = random.randint(int(victim_balance * 0.1), int(victim_balance * 0.25))
    steal_amount = min(steal_amount, 25000)

    update_balance(victim_id, -steal_amount)
    update_balance(thief_id, steal_amount)
    register_rob(thief_id)  # ثبت زمان برای cooldown
    register_mission_action(thief_id, "rob")
    thief_level, ksshr = get_level(thief_id) 
    xp_gain = 10 * thief_level
    add_xp(thief_id, xp_gain)

    bot.reply_to(message, f"تو {steal_amount} KUM⛀ از کیف پول قربانی دزدیدی! {msg_effect} +{xp_gain}XP")

@bot.message_handler(commands=["buy_mine"])
def handle_buy_mine(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = buy_mine(telegram_id)
    bot.reply_to(message, msg)

from db import get_mine_status, perform_mine

@bot.message_handler(commands=["mine"])
def handle_mine(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    mine_level, last_mine = get_mine_status(telegram_id)
    success, response = perform_mine(telegram_id, mine_level, last_mine)
    if success:
        register_mission_action(telegram_id, "mine")
    bot.reply_to(message, response)

from recipes import craft_recipes
from db import get_inventory, consume_item, add_item

@bot.message_handler(commands=["craft"])
def handle_craft(message):
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت درست: /craft [نام آیتم]")

    item_name = parts[1].strip()
    recipe = craft_recipes.get(item_name)
    if not recipe:
        return bot.reply_to(message, f"چنین آیتمی برای ساخت وجود نداره.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    inventory = {name: qty for name, qty, _ in get_inventory(telegram_id)}

    for mat, qty_needed in recipe["materials"].items():
        if inventory.get(mat, 0) < qty_needed:
            return bot.reply_to(message, f"برای ساخت «{item_name}» به {qty_needed} عدد {mat} نیاز داری.")

    # همه مواد موجودن → حذف و افزودن
    for mat, qty in recipe["materials"].items():
        for _ in range(qty):
            consume_item(telegram_id, mat)

    add_item(telegram_id, item_name)
    bot.reply_to(message, f"با موفقیت «{item_name}» ساخته شد!")

@bot.message_handler(commands=["upgrade_mine"])
def handle_upgrade_mine(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    mine_level, _ = get_mine_status(telegram_id)
    success, msg = upgrade_mine(telegram_id, mine_level)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["minestatus"])
def handle_mine_status(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    mine_level, last_mine = get_mine_status(telegram_id)

    from mine_items import mine_data

    level_data = mine_data.get(mine_level, {})
    cooldown = level_data.get("cooldown", 6)
    count = level_data.get("count", 1)
    unlocks = level_data.get("unlocks", [])

    text = f"""📊 وضعیت معدن شما:

🔸 سطح: {mine_level}
⏳ کول‌داون استخراج: هر {cooldown} ساعت
📦 مقدار استخراج در هر بار: {count}
📍 منابع آزادشده در این سطح:
{', '.join(unlocks)}
"""

    bot.reply_to(message, text)

@bot.message_handler(commands=["cook"])
def handle_cook(message):
    from food_data import food_data
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت: /cook [نام غذا]")

    food_name = parts[1].strip()
    recipe = food_data.get(food_name)
    if not recipe:
        return bot.reply_to(message, "چنین غذایی وجود نداره.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    inventory = {name: qty for name, qty, _ in get_inventory(telegram_id)}

    for mat, qty in recipe["materials"].items():
        if inventory.get(mat, 0) < qty:
            return bot.reply_to(message, f"برای پخت {food_name} به {qty}× {mat} نیاز داری.")

    for mat, qty in recipe["materials"].items():
        for _ in range(qty):
            consume_item(telegram_id, mat)

    add_item(telegram_id, food_name)
    register_mission_action(telegram_id, "cook")
    bot.reply_to(message, f"«{food_name}» با موفقیت پخته شد!")

@bot.message_handler(commands=["eat"])
def handle_eat(message):
    from food_data import food_data
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت: /eat [نام غذا]")

    food_name = parts[1].strip()
    data = food_data.get(food_name)
    if not data:
        return bot.reply_to(message, "چنین غذایی وجود نداره.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    inventory = {name: qty for name, qty, _ in get_inventory(telegram_id)}
    if inventory.get(food_name, 0) < 1:
        return bot.reply_to(message, "این غذا رو نداری!")

    consume_item(telegram_id, food_name)

    effect = data["effect"]
    now = datetime.datetime.utcnow()
    expires_at = None
    uses_left = None
    effects(effect, now, telegram_id, uses_left, expires_at)

    bot.reply_to(message, f"{food_name} مصرف شد! اثرش فعاله.")

@bot.message_handler(commands=["buy_farm"])
def handle_buy_farm(message):
    from farm_data import farm_data
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return bot.reply_to(message, "فرمت: /buy_farm [تعداد] [نوع واحد مزرعه]")

    qty_str = parts[1].strip()
    if not is_int(qty_str):
        return bot.reply_to(message, "تعداد رو وارد نکردی!")
    qty = int(qty_str)
    unit_type = parts[2].strip()
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = buy_farm_unit(telegram_id, unit_type, qty)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["harvest"])
def handle_harvest(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = harvest_farm(telegram_id)
    register_mission_action(telegram_id, "harvest")
    bot.reply_to(message, msg)

from db import farm_status

@bot.message_handler(commands=["farmstatus"])
def handle_farm_status(message):
    telegram_id = get_id(message)
    response = farm_status(telegram_id)

    bot.reply_to(message, response, parse_mode="HTML")


@bot.message_handler(commands=["farm_shop"])
def handle_farm_shop(message):
    from farm_data import farm_data
    text = "🌱 <b>فروشگاه مزرعه</b>\n\n"
    
    for name, info in farm_data.items():
        price = info["price"]
        product = info["product"]
        interval = info["interval_hours"]
        product_price = info["product_price"]
        text += (
            f"• <b>{name}</b>\n"
            f"  💰 قیمت: {price} KUM⛀\n"
            f"  🌾 تولید: {product} هر {interval} ساعت\n"
            f"  💰 قیمت {product}: {product_price} KUM⛀\n\n"
        )

    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=["list"])
def handle_list(message):
    return bot.reply_to(message, "این بخش هنوز راه نیوفتاده")
    parts = message.text.split(" ", 2)
    if len(parts) < 3:
        return bot.reply_to(message, "فرمت درست: /list [نام آیتم] [قیمت]")

    item_name = parts[1].strip()
    try:
        price = int(parts[2])
    except:
        return bot.reply_to(message, "قیمت باید عدد باشه.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    inventory = {name: qty for name, qty, _ in get_inventory(telegram_id)}
    if inventory.get(item_name, 0) < 1:
        return bot.reply_to(message, "این آیتم رو نداری!")

    consume_item(telegram_id, item_name)
    list_in_market(telegram_id, item_name, price)

    bot.reply_to(message, f"«{item_name}» به بازار اضافه شد با قیمت {price} کوین.")

@bot.message_handler(commands=["market"])
def handle_market(message):
    return bot.reply_to(message, "این بخش هنوز راه نیوفتاده")
    parts = message.text.split(" ", 1)
    filter_text = parts[1].strip() if len(parts) > 1 else None

    success, result = get_market_list(filter_text)
    if not success:
        return bot.reply_to(message, result)

    rows = result
    if not rows:
        return bot.reply_to(message, "آگهی‌ای مطابق با فیلتر پیدا نشد.")

    response = "🛒 بازار آزاد:\n"
    for row in rows:
        id_, name, price, seller = row
        response += f"#{id_} | {name} - {price} کوین (فروشنده: {seller})\n"

    bot.reply_to(message, response)

    bot.reply_to(message, response)

@bot.message_handler(commands=["trade"])
def handle_trade(message):
    return bot.reply_to(message, "این بخش هنوز راه نیوفتاده")
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت درست: /trade [id]")

    try:
        trade_id = int(parts[1])
    except:
        return bot.reply_to(message, "شناسه آگهی باید عدد باشه.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = trade_from_market(telegram_id, trade_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["cancel"])
def handle_cancel(message):
    return bot.reply_to(message, "این بخش هنوز راه نیوفتاده")
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت درست: /cancel [id]")

    try:
        trade_id = int(parts[1])
    except:
        return bot.reply_to(message, "شناسه باید عدد باشه.")

    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = cancel_market_item(telegram_id, trade_id)
    register_mission_action(telegram_id, "trade")
    bot.reply_to(message, msg)

@bot.message_handler(commands=["missions"])
def handle_missions(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    missions = get_user_missions(telegram_id)
    if not missions:
        return bot.reply_to(message, "هنوز ماموریتی برای امروز ثبت نشده.")

    text = "🎯 ماموریت‌های امروز:\n"
    for m in missions:
        status = "✅" if m["completed"] else f"{m['progress']}/{m['target']}"
        text += f"- {m['desc']} ({status})\n"

    bot.reply_to(message, text)

@bot.message_handler(commands=["claim"])
def handle_claimmissions(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = claim_mission_rewards(telegram_id)
    bot.reply_to(message, msg)

from db import can_claim_reward, update_reward_claim_time, update_balance

@bot.message_handler(commands=["daily"])
def handle_daily(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    if not can_claim_reward(telegram_id, "daily"):
        return bot.reply_to(message, "🕓 پاداش روزانه‌ات رو امروز گرفتی. فردا دوباره بیا!")

    update_balance(telegram_id, 1000)
    update_reward_claim_time(telegram_id, "daily")
    bot.reply_to(message, "🎁 پاداش روزانه گرفتی: 1000 KUM⛀!")

@bot.message_handler(commands=["weekly"])
def handle_weekly(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    if not can_claim_reward(telegram_id, "weekly"):
        return bot.reply_to(message, "🕓 پاداش هفتگی‌ات رو این هفته گرفتی. هفته بعد بیا!")

    update_balance(telegram_id, 10000)
    update_reward_claim_time(telegram_id, "weekly")
    bot.reply_to(message, "🎁 پاداش هفتگی گرفتی: 10000 KUM⛀!")

@bot.message_handler(commands=["monthly"])
def handle_monthly(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    if not can_claim_reward(telegram_id, "monthly"):
        return bot.reply_to(message, "🕓 این ماه پاداشت رو گرفتی. ماه بعد بیا!")

    update_balance(telegram_id, 100000)
    update_reward_claim_time(telegram_id, "monthly")
    bot.reply_to(message, "🎁 پاداش ماهانه گرفتی: 100000 KUM⛀!")

from db import claim_kumbizz

@bot.message_handler(commands=["kumbizz"])
def handle_kumbizz(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = claim_kumbizz(telegram_id)
    bot.reply_to(message, msg)

from db import upgrade_kumbizz

@bot.message_handler(commands=["upgradekumbizz"])
def handle_upgrade_kumbizz(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = upgrade_kumbizz(telegram_id)
    bot.reply_to(message, msg)

from db import start_double_or_nothing, get_gamble_state, update_gamble_amount, end_gamble

@bot.message_handler(commands=["double"])
def handle_double(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return bot.reply_to(message, "💰 مقدار شرط رو وارد کن. مثلا:\n/double 1000")

    amount = int(parts[1])
    if amount <= 0 or get_balance(telegram_id) < amount:
        return bot.reply_to(message, "❌ موجودی کافی نداری.")

    update_balance(telegram_id, -amount)
    start_double_or_nothing(telegram_id, amount)
    bot.reply_to(message, f"🎰 شروع شد! شرط اولیه {amount} KUM⛀.\nارسال /continue برای ادامه یا /take برای برداشت.")

@bot.message_handler(commands=["continue"])
def handle_continue(message):
    telegram_id = get_id(message)
    amount, active = get_gamble_state(telegram_id)
    if not active:
        return bot.reply_to(message, "❌ بازی فعالی نداری. از /double شروع کن.")
    
    add_xp(telegram_id, 1)
    if random.choice([True, False]):
        new_amount = amount * 2
        update_gamble_amount(telegram_id, new_amount)
        bot.reply_to(message, f"✅ بردی! مبلغ فعلی: {new_amount}KUM⛀ +1XP\nادامه بده با /continue یا پول رو بگیر با /take")
    else:
        end_gamble(telegram_id)
        bot.reply_to(message, f"💥 باختی! مبلغ {amount}KUM⛀ از دست رفت. +1XP")

@bot.message_handler(commands=["take"])
def handle_take(message):
    telegram_id = get_id(message)
    amount, active = get_gamble_state(telegram_id)
    if not active:
        return bot.reply_to(message, "❌ بازی فعالی نداری.")

    update_balance(telegram_id, amount)
    end_gamble(telegram_id)
    bot.reply_to(message, f"💰 مبلغ {amount}KUM⛀ با موفقیت برداشت شد. مبارک باشه!")

@bot.message_handler(commands=["slot"])
def handle_slot(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return bot.reply_to(message, "💰 مقدار شرط رو وارد کن. مثلا:\n/slot 500")

    bet = int(parts[1])
    if bet <= 0 or get_balance(telegram_id) < bet:
        return bot.reply_to(message, "❌ موجودی کافی نداری.")

    update_balance(telegram_id, -bet)

    emojis = ['🍒', '🍋', '🍇', '💎', '💀']
    result = [random.choice(emojis) for _ in range(3)]

    counts = {}
    for e in result:
        counts[e] = counts.get(e, 0) + 1

    max_count = max(counts.values())
    reward = 0
    outcome = "💥 باختی!"
    add_xp(telegram_id, 1)

    if max_count == 3:
        if result[0] == "💎":
            reward = bet * 15
            outcome = "💎 سه تا الماس! برد ×15"
            add_xp(telegram_id, 1)
        else:
            reward = bet * 8
            outcome = f"✅ سه تا {result[0]}! برد ×8"
            add_xp(telegram_id, 1)
    elif max_count == 2:
        reward = int(bet * 1.5)
        outcome = f"🪙 دو تا {max(counts, key=counts.get)}! برد ×1.5"
        add_xp(telegram_id, 1)

    if reward > 0:
        update_balance(telegram_id, reward)

    bot.reply_to(message, f"🎰 نتیجه:\n{' '.join(result)}\n\n{outcome}\n{'🏆 +'+str(reward)+'KUM⛀ +2XP' if reward else '😢 شرط از دست رفت +1XP'}")

@bot.message_handler(commands=["guess"])
def handle_guess(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    parts = message.text.split()
    if len(parts) < 3 or not parts[1].isdigit() or not parts[2].isdigit():
        return bot.reply_to(message, "🎯 استفاده درست:\n/guess [عدد 1 تا 10] [مقدار شرط]")

    guess = int(parts[1])
    bet = int(parts[2])

    if not 1 <= guess <= 10:
        return bot.reply_to(message, "❌ عدد حدس باید بین 1 تا 10 باشه.")

    if bet <= 0 or get_balance(telegram_id) < bet:
        return bot.reply_to(message, "❌ موجودی کافی نداری یا مقدار شرط نامعتبره.")

    update_balance(telegram_id, -bet)
    number = random.randint(1, 10)
    add_xp(telegram_id, 1)

    if guess == number:
        add_xp(telegram_id, 4)
        reward = bet * 10
        update_balance(telegram_id, reward)
        bot.reply_to(message, f"🎯 عدد صحیح: {number}\n✅ حدس درست! +{reward}KUM⛀ کام‌کوین +5XP")
    else:
        bot.reply_to(message, f"🎯 عدد صحیح: {number}\n💥 حدست اشتباه بود! شرط از دست رفت. +1XP")

from db import build_factory, upgrade_factory, get_factory_info, get_active_factory_slots, add_to_factory_queue

@bot.message_handler(commands=["produce"])
def handle_produce(message):
    from factory_data import factory_data
    telegram_id = get_id(message)
    add_user(telegram_id)

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        return bot.reply_to(message, "فرمت نوشتنت اشتباهه!. /produce [محصول]")

    product = parts[1]
    count = 1

    if product not in factory_data:
        return bot.reply_to(message, "❌ این محصول در کارخانه وجود نداره.")

    has_factory, level = get_factory_info(telegram_id)
    if not has_factory:
        return bot.reply_to(message, "🏭 هنوز کارخونه نساختی. با /buildfactory شروع کن.")

    max_slots = level
    used_slots = get_active_factory_slots(telegram_id)
    available_slots = max_slots - used_slots

    if available_slots <= 0:
        return bot.reply_to(message, "🛠 همه اسلات‌های کارخانه‌ت در حال تولید هستن.")

    produce_count = min(count, available_slots)
    if produce_count <= 0:
        return bot.reply_to(message, "❌ نمی‌تونی بیشتر از ظرفیتت تولید کنی.")

    raw_inventory = get_inventory(telegram_id)
    inventory = {}
    for entry in raw_inventory:
        name = entry[0]
        qty = entry[1]
        inventory[name] = qty
    inputs = factory_data[product]["inputs"]

    for i in range(produce_count):
        for item, qty in inputs.items():
            if inventory.get(item, 0) < qty:
                return bot.reply_to(message, f"❌ برای تولید {produce_count} تا {product}، مواد اولیه کافی نیست.")
    
    for i in range(produce_count):
        for item, qty in inputs.items():
            for _ in range(qty):
                consume_item(telegram_id, item)
        add_to_factory_queue(telegram_id, product)

    return bot.reply_to(message, f"✅ {produce_count} × {product} در صف تولید قرار گرفت.")

from db import claim_ready_products, get_factory_queue

@bot.message_handler(commands=["factory"])
def handle_factory(message):
    from factory_data import factory_data
    telegram_id = get_id(message)
    add_user(telegram_id)

    delivered, xp_gain = claim_ready_products(telegram_id)
    msg = ""

    if delivered:
        items = "\n".join(f"• {name}" for name, _ in delivered)
        msg += f"📦 محصولات تحویل‌شده:\n{items}\n+{xp_gain}XP\n"

    queue = get_factory_queue(telegram_id)
    if not queue:
        msg += "📭 در حال حاضر چیزی در صف تولید نداری."
        return bot.reply_to(message, msg)

    now = int(time.time() * 1000)
    msg += "🔧 محصولات در حال ساخت:\n"
    for product, start in queue:
        duration = factory_data[product]["time"]
        remaining = duration - (now - start)
        minutes = max(0, remaining // 60000)
        msg += f"• {product} - باقی‌مانده: {minutes} دقیقه\n"

    bot.reply_to(message, msg)

@bot.message_handler(commands=["buildfactory"])
def handle_build_factory(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = build_factory(telegram_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["upgradefactory"])
def handle_upgrade_factory(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = upgrade_factory(telegram_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["factory_list"])
def handle_upgrade_factory(message):
    text = """
🏭 <b>محصولات قابل تولید در کارخانه:</b>

🔹 آهن – از سنگ آهن
قیمت فروش: 800KUM⛀
🔹 مس – از سنگ مس
قیمت فروش: 1100KUM⛀
🔹 آرد – از گندم
قیمت فروش: 250KUM⛀
🔹 نان – از آرد
قیمت فروش: 650KUM⛀
🔹 کیک – از آرد + شیر
قیمت فروش: 1300KUM⛀
🔹 لباس سنتی – از پشم + گیاه دارویی
قیمت فروش: 1500KUM⛀
🔹 شمع طبی – از موم + گیاه دارویی
قیمت فروش: 1700KUM⛀
🔹 آبجو – از جو
قیمت فروش: 750KUM⛀
🔹 شمش طلا – از طلا
قیمت فروش: 4800KUM⛀
🔹 شیشه کریستال – از کریستال آبی + سنگ
قیمت فروش: 9000KUM⛀
🔹 تیتاپ – از کیک + عسل
قیمت فروش: 2300KUM⛀
🔹 زره آهنین – از آهن + پشم
قیمت فروش: 1900KUM⛀
🔹 پاپ کورن – از ذرت
قیمت فروش: 1200KUM⛀
🔹 آجر – از سنگ + زغال
قیمت فروش: 850KUM⛀
🔹 بالشت – از پر + پشم
قیمت فروش: 2000KUM⛀
🔹 پنیر – از شیر
قیمت فروش: 900KUM⛀
🔹 نون و پنیر – از نان + پنیر
قیمت فروش: 1800KUM⛀
🔹 کره – از شیر + شیر
قیمت فروش: 950KUM⛀
"""
    bot.reply_to(message, text, parse_mode="HTML")

from db import buy_business, upgrade_business, run_businesses

@bot.message_handler(commands=["buy_business"])
def handle_buy_business(message):
    from business_data import business_data
    telegram_id = get_id(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(message, "🔧 استفاده درست:\n/buy_business [نام بیزینس]")

    biz = parts[1].strip()
    if biz not in business_data:
        return bot.reply_to(message, "❌ چنین بیزینسی وجود نداره.")

    cost = business_data[biz]["upgrade_cost"]
    if get_balance(telegram_id) < cost:
        return bot.reply_to(message, f"❌ برای خرید این بیزینس {cost} کامکوین نیاز داری.")

    update_balance(telegram_id, -cost)
    success, msg = buy_business(telegram_id, biz)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["upgrade_business"])
def handle_upgrade_business(message):
    from business_data import business_data
    telegram_id = get_id(message)
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        return bot.reply_to(message, "🔧 استفاده درست:\n/upgrade_business [نام بیزینس]")

    biz = parts[1].strip()
    if biz not in business_data:
        return bot.reply_to(message, "❌ چنین بیزینسی وجود نداره.")

    cost = business_data[biz]["upgrade_cost"]
    if get_balance(telegram_id) < cost:
        return bot.reply_to(message, f"❌ برای ارتقا {cost} کامکوین نیاز داری.")

    success, msg = upgrade_business(telegram_id, biz, cost)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["run_business"])
def handle_run_business(message):
    telegram_id = get_id(message)
    results = run_businesses(telegram_id)
    response = "\n".join(results)
    bot.reply_to(message, response)

@bot.message_handler(commands=["business"])
def handle_upgrade_factory(message):
    text = """
🏭 <b>بیزینس های موجود:</b>

🏪 آسیاب
🔸 ورودی: گندم ×1
🎁 خروجی: آرد ×4
💵 قیمت: 20000KUM⛀ | ⏳ کول‌داون: 15 دقیقه

🏪 تولیدی نان
🔸 ورودی: آرد ×1
🎁 خروجی: نان ×3
💵 قیمت: 20000KUM⛀ | ⏳ کول‌داون: 30 دقیقه

🏪 شیرینی پزی
🔸 ورودی: آرد ×2
🎁 خروجی: کیک ×3
💵 قیمت: 25000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 کارگاه لباس محلی
🔸 ورودی: پشم ×1 + گیاه دارویی ×1
🎁 خروجی: لباس سنتی ×2
💵 قیمت: 25000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 شمع سازی
🔸 ورودی: عسل ×1 + گیاه دارویی ×1
🎁 خروجی: شمع طبی ×2
💵 قیمت: 25000KUM⛀ | ⏳ کول‌داون: 30 دقیقه

🏪 کارگاه پنیر
🔸 ورودی: شیر ×1
🎁 خروجی: پنیر ×3
💵 قیمت: 20000KUM⛀ | ⏳ کول‌داون: 15 دقیقه

🏪 تولیدی صبحانه
🔸 ورودی: نان ×1 + پنیر ×1
🎁 خروجی: نون و پنیر ×2
💵 قیمت: 30000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 کارگاه بالشت دوزی
🔸 ورودی:  پر ×1
🎁 خروجی: بالشت ×2
💵 قیمت: 30000KUM⛀ | ⏳ کول‌داون: 30 دقیقه

🏪 تولیدی تیتاپ
🔸 ورودی: کیک ×1 + عسل ×1
🎁 خروجی: تیتاپ ×2
💵 قیمت: 30000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 آجر پزی
🔸 ورودی: سنگ ×1
🎁 خروجی: آجر ×4
💵 قیمت: 25000KUM⛀ | ⏳ کول‌داون: 15 دقیقه

🏪 کارگاه طلاسازی
🔸 ورودی: طلا ×1
🎁 خروجی: شمش طلا ×2
💵 قیمت: 50000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 شیشه گری کریستال
🔸 ورودی: کریستال آبی ×1 + سنگ ×1
🎁 خروجی: شیشه کریستال ×1
💵 قیمت: 60000KUM⛀ | ⏳ کول‌داون: 60 دقیقه

🏪 پاپ کورن سازی
🔸 ورودی: ذرت ×1
🎁 خروجی: پاپ کورن ×5
💵 قیمت: 20000KUM⛀ | ⏳ کول‌داون: 15 دقیقه

🏪 تولیدی کره
🔸 ورودی: شیر ×2
🎁 خروجی: کره ×3
💵 قیمت: 25000KUM⛀ | ⏳ کول‌داون: 15 دقیقه

🏪 زره سازی
🔸 ورودی: آهن ×1 + پشم ×1
🎁 خروجی: زره آهنین ×2
💵 قیمت: 35000KUM⛀ | ⏳ کول‌داون: 30 دقیقه

🏪 تولیدی دلستر
🔸 ورودی: جو ×1
🎁 خروجی: آبجو ×4
🏭 <b>بیزینس‌های موجود:</b>

🏪 آسیاب  
🔸 ورودی: گندم ×1  
🎁 خروجی: آرد ×2  
💵 قیمت: 50000 KUM⛀ | ⏳ 15 دقیقه  

🏪 تولیدی نان  
🔸 ورودی: آرد ×1  
🎁 خروجی: نان ×1  
💵 قیمت: 60000 KUM⛀ | ⏳ 30 دقیقه  

🏪 شیرینی‌پزی  
🔸 ورودی: آرد ×3  
🎁 خروجی: کیک ×2  
💵 قیمت: 75000 KUM⛀ | ⏳ 60 دقیقه  

🏪 کارگاه لباس محلی  
🔸 ورودی: پشم ×1 + گیاه دارویی ×1  
🎁 خروجی: لباس سنتی ×1  
💵 قیمت: 65000 KUM⛀ | ⏳ 60 دقیقه  

🏪 شمع‌سازی  
🔸 ورودی: عسل ×1 + گیاه دارویی ×1  
🎁 خروجی: شمع طبی ×1  
💵 قیمت: 75000 KUM⛀ | ⏳ 30 دقیقه  

🏪 کارگاه پنیر  
🔸 ورودی: شیر ×1  
🎁 خروجی: پنیر ×2  
💵 قیمت: 55000 KUM⛀ | ⏳ 15 دقیقه  

🏪 تولیدی صبحانه  
🔸 ورودی: نان ×1 + پنیر ×1  
🎁 خروجی: نون و پنیر ×1  
💵 قیمت: 80000 KUM⛀ | ⏳ 60 دقیقه  

🏪 کارگاه بالشت‌دوزی  
🔸 ورودی: پر ×1  
🎁 خروجی: بالشت ×1  
💵 قیمت: 75000 KUM⛀ | ⏳ 30 دقیقه  

🏪 تولیدی تیتاپ  
🔸 ورودی: کیک ×1 + عسل ×1  
🎁 خروجی: تیتاپ ×1  
💵 قیمت: 90000 KUM⛀ | ⏳ 60 دقیقه  

🏪 آجرپزی  
🔸 ورودی: سنگ ×1  
🎁 خروجی: آجر ×2  
💵 قیمت: 65000 KUM⛀ | ⏳ 15 دقیقه  

🏪 کارگاه طلاسازی  
🔸 ورودی: طلا ×1  
🎁 خروجی: شمش طلا ×1  
💵 قیمت: 50000 KUM⛀ | ⏳ 60 دقیقه  

🏪 شیشه‌گری کریستال  
🔸 ورودی: کریستال آبی ×1 + سنگ ×1  
🎁 خروجی: شیشه کریستال ×1  
💵 قیمت: 60000 KUM⛀ | ⏳ 60 دقیقه  

🏪 پاپ کورن‌سازی  
🔸 ورودی: ذرت ×1  
🎁 خروجی: پاپ کورن ×2  
💵 قیمت: 50000 KUM⛀ | ⏳ 15 دقیقه  

🏪 تولیدی کره  
🔸 ورودی: شیر ×3  
🎁 خروجی: کره ×2  
💵 قیمت: 70000 KUM⛀ | ⏳ 15 دقیقه  

🏪 زره‌سازی  
🔸 ورودی: آهن ×1 + پشم ×1  
🎁 خروجی: زره آهنین ×1  
💵 قیمت: 60000 KUM⛀ | ⏳ 30 دقیقه  

🏪 تولیدی دلستر  
🔸 ورودی: جو ×1  
🎁 خروجی: آبجو ×2  
💵 قیمت: 50000 KUM⛀ | ⏳ 15 دقیقه  

🏪 صبحانه‌فروشی  
🔸 ورودی: تخم مرغ ×1  
🎁 خروجی: نیمرو ×1  
💵 قیمت: 60000 KUM⛀ | ⏳ 15 دقیقه  

🏪 تولیدی پوشاک  
🔸 ورودی: پشم ×1  
🎁 خروجی: لباس ×1  
💵 قیمت: 55000 KUM⛀ | ⏳ 15 دقیقه
"""
    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=["commands", "help"])
def handle_commands(message):
    text = """
🧾 <b>دستورات بات کامبیز</b>

/invite برای گرفتن لینک و دیدن تعداد دعوت ها

/daily جایزه روزانه
/weekly جایزه هفتگی
/monthly جایزه ماهانه

/kumbizz دریافت پول حاصل از کار کامبیز
/upgradekumbizz ارتقای کامبیز

/balance - مشاهده موجودی سکه  
/inventory - مشاهده آیتم‌های در اختیار  
/shop - دیدن فروشگاه بازی  
/buy [نام آیتم] - خرید آیتم از فروشگاه  
/sell [تعداد] [نام آیتم] - فروش آیتم صید یا شکار  
/gift [تعداد] [نام آیتم] (ریپلای) - هدیه دادن آیتم به دیگران

🎣 /fish - ماهیگیری  
🐗 /hunt - شکار  
/work - کار کردن  
/beg - گدایی

⛏ /mine - استخراج از معدن
/minestatus نشان دادن اطلاعات معدن
/buy_mine خریدن معدن
/upgrade_mine ارتقای معدن

👨‍🌾 /harvest - برداشت از مزرعه  
/farmstatus نمایش دادن اطلاعات مزرعه
/buy_farm [نام آیتم] خریدن اقلام مرتبط با مزرعه
/farm_shop بازار اقلام مرتبط با مزرعه

/buildfactory برای ساخت کارخانه
/upgradefactory برای ارتقا کارخانه
/produce [نام محصول] برای ساخت محصول جدید
/factory برای دریافت محصولات تولید شده
/factory_list برای دیدن محصولات قابل تولید

/business برای دیدن لیست بیزینس های موجود
/buy_business برای خریدن بیزینس
/upgrade_business برای ارتقا بیزینس
/run_business برای شروع بیزینس

🏦 /deposit [مقدار] - واریز به بانک  
/withdraw [مقدار] - برداشت از بانک  
/upgradebank افزایش ظرفیت بانک
/interest گرفتن سود روزانه بانک

/double [مقدار شرط] برای شروع بازی دوبل یا هیچ
/continue برای دوبرابر کردن شرط
/take برای دریافت جایزه دوبل یا هیچ
/slot [شرط] برای بازی اسلات
/guess [حدس] [شرط] برای بازی حدس عدد (اعداد بین 1 تا 10)

💸 /rob (ریپلای) - دزدی از دیگران

/commands - لیست کامل دستورات
"""
    bot.reply_to(message, text, parse_mode="HTML")

bot.polling()
