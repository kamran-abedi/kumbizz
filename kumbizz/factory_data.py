factory_data = {
    "آهن": {
        "inputs": {"سنگ آهن": 1},
        "time": 600_000,
        "description": "فراوری سنگ آهن به آهن"
    },
    "مس": {
        "inputs": {"سنگ مس": 1},
        "time": 600_000,
        "description": "فراوری سنگ مس به مس"
    },
    "آرد": {
        "inputs": {"گندم": 1},
        "time": 300_000,
        "description": "تبدیل گندم به آرد"
    },
    "نان": {
        "inputs": {"آرد": 1},
        "time": 600_000,
        "description": "پای ثابت اکثر غذا ها"
    },
    "کیک": {
        "inputs": {"آرد": 1, "شیر": 1},
        "time": 900_000,
        "description": "ترکیب آرد و شیر برای پخت کیک"
    },
    "لباس سنتی": {
        "inputs": {"پشم": 1, "گیاه دارویی": 1},
        "time": 1200_000,
        "description": "ساخت لباس سنتی از پشم"
    },
    "شمع طبی": {
        "inputs": {"عسل": 1, "گیاه دارویی": 1},
        "time": 1200_000,
        "description": "ترکیب عسل و گیاه دارویی"
    },
    "آبجو": {
        "inputs": {"جو": 2},
        "time": 600_000,
        "description": "تخمیر جو برای تهیه آبجو"
    },
    "شمش طلا": {
        "inputs": {"طلا": 1},
        "time": 900_000,
        "description": "ذوب طلا به شمش"
    },
    "شیشه کریستال": {
        "inputs": {"کریستال آبی": 1, "سنگ": 1},
        "time": 1800_000,
        "description": "ساخت کریستال صنعتی"
    },
    "تیتاپ": {
        "inputs": {"کیک": 1, "عسل": 1},
        "time": 1800_000,
        "description": "کیک حرفه ای با طعمی نوستالژیک"
    },
    "زره آهنین": {
        "inputs": {"پشم": 2, "آهن": 1},
        "time": 1200_000,
        "description": "مناسب برای جنگ"
    },
    "پاپ کورن": {
        "inputs": {"ذرت": 1},
        "time": 600_000,
        "description": "غذای مخصوص فیلم دیدن"
    },
    "آجر": {
        "inputs": {"سنگ": 2},
        "time": 450_000,
        "description": "مناسب برای ساخت و ساز"
    },
    "بالشت": {
        "inputs": {"پر": 2},
        "time": 900_000,
        "description": "کالای خواب"
    },
    "پنیر": {
        "inputs": {"شیر": 2},
        "time": 600_000,
        "description": "مناسب برای صبحانه ای مفید"
    },
    "نون و پنیر": {
        "inputs": {"نان" : 2, "پنیر": 1},
        "time": 1200_000,
        "description": "صبحانه ای مقوی"
    },
    "کره": {
        "inputs": {"شیر": 3},
        "time": 750_000,
        "description": "حاوی مقادیر زیاد کلسیم"
    }
}
factory_levels = {
    1: {
        "price": 50_000,
        "slots": 1
    },
    2: {
        "price": 100_000,
        "slots": 2
    },
    3: {
        "price": 150_000,
        "slots": 3
    },
    4: {
        "price": 200_000,
        "slots": 4
    },
    5: {
        "price": 250_000,
        "slots": 5
    },
    6: {
        "price": 300_000,
        "slots": 6
    },
    7: {
        "price": 350_000,
        "slots": 7
    },
    8: {
        "price": 400_000,
        "slots": 8
    },
    9: {
        "price": 450_000,
        "slots": 9
    },
    10: {
        "price": 500_000,
        "slots": 10
    },
    11: {
        "price": 550_000,
        "slots": 11
    },
    12: {
        "price": 600_000,
        "slots": 12
    },
    13: {
        "price": 650_000,
        "slots": 13
    },
    14: {
        "price": 700_000,
        "slots": 14
    },
    15: {
        "price": 750_000,
        "slots": 15
    },
    16: {
        "price": 800_000,
        "slots": 16
    },
    17: {
        "price": 850_000,
        "slots": 17
    },
    18: {
        "price": 900_000,
        "slots": 18
    },
    19: {
        "price": 950_000,
        "slots": 19
    },
    20: {
        "price": 1_000_000,
        "slots": 20
    }
}
factory_sellable = [
    {"name": "آهن", "base_price": 800},                
    {"name": "مس", "base_price": 1100},              
    {"name": "آرد", "base_price": 150},             
    {"name": "نان", "base_price": 350},            
    {"name": "کیک", "base_price": 600},           
    {"name": "لباس سنتی", "base_price": 1000},      
    {"name": "شمع طبی", "base_price": 1200},      
    {"name": "آبجو", "base_price": 450},          
    {"name": "شمش طلا", "base_price": 4800},        
    {"name": "شیشه کریستال", "base_price": 9000},   
    {"name": "تیتاپ", "base_price": 1500},          
    {"name": "زره آهنین", "base_price": 2000},      
    {"name": "پاپ کورن", "base_price": 750},      
    {"name": "آجر", "base_price": 600},            
    {"name": "بالشت", "base_price": 2500},        
    {"name": "پنیر", "base_price": 650},           
    {"name": "نون و پنیر", "base_price": 3200},     
    {"name": "کره", "base_price": 950},             
    {"name": "نیمرو", "base_price": 250},
    {"name": "لباس", "base_price": 400}
]
