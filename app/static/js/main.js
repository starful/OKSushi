/**
 * 🍣 OKSushi Main JavaScript
 * - 다국어 대응 카테고리 매핑 로직 포함
 * - 지도 마커 및 리스트 연동
 */

import { initGoogleMap, renderMarkers, filterItems } from './map-core.js';

// 전역 상태
let allItems = [];
let currentLang = 'en';
const DATA_KEY = 'sushis'; // config.py의 data_key와 일치

/**
 * 💡 한국어 카테고리명을 영어 ID(theme)로 매핑합니다.
 * items.csv나 마크다운에 적힌 카테고리명과 HTML 버튼의 data-theme 값을 연결합니다.
 */
const CATEGORY_MAPPING = {
    // 한국어 -> 영어 ID
    "오마카세": "omakase",
    "에도마에": "edomae",
    "회전초밥": "kaiten",
    "해산물덮밥": "seafood",
    "현지인맛집": "localgem",
    "미슐랭": "michelin",
    "가성비": "affordable",
    "프리미엄": "premium",
    // 영어 명칭 -> 영어 ID (공백 및 특수문자 대응)
    "Seafood Don": "seafood",
    "Local Gem": "localgem",
    "Michelin Star": "michelin"
};

/**
 * 앱 초기화
 */
async function init() {
    console.log("🚀 OKSushi App Starting...");

    // 1. URL 파라미터에서 언어 추출
    const urlParams = new URLSearchParams(window.location.search);
    currentLang = urlParams.get('lang') || 'en';

    // 2. 데이터 가져오기
    await fetchItems();

    // 3. 구글 맵 초기화
    const map = await initGoogleMap();
    
    // 4. 초기 화면 렌더링
    renderMarkers(map, allItems);
    updateListView(allItems);
    updateFilterCounts(allItems); // 상단 숫자 업데이트

    // 5. 필터 버튼 이벤트 바인딩
    setupFilters(map);
}

/**
 * API로부터 현재 언어에 맞는 데이터를 로드합니다.
 */
async function fetchItems() {
    try {
        const response = await fetch(`/api/items?lang=${currentLang}`);
        const data = await response.json();
        
        allItems = data[DATA_KEY] || [];
        
        // 푸터 통계 업데이트
        const totalItemsEl = document.getElementById('total-items');
        if (totalItemsEl) totalItemsEl.textContent = allItems.length;

        const updatedDateEl = document.getElementById('last-updated-date');
        if (updatedDateEl && data.last_updated) {
            updatedDateEl.textContent = data.last_updated;
        }
    } catch (error) {
        console.error("❌ Data load error:", error);
    }
}

/**
 * 💡 필터 버튼 옆의 숫자(Badge)를 업데이트하는 핵심 로직
 */
function updateFilterCounts(items) {
    // 1. 모든 배지를 0으로 초기화
    const countBadges = document.querySelectorAll('.count-badge');
    countBadges.forEach(badge => { badge.textContent = '0'; });

    // 2. 'All' 버튼 숫자 설정
    const allCountBadge = document.getElementById('count-all');
    if (allCountBadge) allCountBadge.textContent = items.length;

    // 3. 아이템별 카테고리 카운트 계산
    items.forEach(item => {
        if (item.categories && Array.isArray(item.categories)) {
            item.categories.forEach(cat => {
                // 매핑 테이블에서 영어 키를 찾거나, 없으면 소문자화/공백제거 수행
                const themeKey = CATEGORY_MAPPING[cat] || cat.toLowerCase().replace(/\s/g, '');
                
                // 해당 themeKey를 ID로 가진 배지 찾기 (예: count-omakase)
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
 * 카테고리 필터 버튼 설정
 */
function setupFilters(map) {
    const filterBtns = document.querySelectorAll('.theme-button');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // UI 상태 변경
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const theme = btn.getAttribute('data-theme');
            
            // map-core.js의 필터 함수 호출
            // (내부적으로 CATEGORY_MAPPING과 유사한 비교 로직이 있어야 함)
            const filtered = filterItems(allItems, theme, CATEGORY_MAPPING);

            // 지도 및 리스트 갱신
            renderMarkers(map, filtered);
            updateListView(filtered);
            
            // 모바일 사용자를 위해 리스트 영역으로 스크롤 (선택 사항)
            if (window.innerWidth < 768 && theme !== 'all') {
                const listSection = document.getElementById('list-section');
                if (listSection) listSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * 하단 맛집 리스트 뷰 생성
 */
function updateListView(items) {
    const listContainer = document.getElementById('item-list');
    if (!listContainer) return;

    if (items.length === 0) {
        const msg = currentLang === 'ko' ? '해당 카테고리의 맛집이 없습니다.' : 'No spots found in this category.';
        listContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 100px 0; color: #aaa;">${msg}</div>`;
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

// DOM 준비 완료 시 실행
document.addEventListener('DOMContentLoaded', init);