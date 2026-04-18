/**
 * OK 시리즈 공통 Main Engine
 * ─ /api/items 에서 데이터를 받아 지도 + 리스트를 렌더링
 * ─ 언어 전환 / 카테고리 필터 이벤트 처리
 */

import { CATEGORY_MAP } from './config.js';
import { initGoogleMap, renderPhotoMarkers, filterMarkers, closeInfoWindow } from './map-core.js';

// ─── 상태 ──────────────────────────────────────────
let allItems    = [];
let currentLang  = 'en';
let currentTheme = 'all';

// ─── 앱 시작 ───────────────────────────────────────
async function initApp() {
    try {
        const res  = await fetch('/api/items');
        const data = await res.json();
        // data_key는 서버마다 다를 수 있으므로 첫 번째 배열 키를 자동 감지
        const key  = Object.keys(data).find(k => Array.isArray(data[k]));
        allItems   = data[key] || [];

        // 푸터 날짜 업데이트
        const el = document.getElementById('last-updated-date');
        if (el) el.textContent = data.last_updated || '';

        // ⚙️ Maps ID는 index.html의 <script> 안에 넣거나 data 속성으로 전달
        //    여기서는 #map 요소의 data-map-id 속성을 우선 사용
        const mapEl = document.getElementById('map');
        const mapId = mapEl?.dataset.mapId || '';

        await initGoogleMap(mapId);
        updateUI();
    } catch (err) {
        console.error('OKSeries: 초기 로드 실패', err);
    }
}

// ─── UI 통합 업데이트 ──────────────────────────────
async function updateUI() {
    const filtered = getFilteredData();
    renderList(filtered);
    await renderPhotoMarkers(filtered);
    updateCounts();
}

// ─── 데이터 필터링 ─────────────────────────────────
function getFilteredData() {
    return allItems.filter(item => {
        const langOk = item.lang === currentLang;
        let themeOk  = true;
        if (currentTheme !== 'all') {
            const kor = CATEGORY_MAP[currentTheme] || '';
            themeOk = (item.categories || []).some(c =>
                c.toLowerCase() === currentTheme || c === kor
            );
        }
        return langOk && themeOk;
    });
}

// ─── 리스트 렌더링 ─────────────────────────────────
function renderList(data) {
    const container = document.getElementById('item-list');
    if (!container) return;

    if (data.length === 0) {
        container.innerHTML = `
            <div style="grid-column:1/-1; text-align:center; padding:100px 0; color:#999;">
                <p style="font-size:1.2rem;">검색 결과가 없습니다.</p>
            </div>`;
        return;
    }

    container.innerHTML = data.map(item => `
        <div class="onsen-card">
            <a href="${item.link}">
                <img src="${item.thumbnail}" class="card-thumb" alt="${item.title}" loading="lazy">
            </a>
            <div class="card-content">
                <h3 class="card-title"><a href="${item.link}">${item.title}</a></h3>
                <p class="card-summary">${item.summary}</p>
                <div class="card-meta">
                    <span>📍 ${item.address || ''}</span>
                    <span>📅 ${item.published || item.date || ''}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// ─── 카테고리 배지 숫자 업데이트 ──────────────────
function updateCounts() {
    const langData = allItems.filter(i => i.lang === currentLang);

    // 전체 count
    const totalEl = document.getElementById('total-items');
    const allEl   = document.getElementById('count-all');
    if (totalEl) totalEl.textContent = langData.length;
    if (allEl)   allEl.textContent   = langData.length;

    // 각 테마별 count
    for (const [key, kor] of Object.entries(CATEGORY_MAP)) {
        const badge = document.getElementById(`count-${key}`);
        if (!badge) continue;
        const cnt = langData.filter(i =>
            (i.categories || []).some(c =>
                c.toLowerCase() === key || c === kor
            )
        ).length;
        badge.textContent = cnt;
    }
}

// ─── 이벤트: 언어 전환 ─────────────────────────────
document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentLang = btn.dataset.lang;
        closeInfoWindow();
        updateUI();
    });
});

// ─── 이벤트: 카테고리 필터 ─────────────────────────
document.querySelectorAll('.theme-button').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.theme-button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTheme = btn.dataset.theme;
        closeInfoWindow();
        updateUI();

        // 모바일: 리스트 섹션으로 스크롤
        if (window.innerWidth < 768) {
            document.getElementById('list-section')?.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// ─── 앱 실행 ───────────────────────────────────────
initApp();
