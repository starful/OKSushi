import { getThemeColor, findMainTheme } from './utils.js';

let map;
let allMarkers = [];
let infoWindow;

// ─── Google Maps 로드 대기 ─────────────────────────
async function waitForGoogleMaps() {
    if (window.google && window.google.maps) return;
    return new Promise(resolve => {
        const t = setInterval(() => {
            if (window.google && window.google.maps) {
                clearInterval(t);
                resolve();
            }
        }, 100);
    });
}

// ─── 지도 초기화 ───────────────────────────────────
export async function initGoogleMap(mapId, center = { lat: 36.2, lng: 138.2 }, zoom = 6) {
    await waitForGoogleMaps();
    const { Map } = await google.maps.importLibrary("maps");
    map = new Map(document.getElementById("map"), {
        zoom,
        center,
        mapId,
        mapTypeControl:    false,
        fullscreenControl: false,
        streetViewControl: false,
        gestureHandling:   'greedy',
    });
    infoWindow = new google.maps.InfoWindow();
    _addLocationButton();
    return map;
}

// ─── 마커 렌더링 (사진 원형 마커) ─────────────────
export async function renderPhotoMarkers(items) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    allMarkers.forEach(m => m.map = null);
    allMarkers = [];

    const bounds = new google.maps.LatLngBounds();

    items.forEach(item => {
        if (!item.lat || !item.lng) return;

        const el = document.createElement('div');
        el.className = 'item-marker';
        el.innerHTML = `<img src="${item.thumbnail}" alt="${item.title}" loading="lazy">`;

        const marker = new AdvancedMarkerElement({
            map,
            position: { lat: parseFloat(item.lat), lng: parseFloat(item.lng) },
            title: item.title,
            content: el,
        });

        marker.addListener('click', () => _showInfoWindow(marker, item));
        allMarkers.push(marker);
        bounds.extend(marker.position);
    });

    _fitBounds(items.length, bounds);
}

// ─── 마커 렌더링 (색상 도트 마커) ─────────────────
export async function renderDotMarkers(items) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");

    allMarkers.forEach(m => m.map = null);
    allMarkers = [];

    const bounds = new google.maps.LatLngBounds();

    items.forEach(item => {
        const theme = findMainTheme(item.categories);
        const color = getThemeColor(theme);

        const el = document.createElement('div');
        el.className = 'marker-dot';
        el.style.backgroundColor = color;

        const marker = new AdvancedMarkerElement({
            map,
            position: { lat: parseFloat(item.lat), lng: parseFloat(item.lng) },
            title: item.title,
            content: el,
        });

        marker.itemData = item;
        marker.addListener('click', () => _showInfoWindow(marker, item));
        allMarkers.push(marker);
        bounds.extend(marker.position);
    });

    _fitBounds(items.length, bounds);
}

// ─── 마커 필터링 ───────────────────────────────────
export function filterMarkers(theme) {
    let hasVisible = false;
    allMarkers.forEach(marker => {
        const item = marker.itemData || {};
        const themes = (item.categories || []).map(c => c.toLowerCase());
        const visible = theme === 'all' || themes.includes(theme);
        marker.map = visible ? map : null;
        if (visible) hasVisible = true;
    });
    if (hasVisible) _updateBounds();
}

// ─── 모든 마커 닫기 ───────────────────────────────
export function closeInfoWindow() {
    if (infoWindow) infoWindow.close();
}

// ─── 내부 헬퍼 ────────────────────────────────────
function _showInfoWindow(marker, item) {
    const content = `
        <div class="info-box-content">
            <div class="info-box-title">${item.title}</div>
            <div class="info-box-address">📍 ${item.address || ''}</div>
            <a href="${item.link}" class="info-box-link">View Details →</a>
        </div>`;
    infoWindow.setContent(content);
    infoWindow.open({ anchor: marker, map });
}

function _fitBounds(count, bounds) {
    if (!count || !map) return;
    if (count === 1) {
        map.setCenter(allMarkers[0].position);
        map.setZoom(14);
    } else {
        map.fitBounds(bounds, { padding: 80 });
    }
}

function _updateBounds() {
    const bounds = new google.maps.LatLngBounds();
    let n = 0;
    allMarkers.forEach(m => { if (m.map) { bounds.extend(m.position); n++; } });
    if (n > 0) {
        map.fitBounds(bounds);
    }
}

function _addLocationButton() {
    const btn = document.createElement('button');
    btn.textContent = '🎯 내 위치';
    btn.className = 'location-button';
    btn.style.cssText = 'margin:10px; padding:8px 14px; background:#fff; border:1px solid #ccc; border-radius:20px; cursor:pointer; font-size:13px; box-shadow:0 2px 6px rgba(0,0,0,.2);';
    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(btn);
    btn.onclick = () => {
        if (!navigator.geolocation) return;
        navigator.geolocation.getCurrentPosition(pos => {
            const p = { lat: pos.coords.latitude, lng: pos.coords.longitude };
            map.setCenter(p);
            map.setZoom(14);
        });
    };
}
