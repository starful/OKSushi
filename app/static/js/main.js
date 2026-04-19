/**
 * OKSushi Main JavaScript
 * - 언어 파라미터 감지 및 데이터 로드
 * - 지도 마커 및 리스트 렌더링
 * - 카테고리 필터링 및 숫자 배지 업데이트
 */

import { initGoogleMap, renderMarkers, filterItems } from './map-core.js';

// 전역 상태 관리
let allItems = [];
let currentLang = 'en';
const DATA_KEY = 'sushis'; // config.py의 data_key와 반드시 일치해야 함

/**
 * 앱 시작점
 */
async function init() {
    console.log("🚀 OKSushi initializing...");

    // 1. URL에서 언어 감지 (?lang=ko 또는 ?lang=en)
    const urlParams = new URLSearchParams(window.location.search);
    currentLang = urlParams.get('lang') || 'en';

    // 2. 해당 언어의 데이터 API 호출
    await fetchItems();

    // 3. 구글 맵 초기화 (map-core.js 호출)
    const map = await initGoogleMap();
    
    // 4. 초기 렌더링 (마커, 리스트, 필터 숫자)
    renderMarkers(map, allItems);
    updateListView(allItems);
    updateFilterCounts(allItems);

    // 5. 필터 버튼 이벤트 바인딩
    setupFilters(map);
}

/**
 * API로부터 스시 데이터를 가져옵니다.
 */
async function fetchItems() {
    try {
        // 서버의 /api/items?lang=ko 경로로 요청
        const response = await fetch(`/api/items?lang=${currentLang}`);
        const data = await response.json();
        
        // sushis 키에 담긴 데이터를 전역 변수에 저장
        allItems = data[DATA_KEY] || [];
        
        // 하단 상태바(Footer) 업데이트
        const totalBadge = document.getElementById('total-items');
        if (totalBadge) totalBadge.textContent = allItems.length;

        const dateBadge = document.getElementById('last-updated-date');
        if (dateBadge && data.last_updated) {
            dateBadge.textContent = data.last_updated;
        }
    } catch (error) {
        console.error("❌ Failed to fetch items:", error);
    }
}

/**
 * 상단 카테고리 버튼 옆의 숫자 배지를 업데이트합니다.
 */
function updateFilterCounts(items) {
    // 1. 모든 배지를 0으로 초기화
    const countBadges = document.querySelectorAll('.count-badge');
    countBadges.forEach(badge => { badge.textContent = '0'; });

    // 2. 'All' 버튼 숫자 설정
    const allCount = document.getElementById('count-all');
    if (allCount) allCount.textContent = items.length;

    // 3. 각 아이템의 카테고리를 순회하며 숫자 합산
    items.forEach(item => {
        if (item.categories && Array.isArray(item.categories)) {
            item.categories.forEach(cat => {
                // 공백 제거 및 소문자화하여 ID 매칭 (예: 'Omakase' -> 'count-omakase')
                const safeCatId = `count-${cat.toLowerCase().replace(/\s/g, '')}`;
                const badge = document.getElementById(safeCatId);
                if (badge) {
                    const currentVal = parseInt(badge.textContent) || 0;
                    badge.textContent = currentVal + 1;
                }
            });
        }
    });
}

/**
 * 필터 버튼 클릭 시 동작을 설정합니다.
 */
function setupFilters(map) {
    const filterBtns = document.querySelectorAll('.theme-button');
    
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // 버튼 활성화 상태 변경
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 필터링 실행 (map-core.js의 filterItems 호출)
            const theme = btn.getAttribute('data-theme');
            const filtered = filterItems(allItems, theme);

            // 지도 마커 및 하단 리스트 갱신
            renderMarkers(map, filtered);
            updateListView(filtered);
            
            // 리스트 영역으로 부드럽게 스크롤 (모바일 배려)
            if (window.innerWidth < 768 && theme !== 'all') {
                document.getElementById('list-section').scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

/**
 * 하단 리스트 영역의 HTML을 생성하여 렌더링합니다.
 */
function updateListView(items) {
    const listContainer = document.getElementById('item-list');
    if (!listContainer) return;

    if (items.length === 0) {
        const noResultMsg = currentLang === 'ko' ? '검색 결과가 없습니다.' : 'No results found.';
        listContainer.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 80px 0; color: #999;">${noResultMsg}</div>`;
        return;
    }

    // 카드 리스트 생성
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

// DOM 로드 완료 시 실행
document.addEventListener('DOMContentLoaded', init);