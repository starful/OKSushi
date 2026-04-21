# app/config.py

SITE_CONFIG = {
    "project_name":  "oksushi",
    "site_name":     "OKSushi",
    "site_url":      "https://oksushi.net",
    "tagline":       "Discover the Finest Sushi in Japan",
    "data_key":      "sushis",

    "ga_id":         "G-43EXEQCKYT",  # 새 GA4 ID
    "maps_api_key":  "AIzaSyD8wYazKeD2fX4ZJhSHbzuCw9AE7cBjS7I",
    "maps_id":       "2938bb3f7f034d786b85aac4",

    "emoji":         "🍣",
    "accent_color":  "#c0392b",       # 신선한 참치(Maguro)의 진한 레드
    "bg_dot_color":  "#eaddca",       # 히노키(편백나무) 도마의 연한 베이지 색상

    "filter_buttons": [
        {"label_en": "All",        "label_ko": "전체",    "theme": "all",       "count_id": "count-all"},
        {"label_en": "🍱 Omakase",  "label_ko": "오마카세", "theme": "omakase",   "count_id": "count-omakase"},
        {"label_en": "🌟 Michelin", "label_ko": "미슐랭",   "theme": "michelin",  "count_id": "count-michelin"},
        {"label_en": "🔄 Kaiten",   "label_ko": "회전초밥", "theme": "kaiten",    "count_id": "count-kaiten"},
        {"label_en": "🐟 Market",   "label_ko": "시장스시", "theme": "market",    "count_id": "count-market"},
        {"label_en": "💰 Value",    "label_ko": "가성비",   "theme": "budget",    "count_id": "count-budget"},
        {"label_en": "🙋 Solo",     "label_ko": "혼밥",     "theme": "solo",      "count_id": "count-solo"},
        {"label_en": "🍶 Sake",     "label_ko": "사케/술",  "theme": "pairing",   "count_id": "count-pairing"},
    ],

    "category_mapping": {
        "오마카세": "Omakase",
        "미슐랭": "Michelin",
        "회전초밥": "Kaiten",
        "시장스시": "Market",
        "가성비": "Budget",
        "혼밥": "Solo",
        "사케/술": "Pairing"
    },

    "js_category_map": {
        "omakase": "오마카세",
        "edomae":  "에도마에",
        "kaiten":  "회전초밥",
        "seafood": "해산물덮밥",
    },

    "schema_type": "Restaurant",
    "guide_images": [
        # --- 기존 이미지 (4개) ---
        "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1553621042-f6e147245754?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1583623025817-d180a2221d0a?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1512132411229-c30391241dd8?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1476124369491-e7addf5db371?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1611143669185-af224c5e3252?q=80&w=800&auto=format&fit=crop"
    ],
    "footer_tagline": "The ultimate guide to the best sushi experiences in Japan.",
    "footer_year": "2025",
}