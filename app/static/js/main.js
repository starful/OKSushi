import { initGoogleMap, renderMarkers, filterItems } from './map-core.js';

let allItems = [];
let currentLang = 'en';
const DATA_KEY = 'sushis'; // config.py와 동일하게 설정

async function init() {
    const urlParams = new URLSearchParams(window.location.search);
    currentLang = urlParams.get('lang') || 'en';

    // 1. 데이터 가져오기
    await fetchItems();

    // 2. 구글 맵 초기화
    const map = await initGoogleMap();
    
    // 3. 초기 렌더링
    renderMarkers(map, allItems);
    updateListView(allItems);
    updateFilterCounts(allItems);

    // 4. 필터 이벤트 설정
    setupFilters(map);

    // 5. 언어 전환 설정
    setupLanguageToggle(map);
}

async function fetchItems() {
    try {
        const response = await fetch(`/api/items?lang=${currentLang}`);
        const data = await response.json();
        
        // 데이터 키 참조: data.sushis
        allItems = data[DATA_KEY] || [];
        
        // 푸터 정보 업데이트
        document.getElementById('total-items').textContent = allItems.length;
        if (data.last_updated) {
            document.getElementById('last-updated-date').textContent = data.last_updated;
        }
    } catch (error) {
        console.error("❌ 데이터 로드 실패:", error);
    }
}

function updateFilterCounts(items) {
    // 모든 필터 숫자를 0으로 초기화
    const countBadges = document.querySelectorAll('.count-badge');
    countBadges.forEach(badge => badge.textContent = '0');

    // 전체 개수
    const totalBadge = document.getElementById('count-all');
    if (totalBadge) totalBadge.textContent = items.length;

    // 카테고리별 개수 계산
    items.forEach(item => {
        if (item.categories) {
            item.categories.forEach(cat => {
                const lowerCat = cat.toLowerCase().replace(/\s/g, '');
                const badge = document.getElementById(`count-${lowerCat}`);
                if (badge) {
                    badge.textContent = parseInt(badge.textContent) + 1;
                }
            });
        }
    });
}

function setupFilters(map) {
    const filterBtns = document.querySelectorAll('.theme-button');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const theme = btn.getAttribute('data-theme');
            const filtered = filterItems(allItems, theme);

            renderMarkers(map, filtered);
            updateListView(filtered);
        });
    });
}

function updateListView(items) {
    const listContainer = document.getElementById('item-list');
    if (!listContainer) return;

    if (items.length === 0) {
        listContainer.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 100px 20px; color: #888;">No sushi spots found in this category.</div>';
        return;
    }

    listContainer.innerHTML = items.map(item => `
        <a href="${item.link}" class="onsen-card">
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

function setupLanguageToggle(map) {
    const btns = document.querySelectorAll('.lang-btn[data-lang]');
    btns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const lang = e.target.getAttribute('data-lang');
            if (lang === currentLang) return;

            // 가이드 카드 토글
            document.querySelectorAll('.guide-card').forEach(c => c.style.display = 'none');
            document.querySelectorAll(`.guide-${lang}`).forEach(c => c.style.display = 'flex');

            currentLang = lang;
            await fetchItems();
            renderMarkers(map, allItems);
            updateListView(allItems);
            updateFilterCounts(allItems);
        });
    });
}

document.addEventListener('DOMContentLoaded', init);