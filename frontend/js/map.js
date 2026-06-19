//Draws NYC taxi zones on a leaflet map and colors each zone by a chosen 
//number (trips,revenue,etc.). Light basemap so the teal colors stand out.

const ZoneMap = {
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

    //redraw the zones with fresh numbers (called when filters change)
    render(statRows) {
        this.stats = new Map(statRows.map((row) => [row.zone_id, row])); // index stats by zone id
        const values = statRows.map((row) => Number(row[this.metric]))
            .filter((value) => !isNaN(value)); // keep numeric values only
        const breaks = this.makeBreaks(values);

        if (this.layer) this.layer.remove(); // drop the old colored layer

        this.layer = L.geoJSON(this.geojson, {
            //color each zone by its value
            style: (feature) => {
                const row = this.stats.get(feature.properties.location_id);
                return {
                    weight: 0.8, color: "#ffffff",   // thin white border
                    fillColor: this.colorFor(row ? Number(row[this.metric]) : null, breaks),
                    fillOpacity: 0.9,
                };
            },
            // tooltip + hover effect for each zone
            onEachFeature: (feature, zoneLayer) => {    
                const props = feature.properties;
                const row = this.stats.get(props.location_id);

                const lines = ["<b>" + props.zone + "</b>", props.borough]; //tooltip text
                if (row) {
                    lines.push("Trips: " + Number(row.trips).toLocaleString());
                    lines.push("Revenue: $" + this.shortNumber(row.revenue));
                    lines.push("Avg fare: $" + row.avg_fare);
                    lines.push("Avg speed: " + row.avg_speed + " mph");
                } else{
                    lines.push("No pickups under current filters");
                }
                zoneLayer.bindTooltip(lines.join("<br>"), { sticky: true });

                zoneLayer.on("mouseover", () =>   //darken outline on hover
                    zoneLayer.setStyle({ weight: 1.6, color: "#0f766e" }));
                zoneLayer.on("mouseout", () => this.layer.resetStyle(zoneLayer)); //reset on leave
            }
        }).addTo(this.map);
        this.renderLegend(breaks);
    },

    // Color key under the map
    renderLegend(breaks) {
        const el = document.getElementById("map-legend");
        let html = "<span>" + this.METRIC_LABELS[this.metric] + "</span>"; // title
        let low = 0;
        breaks.concat(Infinity).forEach((high, i) => {  //one swatch per band
            const range = high === Infinity ? 
                ">" + this.shortNumber(low) : this.shortNumber(low) + " to " + this.shortNumber(high);
            html += '<span><i class="swatch" style="background:' + this.COLORS[i] + '"></i> ' + range + "</span>";
            low = high;
        });
        el.innerHTML = html;
    }
};