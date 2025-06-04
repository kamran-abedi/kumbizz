import telebot
from db import init_db, add_user, get_balance, update_balance, add_item, get_inventory, add_xp, get_level, has_item, xp_required, get_best_item_by_type, reduce_item_hp, add_catch, sell_item, transfer_item, apply_daily_interest, upgrade_bank, withdraw, deposit, get_bank_info, init_rob_table, register_rob, can_rob, consume_item, buy_mine, mine_resources, upgrade_mine, effects, set_cooldown, is_on_cooldown, buy_farm_unit, harvest_farm, list_in_market, get_market_list, trade_from_market, cancel_market_item, get_user_missions, claim_mission_rewards, register_mission_action, ensure_user
from items import shop_items
from hunt_data import hunt_list
from fish_data import fish_list
from mine_items import mine_drops
import random
import datetime

bot = telebot.TeleBot("7235180534:AAH_3W3R07_AaHT_QN05RsOGS9Lk5no4ar4")
init_db()
init_rob_table()

def get_id(message):
    telegram_id = message.from_user.id
    return telegram_id

@bot.message_handler(commands=["start"])
def start(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    bot.reply_to(message, "سلام. به دنیای کامبیز خوش اومدی! برای دیدن دستور های موجود بنویسید /commands")

@bot.message_handler(commands=["balance"])
def show_balance(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    balance, bank_balance, bank_capacity = get_bank_info(telegram_id)
    bot.reply_to(message, f"کیف پول: {balance} کوین\nبانک: {bank_balance}/{bank_capacity} کوین")

@bot.message_handler(commands=["beg"])
def beg(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    chance = 90
    chance_percent = random.randint(1, 100)
    if(chance >= chance_percent):
        level, xp = get_level(telegram_id)
        amount = random.randint(10, 100)*(level)
        update_balance(telegram_id, amount)
        bot.reply_to(message, f"یکی دلش سوخت و بهت {amount} تا کامکوین داد!")
    else:
        bot.reply_to(message, "کسی دلش به حالت نسوخت!")
    add_xp(telegram_id, 5)

@bot.message_handler(commands=["shop"])
def shop(message):
    text = "فروشگاه کامبیز:\n"
    for name, info in shop_items.items():
        text += f"{name} - {info['price']} کامبیزکوین\n{info['description']}\n\n"
    text += "برای خرید: /buy [اسم کالا] رو بنویسید."
    bot.reply_to(message, text)

@bot.message_handler(commands=['buy'])
def buy(message):
    try:
        telegram_id = get_id(message)
        add_user(telegram_id)
        item_name = message.text.split(" ", 1)[1]
        item = shop_items.get(item_name)

        if not item:
            bot.reply_to(message, "این کالا وجود نداره.")
            return

        user_balance = get_balance(telegram_id)
        if user_balance < item["price"]:
            bot.reply_to(message, "پول کافی نداری!")
            return

        update_balance(telegram_id, -item["price"])
        add_item(telegram_id, item_name)
        bot.reply_to(message, f"تبریک! تو الان یک '{item_name}' داری.")
    except IndexError:
        bot.reply_to(message, "فرمت درست: /buy [اسم کالا]")

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

    if is_on_cooldown(telegram_id, "work", 2):
        return bot.reply_to(message, "⏳ باید ۲ دقیقه بین هر بار کار کردن فاصله بدی.")
    
    if not has_item(telegram_id, "کت و شلوار"):
        bot.reply_to(message, "برای کار کردن باید یه کت و شلوار بخری تا شبیه کارمندها بشی! (/shop)")
        return

    level, xp = get_level(telegram_id)
    reward = 200*level
    update_balance(telegram_id, reward)
    add_xp(telegram_id, 10)
    set_cooldown(telegram_id, "work")
    register_mission_action(telegram_id, "work")
    bot.reply_to(message, f"آفرین! کار کردی و {reward} کامبیزکوین گرفتی. +10 XP")

from fish_data import fish_list

@bot.message_handler(commands=["fish"])
def fish(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    result = get_best_item_by_type(telegram_id, "fishing rod")

    if is_on_cooldown(telegram_id, "fish", 1):
        return bot.reply_to(message, "⏳ باید یک دقیقه بین هر بار ماهیگیری فاصله بدی.")

    if not result:
        bot.reply_to(message, "نیاز به چوب ماهیگیری داری! برو از فروشگاه بخر.")
        return

    item_name, item = result
    item_rarity = item.get("rarity", "common")
    multiplier = float(item.get("multiplier", 1.0))
    chance = item.get("chance", 50)
    set_cooldown(telegram_id, "fish")

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

    if is_on_cooldown(telegram_id, "hunt", 1):
        return bot.reply_to(message, "⏳ باید یک دقیقه بین هر بار شکار فاصله بدی.")

    if not result:
        bot.reply_to(message, "نیاز به تفنگ داری! برو از فروشگاه بخر.")
        return

    item_name, item = result
    item_rarity = item.get("rarity", "common")
    multiplier = float(item.get("multiplier", 1.0))
    chance = item.get("chance", 50)
    set_cooldown(telegram_id, "hunt")

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

# ساخت دیکشنری قیمت‌ها برای lookup سریع
item_prices = {item["name"]: item["base_price"] for item in (fish_list + hunt_list + mine_drops + farm_sellable)}

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
            bot.reply_to(message, f"{quantity} عدد '{item_name}' رو به {total} کامبیزکوین فروختی!")
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
        if item == "گاز اشک‌آور":
            msg_effect = "گاز اشک‌آور قربانی باعث شد دزدی شکست بخوره!"
            consume_item(victim_id, item)
            return bot.reply_to(message, msg_effect)
        elif item == "سگ نگهبان" and random.random() < 0.5:
            msg_effect = "سگ نگهبان پارس کرد و تو رو فراری داد!"
            return bot.reply_to(message, msg_effect)
        elif item == "کیف زرهی":
            victim_balance //= 2
            msg_effect = "(کیف زرهی مقدار دزدی رو نصف کرد)"

    # محاسبه مقدار دزدی
    steal_amount = random.randint(int(victim_balance * 0.05), int(victim_balance * 0.15))
    steal_amount = min(steal_amount, 5000)

    update_balance(victim_id, -steal_amount)
    update_balance(thief_id, steal_amount)
    register_rob(thief_id)  # ثبت زمان برای cooldown
    register_mission_action(thief_id, "rob")
    thief_level, ksshr = get_level(thief_id) 
    xp_gain = 10 * thief_level
    add_xp(thief_id, xp_gain)

    bot.reply_to(message, f"تو {steal_amount} کوین از کیف پول قربانی دزدیدی! {msg_effect} +{xp_gain}XP")

@bot.message_handler(commands=["buy_mine"])
def handle_buy_mine(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = buy_mine(telegram_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["mine"])
def handle_mine(message):
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = mine_resources(telegram_id)
    register_mission_action(telegram_id, "mine")
    bot.reply_to(message, msg)

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
    success, msg = upgrade_mine(telegram_id)
    bot.reply_to(message, msg)

@bot.message_handler(commands=["minestatus"])
def handle_mine_status(message):
    telegram_id = get_id(message)
    from db import get_mine_status
    success, msg = get_mine_status(telegram_id)
    bot.reply_to(message, msg, parse_mode="HTML")

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
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        return bot.reply_to(message, "فرمت: /buy_farm [نوع واحد مزرعه]")

    unit_type = parts[1].strip()
    telegram_id = get_id(message)
    add_user(telegram_id)
    success, msg = buy_farm_unit(telegram_id, unit_type)
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
        text += (
            f"• <b>{name}</b>\n"
            f"  💰 قیمت: {price} سکه\n"
            f"  🌾 تولید: {product} هر {interval} ساعت\n\n"
        )

    bot.reply_to(message, text, parse_mode="HTML")

@bot.message_handler(commands=["list"])
def handle_list(message):
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
    bot.reply_to(message, "🎁 پاداش روزانه گرفتی: 1000 سکه!")

@bot.message_handler(commands=["weekly"])
def handle_weekly(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    if not can_claim_reward(telegram_id, "weekly"):
        return bot.reply_to(message, "🕓 پاداش هفتگی‌ات رو این هفته گرفتی. هفته بعد بیا!")

    update_balance(telegram_id, 10000)
    update_reward_claim_time(telegram_id, "weekly")
    bot.reply_to(message, "🎁 پاداش هفتگی گرفتی: 10000 سکه!")

@bot.message_handler(commands=["monthly"])
def handle_monthly(message):
    telegram_id = get_id(message)
    add_user(telegram_id)

    if not can_claim_reward(telegram_id, "monthly"):
        return bot.reply_to(message, "🕓 این ماه پاداشت رو گرفتی. ماه بعد بیا!")

    update_balance(telegram_id, 100000)
    update_reward_claim_time(telegram_id, "monthly")
    bot.reply_to(message, "🎁 پاداش ماهانه گرفتی: 100000 سکه!")

@bot.message_handler(commands=["commands", "help"])
def handle_commands(message):
    text = """
🧾 <b>دستورات بات کامبیز</b>

/daily جایزه روزانه
/weekly جایزه هفتگی
/monthly جایزه ماهانه

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

🎯 /missions - دیدن ماموریت‌های روز  
/claimmissions - دریافت جوایز ماموریت‌ها

🏦 /deposit [مقدار] - واریز به بانک  
/withdraw [مقدار] - برداشت از بانک  
/upgradebank افزایش ظرفیت بانک
/interest گرفتن سود روزانه بانک

💸 /rob (ریپلای) - دزدی از دیگران

/commands - لیست کامل دستورات
"""
    bot.reply_to(message, text, parse_mode="HTML")

bot.polling()
