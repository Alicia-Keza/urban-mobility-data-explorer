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
    async refreshSummary(){
         const stats = await API.get("/summary", API.currentFilters());

    // Show money as $1.2M / $12.3k / $9.50 depending on size.
    function money(amount) {
      if (amount >= 1_000_000) return "$" + (amount / 1_000_000).toFixed(2) + "M";
      if (amount >= 1_000) return "$" + (amount / 1_000).toFixed(1) + "k";
      return "$" + Number(amount).toFixed(2);
    }

    document.getElementById("kpi-trips").textContent =
      Number(stats.trips).toLocaleString();
    document.getElementById("kpi-revenue").textContent = money(stats.revenue || 0);
    document.getElementById("kpi-fare").textContent =
      stats.avg_fare ? "$" + stats.avg_fare.toFixed(2) :"-";
    document.getElementById("kpi-dist").textContent =
      stats.avg_distance ? stats.avg_distance.toFixed(2) + "mi" :"-";
    document.getElementById("kpi-dur").textContent =
      stats.avg_duration ? stats.avg_duration.toFixed(1) + "min" :"-";
    document.getElementById("kpi-speed").textContent =
      stats.avg_speed ? stats.avg_speed.toFixed(1) + "mph" :"-";

    },
    async refreshMap(){
        // colour the map by whatever the map dropdown is set to
        ZoneMap.metric = document.getElementById("map-metric").value;
        const stats = await API.get("/zones/stats",API.currentFilters());
        ZoneMap.render(stats);
    },

    async refreshTopZones(){
        const metric= document.getElementById("top-metric").value;
        const payload = await API.get("/zones/top",{
            ...API.currentFilters(),
            metric: metric,
            k: 10,
            });
            Charts.renderTop(payload);
    },

    async refreshTrends(){
        const filters = API.currentFilters();
        const [hourly, daily] = await Promise.all([
            API.get("/trends/hourly",filters),
        API.get("/trends/daily", filters),
            ]);
            Charts.renderHourly(hourly);
            Charts.renderDaily(daily);
    },
    async refreshBreakdown(){
      const filters = API.currentFilters();
      const [payment, borough]= await Promise.all([
        API.get("/breakdown/payment",filters),
        API.get("/breakdown/borough",filters),
      ]);
      Charts.renderPayment(payment);
      Charts.renderBorough(borough); 
    },

    async refreshTable(){
        const data = await API.get("/trips",{
            ...API.currentFilters(),
            sort:this.sort,
            order:this.order,
            page:this.page,
            limit:25,
        });
        const body = document.querySelector("#trips-table tbody");
    body.innerHTML = data.rows.map((r) =>
      "<tr>" +
        "<td>" + r.pickup_datetime.slice(5, 16) + "</td>" +
        '<td class="route"><b>' + r.pickup_zone + "</b> to " + r.dropoff_zone + "</td>" +
        "<td>" + r.trip_distance.toFixed(2) + "</td>" +
        "<td>" + r.trip_duration_min.toFixed(0) + "</td>" +
        "<td>" + r.avg_speed_mph.toFixed(1) + "</td>" +
        "<td>$" + r.fare_amount.toFixed(2) + "</td>" +
        "<td>$" + r.tip_amount.toFixed(2) + "</td>" +
        "<td><b>$" + r.total_amount.toFixed(2) + "</b></td>" +
        "<td>" + r.payment + "</td>" +
      "</tr>"
    ).join("");

    const pageCount = Math.max(1, Math.ceil(data.total / data.limit));
    if (this.page > pageCount) this.page = pageCount;
    document.getElementById("pg-info").textContent =
      "page " + this.page + " of " + pageCount.toLocaleString();
    document.getElementById("table-count").textContent =
      data.total.toLocaleString() + " trips match";
    document.getElementById("pg-prev").disabled = this.page <= 1;
    document.getElementById("pg-next").disabled = this.page >= pageCount;
    },
};
// starting everything once the page loads
document.addEventListener("DOMContentLoaded", () => App.init());   

