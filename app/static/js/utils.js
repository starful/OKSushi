import { CATEGORY_MAP, THEME_COLORS } from './config.js';

/**
 * 카테고리 배열에서 테마 키 목록 반환
 * ex) ["Tonkotsu", "Local Gem"] → ["tonkotsu", "local"]
 */
export function getThemesFromCategories(categories = []) {
    const reverseMap = {};
    for (const [key, val] of Object.entries(CATEGORY_MAP)) {
        reverseMap[val.toLowerCase()] = key;
        reverseMap[key.toLowerCase()]  = key;
    }
    return categories.map(c => reverseMap[c.toLowerCase()] || 'default');
}

/**
 * 카테고리 배열에서 대표 테마 하나 반환
 */
export function findMainTheme(categories = []) {
    const themes = getThemesFromCategories(categories);
    return themes[0] || 'default';
}

/**
 * 테마에 해당하는 색상 반환
 */
export function getThemeColor(theme) {
    return THEME_COLORS[theme] || THEME_COLORS['default'];
}
