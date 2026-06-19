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




}

