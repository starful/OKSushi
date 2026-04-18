/**
 * 구글 맵 초기화
 */
export async function initGoogleMap() {
    const { Map } = await google.maps.importLibrary("maps");
    
    // 일본 중심 위치
    const map = new Map(document.getElementById("map"), {
        center: { lat: 36.5, lng: 138.0 },
        zoom: 6,
        mapId: "YOUR_MAP_ID", // 실제 구글 클라우드 맵 ID가 있다면 입력
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false
    });

    return map;
}

/**
 * 마커 렌더링
 */
let markers = [];
export async function renderMarkers(map, items) {
    const { AdvancedMarkerElement, PinElement } = await google.maps.importLibrary("marker");

    // 기존 마커 제거
    markers.forEach(m => m.map = null);
    markers = [];

    const infoWindow = new google.maps.InfoWindow();

    items.forEach(item => {
        // 스시 테마에 맞는 빨간색 핀 생성
        const pin = new PinElement({
            background: "#c0392b",
            borderColor: "#ffffff",
            glyphColor: "#ffffff",
            scale: 0.8
        });

        const marker = new AdvancedMarkerElement({
            map,
            position: { lat: item.lat, lng: item.lng },
            content: pin.element,
            title: item.title
        });

        marker.addListener("click", () => {
            infoWindow.setContent(`
                <div class="info-box-content" style="padding:10px;">
                    <div class="info-box-title" style="font-weight:bold;margin-bottom:5px;">${item.title}</div>
                    <div class="info-box-address" style="font-size:12px;color:#666;margin-bottom:10px;">${item.address}</div>
                    <a href="${item.link}" class="info-box-link" style="display:inline-block;background:#c0392b;color:white;padding:5px 10px;border-radius:15px;text-decoration:none;font-size:12px;">View Details</a>
                </div>
            `);
            infoWindow.open(map, marker);
        });

        markers.push(marker);
    });

    // 마커 범위에 따라 지도 자동 조정
    if (items.length > 0 && map) {
        const bounds = new google.maps.LatLngBounds();
        items.forEach(i => bounds.extend({ lat: i.lat, lng: i.lng }));
        
        if (items.length === 1) {
            map.setCenter(bounds.getCenter());
            map.setZoom(15);
        } else {
            map.fitBounds(bounds);
        }
    }
}

/**
 * ✅ 핵심: 이 함수가 export 되어 있어야 main.js에서 쓸 수 있습니다.
 */
export function filterItems(items, theme) {
    if (!theme || theme === 'all') {
        return items;
    }
    
    // theme: 'omakase', 'edomae' 등
    // item.categories: ['Omakase', 'Premium'] 등
    return items.filter(item => 
        item.categories && item.categories.some(cat => 
            cat.toLowerCase().replace(/\s/g, '') === theme.toLowerCase().replace(/\s/g, '')
        )
    );
}