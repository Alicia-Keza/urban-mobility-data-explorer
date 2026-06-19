//Draws NYC taxi zones on a leaflet map and colors each zone by a chosen 
//number (trips,revenue,etc.). Light basemap so the teal colors stand out.

const Zonemap = {
    map: null,  // the leaflet map
    layer: null,  // the colored zones on screen now
    geojson: null,  // zone shapes, loaded once
    stats: new Map(),  // zone_id -> its numbers
    metric: "trips",  // number we color by

    METRIC_LABELS: {
        trips: "Trip count",
        revenue: "Revenue ($)",
        avg_fare: "Avg fare ($)",
        avg_speed: "Avg speed (mph)",   
    },

    //teal shades, light (few) to dark (many)
    COLORS: ["#edf1ef", "#ccfbf1", "#99f6e4", "#2dd4bf", "#0d9488", "#115e59"],
    
    //build the map once and load the zone shapes
    async init() {
        this.map = L.map("map", { zoomControl: true, attributionControl: false })
            .setView([40.71, -73.97], 10);  //center on NYC
        L.tileLayer(
            "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png",
            { maxZoom: 18 }
        ).addTo(this.map);  //light background tiles
        this.geojson = await API.get("/zones/geojson");  //zone outlines, reused on recolor
    },

    
}