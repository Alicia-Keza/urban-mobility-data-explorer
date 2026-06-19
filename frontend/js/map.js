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

    // Five cut-offs that split zones into six even-sized groups (so a few busyzones don't make everywhere else look empty)
    makeBreaks(values) {
        if (!values.length) return [];
        const sorted = [...values].sort((a, b) => a - b);  // sort low to high
        const at = (fraction) =>                           // value at a position (0.2 = 20% in)
            sorted[Math.min(sorted.length - 1, Math.floor(fraction * sorted.length))];
        return [at(0.2), at(0.4), at(0.6), at(0.8), at(0.95)];
    },

    // pick a shade: higher value = deeper teal
    colorFor(value, breaks) {
        if (value === undefined || value === null) return "#f1f0ea"; // no data
        let step = 0;
        while (step < breaks.length && value > breaks[step]) step++; // darker per break passed
        return this.COLORS[step];

    },

    //shorten big numbers, e.g. 12000 -> "12.0k"
    shortNumber(value) {
        if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + "M";
        if (value >= 1_000) return (value / 1_000).toFixed(1) + "k";
        return Number(value).toFixed(value % 1 === 0 ? 0 : 1);
    },

    
}