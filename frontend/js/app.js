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

    // wire up the buttons, dropdowns and sortable table headers    

    connectButtons() {
        document.getElementById("btn-apply").addEventListener("click", () => {
            this.page = 1;
            this.refreshEverything();
        });

        document.getElementById("btn-reset").addEventListener("click", () => {
            document.getElementById("f-date-from").value = "2019-01-01";
            document.getElementById("f-date-to").value = "2019-01-31";
            document.getElementById("f-hour-from").value = 0;
            document.getElementById("f-hour-to").value = 23;

            ["f-borough", "f-payment","f-min-fare", "f-max-fare",
                "f-min-dist", "f-max-dist"].forEach((id) => {
                document.getElementById(id).value = "";
            });
            this.page = 1;
            this.refreshEverything();
        });

        // switching the map metric only needs the map redrawn
        document.getElementById("map-metric").addEventListener("change", (event) => {
            this.refreshMap();
        });
        // switching the top-zones metric only needs the top-zones redrawn
        document.getElementById("top-metric").addEventListener("change", () => {
            this.refreshTopZones();
        });
          // Clicking a table header sorts by that column. Clicking it again flips

    document.querySelectorAll("#trips-table th[data-sort]").forEach((header) => {
      header.addEventListener("click", () => {
        const column = header.dataset.sort;
        if (this.sort === column) {
          this.order = this.order === "desc" ? "asc" : "desc";
        } else {
          this.sort = column;
          this.order = "desc";
        }
        document.querySelectorAll("#trips-table th").forEach((h) =>
          h.classList.toggle("active", h === header));
        this.page = 1;
        this.refreshTable();
      });
    });
    document.getElementById("pg-prev").addEventListener("click", () => {
        if (this.page > 1) {
            this.page--;
            this.refreshTable();
        }
    });
    document.getElementById("pg-next").addEventListener("click", () => {
        this.page++;
        this.refreshTable();
    });
    },
    //refreshing the dashboard means refreshing the map, top-zones chart and trips table

    async refreshEverything() {
        this.setStatus("counting trips...");
        try{
             await Promise.all([
             this.refreshSummary(),
             this.refreshMap(),
                this.refreshTopZones(),
                this.refreshTrends(),
                this.refreshBreakdown(),
                this.refreshTable(),            
            ]);
            this.setStatus("");
        } catch(error){
            console.error(error);
            this,this.setStatus("something went wrong, check the console");

        }
           
    },
    
}    

