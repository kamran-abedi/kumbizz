factory_data = {
    "آهن": {
        "inputs": {"سنگ آهن": 1},
        "time": 600,
        "description": "فراوری سنگ آهن به آهن"
    },
    "مس": {
        "inputs": {"سنگ مس": 1},
        "time": 600,
        "description": "فراوری سنگ مس به مس"
    },
    "آرد": {
        "inputs": {"گندم": 1},
        "time": 300,
        "description": "تبدیل گندم به آرد"
    },
    "نان": {
        "inputs": {"آرد": 1},
        "time": 600,
        "description": "پای ثابت اکثر غذا ها"
    },
    "کیک": {
        "inputs": {"آرد": 1, "شیر": 1},
        "time": 1200,
        "description": "ترکیب آرد و شیر برای پخت کیک"
    },
    "لباس سنتی": {
        "inputs": {"پشم": 1, "گیاه دارویی": 1},
        "time": 2400,
        "description": "ساخت لباس سنتی از پشم"
    },
    "شمع طبی": {
        "inputs": {"عسل": 1, "گیاه دارویی": 1},
        "time": 2400,
        "description": "ترکیب عسل و گیاه دارویی"
    },
    "آبجو": {
        "inputs": {"جو": 2},
        "time": 600,
        "description": "تخمیر جو برای تهیه آبجو"
    },
    "شمش طلا": {
        "inputs": {"طلا": 1},
        "time": 900,
        "description": "ذوب طلا به شمش"
    },
    "شیشه کریستال": {
        "inputs": {"کریستال آبی": 1, "سنگ": 1},
        "time": 1800,
        "description": "ساخت کریستال صنعتی"
    },
    "تیتاپ": {
        "inputs": {"کیک": 1, "عسل": 1},
        "time": 2400,
        "description": "کیک حرفه ای با طعمی نوستالژیک"
    },
    "زره آهنین": {
        "inputs": {"پشم": 2, "آهن": 1},
        "time": 1200,
        "description": "مناسب برای جنگ"
    },
    "پاپ کورن": {
        "inputs": {"ذرت": 1},
        "time": 600,
        "description": "غذای مخصوص فیلم دیدن"
    },
    "آجر": {
        "inputs": {"سنگ": 2},
        "time": 450,
        "description": "مناسب برای ساخت و ساز"
    },
    "بالشت": {
        "inputs": {"پر": 2},
        "time": 900,
        "description": "کالای خواب"
    },
    "پنیر": {
        "inputs": {"شیر": 2},
        "time": 600,
        "description": "مناسب برای صبحانه ای مفید"
    },
    "نون و پنیر": {
        "inputs": {"نان" : 2, "پنیر": 1},
        "time": 1200,
        "description": "صبحانه ای مقوی"
    },
    "کره": {
        "inputs": {"شیر": 3},
        "time": 750,
        "description": "حاوی مقادیر زیاد کلسیم"
    }
}
factory_levels = {
    1: {
        "cooldown": 600,
        "price": 100_000,
        "slots": 1
    },
    2: {
        "cooldown": 450,
        "price": 250_000,
        "slots": 2
    },
    3: {
        "cooldown": 300,
        "price": 500_000,
        "slots": 3
    },
    4: {
        "cooldown": 180,
        "price": 1_000_000,
        "slots": 4
    },
    5: {
        "cooldown": 120,
        "price": 2_000_000,
        "slots": 5
    }
}
factory_sellable = [
    {"name": "آهن", "base_price": 500},
    {"name": "مس", "base_price": 800},
    {"name": "آرد", "base_price": 150},
    {"name": "نان", "base_price": 300},
    {"name": "کیک", "base_price": 500},
    {"name": "لباس سنتی", "base_price": 1200},
    {"name": "شمع طبی", "base_price": 1300},
    {"name": "آبجو", "base_price": 500},
    {"name": "شمش طلا", "base_price": 3500},
    {"name": "شیشه کریستال", "base_price": 5000},
    {"name": "تیتاپ", "base_price": 1800},
    {"name": "زره آهنین", "base_price": 1400},
    {"name": "پاپ کورن", "base_price": 800},
    {"name": "آجر", "base_price": 400},
    {"name": "بالشت", "base_price": 1800},
    {"name": "پنیر", "base_price": 500},
    {"name": "نون و پنیر", "base_price": 1000},
    {"name": "کره", "base_price": 700}
]