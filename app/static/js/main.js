/**
 * 🍣 OKSushi Main JavaScript
 * - 전략적 카테고리 개편 (외국인 선호 키워드)
 * - 다국어 데이터 매핑 및 실시간 숫자 업데이트 로직
 */

import { initGoogleMap, renderMarkers, filterItems } from './map-core.js';

// [전역 상태]
let allItems = [];
let currentLang = 'en';
const DATA_KEY = 'sushis';

/**
 * 💡 카테고리 매핑 사전 (중요)
 * 데이터상의 명칭(KO/EN)을 HTML 버튼의 data-theme 값과 연결합니다.
 */
const CATEGORY_MAP = {
    // 한국어 데이터 -> 영어 ID
    "오마카세": "omakase",
    "회전초밥": "kaiten",
    "미슐랭": "michelin",
    "가성비": "budget",
    "수산시장": "market",
    "혼밥가능": "solo",
    "프리미엄": "premium",
    "현지인맛집": "localgem",

    // 영어 데이터 -> 영어 ID (공백 제거 및 소문자화 대응)
    "Omakase": "omakase",
    "Kaiten": "kaiten",
    "Michelin": "michelin",
    "Michelin Star": "michelin",
    "Budget": "budget",
    "Fish Market": "market",
    "Solo Friendly": "solo",
    "Solo": "solo",
    "Local Gem": "localgem",
    "Premium": "premium"
};

/**
 * 앱 초기화 시작
 */
async function init() {
    console.log("🚀 OKSushi premium engine starting...");

    // 1. URL에서 현재 언어 감지 (?lang=ko 등)
    const urlParams = new URLSearchParams(window.location.search);
    currentLang = urlParams.get('lang') || 'en';

    // 2. 해당 언어의 데이터 가져오기
    await fetchItems();

    // 3. 구글 맵 초기화 (map-core.js)
    const map = await initGoogleMap();
    
    // 4. 초기 화면 렌더링
    renderMarkers(map, allItems);
    updateListView(allItems);
    updateFilterCounts(allItems); // 상단 숫자 배지 업데이트

    // 5. 필터 버튼 이벤트 설정
    setupFilters(map);
}

/**
 * API를 통해 현재 언어에 맞는 스시 데이터를 로드합니다.
 */
async function fetchItems() {
    try {
        const response = await fetch(`/api/items?lang=${currentLang}`);
        const data = await response.json();
        
        allItems = data[DATA_KEY] || [];
        
        // 하단 상태바 정보 업데이트
        const totalEl = document.getElementById('total-items');
        if (totalEl) totalEl.textContent = allItems.length;

        const dateEl = document.getElementById('last-updated-date');
        if (dateEl && data.last_updated) {
            dateEl.textContent = data.last_updated;
        }
    } catch (error) {
        console.error("❌ Data load failed:", error);
    }
}

/**
 * 상단 필터 버튼 옆의 숫자(Badge)를 실시간으로 계산해 표시합니다.
 */
function updateFilterCounts(items) {
    // 모든 배지 0으로 초기화
    document.querySelectorAll('.count-badge').forEach(badge => {
        badge.textContent = '0';
    });

    // 'All' 버튼 숫자 설정
    const allCountBadge = document.getElementById('count-all');
    if (allCountBadge) allCountBadge.textContent = items.length;

    // 카테고리별 합산
    items.forEach(item => {
        if (item.categories && Array.isArray(item.categories)) {
            // 한 아이템이 가진 여러 카테고리를 순회
            item.categories.forEach(cat => {
                // 매핑 사전에서 ID를 찾고, 없으면 소문자/공백제거 변환
                const themeKey = CATEGORY_MAP[cat] || cat.toLowerCase().replace(/\s/g, '');
                
                // 해당 ID를 가진 배지 요소 탐색 (예: count-omakase)
                const badge = document.getElementById(`count-${themeKey}`);
                if (badge) {
                    const currentVal = parseInt(badge.textContent) || 0;
                    badge.textContent = currentVal + 1;
                }
            });
        }
    });
}

/**
 * 필터 버튼 클릭 이벤트 바인딩
 */
function setupFilters(map) {
    const filterBtns = document.querySelectorAll('.theme-button');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 버튼 디자인 활성화 상태 변경
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const selectedTheme = btn.getAttribute('data-theme');

            // 💡 필터링 로직: CATEGORY_MAP을 사용하여 데이터 명칭에 상관없이 매칭
            const filtered = allItems.filter(item => {
                if (selectedTheme === 'all') return true;
                
                return item.categories.some(cat => {
                    const itemThemeId = CATEGORY_MAP[cat] || cat.toLowerCase().replace(/\s/g, '');
                    return itemThemeId === selectedTheme;
                });
            });

            // 지도 마커 및 하단 리스트 갱신
            renderMarkers(map, filtered);
            updateListView(filtered);
            
            // 모바일 사용자를 위해 결과 영역으로 부드러운 스크롤
            if (window.innerWidth < 768 && selectedTheme !== 'all') {
                const listSection = document.getElementById('list-section');
                if (listSection) listSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * 하단 스시 맛집 카드 리스트 렌더링
 */
function updateListView(items) {
    const listContainer = document.getElementById('item-list');
    if (!listContainer) return;

    if (items.length === 0) {
        const emptyMsg = currentLang === 'ko' ? '해당 조건의 맛집을 찾을 수 없습니다.' : 'No sushi spots found.';
        listContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 100px 0; color: #aaa;">${emptyMsg}</div>`;
        return;
    }

    listContainer.innerHTML = items.map(item => `
        <a href="${item.link}?lang=${currentLang}" class="onsen-card">
            <img src="${item.thumbnail}" alt="${item.title}" class="card-thumb" loading="lazy">
            <div class="card-content">
                <h3 class="card-title">${item.title}</h3>
                <p class="card-summary">${item.summary}</p>
                <div class="card-meta">
                    <span>📍 ${item.address}</span>
                </div>
            </div>
        </a>
    `).join('');
}

// 초기화 실행
document.addEventListener('DOMContentLoaded', init);