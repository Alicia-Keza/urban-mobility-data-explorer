// Main application object
// This is where we keep track of the state of the application, and where we define the main functions that control the app.

const App = {
    page: 1,                    // which page of the trips table we are on
    sort: "pickup_datetime",        // which column of the trips table we are sorting by
    order: "desc",  
    
    // runs once when the page loads
    async init() {
        this.fillHourBoxes();
        await this.loadFilterOptions();
        await ZoneMap.init();
        this.connectButtons();
        await this.refreshEverything();
    },

    // small message in the top-right corner
    setStatus(text) {
        document.getElementById("status-pill").textContent = text;  
    },

    // fill the two "hour" dropdowns with 00:00 ... 23:00
    fillHourBoxes() {
        const from = document.getElementById("f-hour-from");
        const to = document.getElementById("f-hour-to");
        for (let hour = 0; hour < 24; hour++) {
            const label = String(hour).padStart(2, "0") + ":00";
            from.add(new Option(label, hour));
            to.add(new Option(label, hour));
        }
        from.value = 0;
        to.value = 23;
    },

    // ask the backend for the borough and payment lists, then fill those boxes
    async loadFilterOptions() {
        const meta = await API.get("/meta");
        const boroughBox = document.getElementById("f-borough");
        meta.boroughs.forEach((b) => boroughBox.add(new Option(b, b)));
        const paymentBox = document.getElementById("f-payment");
        meta.payment_types.forEach((p) =>
            paymentBox.add(new Option(p.description, p.payment_type_id)));
    },




}

