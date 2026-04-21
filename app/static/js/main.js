/**
 * 🍣 OKSushi Main JavaScript
 * - 실시간 카테고리 카운팅 엔진
 * - 다국어 데이터 매핑 로직
 */

import { initGoogleMap, renderMarkers, filterItems } from './map-core.js';

// 전역 상태
let allItems = [];
let currentLang = 'en';
const DATA_KEY = 'sushis';

/**
 * 💡 데이터상의 명칭을 HTML theme ID와 연결하는 매핑 테이블
 */
const CATEGORY_MAP = {
    // 한국어 명칭 -> theme ID
    "오마카세": "omakase",
    "미슐랭": "michelin",
    "회전초밥": "kaiten",
    "시장스시": "market",
    "가성비": "budget",
    "혼밥": "solo",
    "사케/술": "pairing",

    // 영어 명칭 -> theme ID
    "Omakase": "omakase",
    "Michelin": "michelin",
    "Kaiten": "kaiten",
    "Market": "market",
    "Value": "budget",
    "Solo": "solo",
    "Sake": "pairing"
};

/**
 * 앱 초기화
 */
async function init() {
    console.log("🚀 OKSushi premium engine starting...");

    // 1. URL 파라미터에서 현재 언어 감지
    const urlParams = new URLSearchParams(window.location.search);
    currentLang = urlParams.get('lang') || 'en';

    // 2. 서버 데이터 가져오기
    await fetchItems();

    // 3. 지도 초기화
    const map = await initGoogleMap();
    
    // 4. 초기 렌더링
    renderMarkers(map, allItems);
    updateListView(allItems);
    updateFilterCounts(allItems); // 💡 여기서 숫자 업데이트

    // 5. 필터 버튼 이벤트 바인딩
    setupFilters(map);
}

/**
 * API 호출 및 데이터 저장
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
        console.error("❌ Data load error:", error);
    }
}

/**
 * 💡 필터 버튼 옆의 숫자 배지를 정확하게 계산하여 표시
 */
function updateFilterCounts(items) {
    // 1. 모든 배지를 0으로 초기화
    document.querySelectorAll('.count-badge').forEach(badge => {
        badge.textContent = '0';
    });

    // 2. '전체(All)' 버튼 숫자 설정
    const allCountBadge = document.getElementById('count-all');
    if (allCountBadge) allCountBadge.textContent = items.length;

    // 3. 아이템별 카테고리 카운트 합산
    items.forEach(item => {
        if (item.categories && Array.isArray(item.categories)) {
            item.categories.forEach(cat => {
                // 매핑 테이블에서 테마 ID 추출 (없으면 공백제거/소문자 기본값)
                const themeId = CATEGORY_MAP[cat] || cat.toLowerCase().replace(/\s/g, '');
                
                // HTML의 id="count-테마명" 요소를 찾아 숫자 증가
                const badge = document.getElementById(`count-${themeId}`);
                if (badge) {
                    const currentVal = parseInt(badge.textContent) || 0;
                    badge.textContent = currentVal + 1;
                }
            });
        }
    });
}

/**
 * 필터 버튼 클릭 처리
 */
function setupFilters(map) {
    const filterBtns = document.querySelectorAll('.theme-button');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 버튼 활성화 상태 변경
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const selectedTheme = btn.getAttribute('data-theme');

            // 💡 필터링 로직: 매핑 사전을 활용하여 데이터 명칭에 상관없이 매칭
            const filtered = allItems.filter(item => {
                if (selectedTheme === 'all') return true;
                return item.categories.some(cat => {
                    const itemThemeId = CATEGORY_MAP[cat] || cat.toLowerCase().replace(/\s/g, '');
                    return itemThemeId === selectedTheme;
                });
            });

            // 지도 및 리스트 갱신
            renderMarkers(map, filtered);
            updateListView(filtered);
        });
    });
}

/**
 * 하단 맛집 리스트 렌더링
 */
function updateListView(items) {
    const listContainer = document.getElementById('item-list');
    if (!listContainer) return;

    if (items.length === 0) {
        const msg = currentLang === 'ko' ? '해당 조건의 맛집이 없습니다.' : 'No spots found.';
        listContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 100px 0; color: #999;">${msg}</div>`;
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

// 부팅
document.addEventListener('DOMContentLoaded', init);