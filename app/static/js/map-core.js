/**
 * 🍣 OKSushi 지도 엔진
 * - Maguro Red 테마 마커 적용
 * - 필터 로직 포함
 */

/**
 * 구글 맵 초기화
 */
export async function initGoogleMap() {
    const { Map } = await google.maps.importLibrary("maps");
    
    const map = new Map(document.getElementById("map"), {
        center: { lat: 36.5, lng: 138.0 },
        zoom: 6,
        mapId: "OKSUSHI_MAP_ID", // 실제 ID가 없어도 작동합니다
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: false,
        styles: [ // 지도를 조금 더 깔끔하게 (선택 사항)
            { featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }
        ]
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
        // 스시 테마: Maguro Red (#c0392b) 핀
        const pin = new PinElement({
            background: "#c0392b",
            borderColor: "#ffffff",
            glyphColor: "#ffffff",
            scale: 0.9
        });

        const marker = new AdvancedMarkerElement({
            map,
            position: { lat: item.lat, lng: item.lng },
            content: pin.element,
            title: item.title
        });

        marker.addListener("click", () => {
            const contentString = `
                <div class="info-box-content" style="padding:10px; max-width:200px;">
                    <div style="font-weight:bold; font-size:14px; margin-bottom:5px;">${item.title}</div>
                    <div style="font-size:12px; color:#666; margin-bottom:10px;">${item.address}</div>
                    <a href="${item.link}" style="display:block; text-align:center; background:#c0392b; color:white; padding:8px; border-radius:4px; font-size:12px; font-weight:bold; text-decoration:none;">
                        🍣 맛집 보기
                    </a>
                </div>
            `;
            infoWindow.setContent(contentString);
            infoWindow.open(map, marker);
        });

        markers.push(marker);
    });

    // 화면 범위 조정
    if (items.length > 0 && map) {
        const bounds = new google.maps.LatLngBounds();
        items.forEach(i => bounds.extend({ lat: i.lat, lng: i.lng }));
        
        if (items.length === 1) {
            map.setCenter(bounds.getCenter());
            map.setZoom(15);
        } else {
            map.fitBounds(bounds, { padding: 50 });
        }
    }
}

/**
 * 아이템 필터링 (main.js에서 호출)
 */
export function filterItems(items, theme) {
    if (!theme || theme === 'all') return items;
    
    return items.filter(item => {
        if (!item.categories) return false;
        // 카테고리 명칭 정규화 (공백 제거, 소문자화) 비교
        return item.categories.some(cat => 
            cat.toLowerCase().replace(/\s/g, '') === theme.toLowerCase().replace(/\s/g, '')
        );
    });
}