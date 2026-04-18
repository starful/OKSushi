// ============================================================
//  OK 시리즈 공통 JS 설정
//  새 프로젝트 만들 때 카테고리/색상만 수정하면 됩니다.
// ============================================================

// 영문 테마키 → 한국어 카테고리명 매핑
// (config.py의 js_category_map과 일치해야 함)
export const CATEGORY_MAP = {
    'tonkotsu': '돈코츠',
    'shoyu':    '쇼유',
    'miso':     '미소',
    'shio':     '시오',
    'chicken':  '치킨라멘',
    'tsukemen': '츠케멘',
    'vegan':    '비건',
};

// 테마별 마커 색상
export const THEME_COLORS = {
    'tonkotsu': '#e67e22',
    'shoyu':    '#845c21',
    'miso':     '#e74c3c',
    'shio':     '#3498db',
    'chicken':  '#f1c40f',
    'tsukemen': '#9b59b6',
    'vegan':    '#27ae60',
    'default':  '#757575',
};
