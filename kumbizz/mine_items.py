mine_drops = [
    {"name": "سنگ",
    "level_required": 1,
    "chance": 40,
    "base_price": 150},
    {"name": "رغال سنگ",
    "level_required": 1,
    "chance": 30,
    "base_price": 250},
    {"name": "سنگ آهن",
    "level_required": 2,
    "chance": 25,
    "base_price": 300},
    {"name": "سنگ مس",
    "level_required": 3,
    "chance": 20,
    "base_price": 500},
    {"name": "نقره",
    "level_required": 3,
    "chance": 15,
    "base_price": 800},
    {"name": "طلا",
    "level_required": 4,
    "chance": 8,
    "base_price": 2000},
    {"name": "کریستال آبی",
    "level_required": 4,
    "chance": 5,
    "base_price": 3500},
    {"name": "الماس",
    "level_required": 5,
    "chance": 3,
    "base_price": 5500},
    {"name": "سنگ افسانه ای",
    "level_required": 5,
    "chance": 2,
    "base_price": 8000},
    {"name": "اورانیوم",
    "level_required": 6,
    "chance": 2,
    "base_price": 10000},
    {"name": "شهاب سنگ",
    "level_required": 6,
    "chance": 1,
    "base_price": 25000}
]
mine_data = {
    1: {
        "cooldown": 6,
        "count": 1,
        "unlocks": ["سنگ", "زغال سنگ"],
        "level_price": 15000
    },
    2: {
        "cooldown": 5,
        "count": 1,
        "unlocks": ["سنگ آهن"],
        "level_price": 25000
    },
    3: {
        "cooldown": 5,
        "count": 2,
        "unlocks": ["سنگ مس", "نقره"],
        "level_price": 60000
    },
    4: {
        "cooldown": 4,
        "count": 2,
        "unlocks": ["طلا", "کریستال آبی"],
        "level_price": 150000
    },
    5: {
        "cooldown": 4,
        "count": 3,
        "unlocks": ["الماس", "سنگ افسانه ای"],
        "level_price": 350000
    },
    6: {
        "cooldown": 3,
        "count": 4,
        "unlocks": ["اورانیوم", "شهاب سنگ"],
        "level_price": 750000
    }
}
