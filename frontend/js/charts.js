// Charting functions
// This file contains functions for creating and updating charts using Chart.js library
// The charts are used to visualize data such as trips, average speed, and other metrics

Chart.defaults.font.family = "Inter, sans-serif";

const Charts = {
    saved: {},   // keeps the current chart objects so we can destroy them
    // Colors used across the charts.
    BLACK: "#151413",
    GREEN: "#0d948f",
    TEAL: "rgba(24, 167, 155, 0.55)",
    GRAY: "#636261",
    // Used for the pie slices.
    PALETTE: ["#0d948f", "#636361", "#d8d5cc", "#8b887f", "#99f6e4", "#151413"],  
    
    
    // Plain axis styling
    axis() {
        return {
            ticks: { color: "#8b887f", font: { size: 11 } },
            grid: { color: "rgba(26,25,23,0.06)" },
            border: { color: "rgba(26,25,23,0.08)" },
        };
    },

    // Shorten big numbers on an axis
    shorten(value) {
        if (typeof value !== "number") return value;
        if (value >= 1_000_000) return (value / 1_000_000).toFixed(1) + "M";
        if (value >= 1_000) return Math.round(value / 1_000) + "k";
        return value;
    },

    shortAxis() {
        const a = this.axis();
        a.ticks.callback = (value) => this.shorten(value);
        return a;
    },

    // Build a chart, replacing any existing one with the same id.
    draw(id, config) {
        if (this.saved[id]) this.saved[id].destroy();
        config.options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#5c5a54", boxWidth: 10, font: { size: 11 } } },
            },
            ...config.options,
        };
        this.saved[id] = new Chart(document.getElementById(id), config);
    },

  renderHourly(rows) {
    this.draw("chart-hourly", {
      type: "line",
      data: {
        labels: rows.map(r => r.hour + ":00"),
        datasets: [
          {
            label: "Trips",
            data: rows.map(r => r.trips),
            borderColor: this.INK,
            tension: 0.3,
            yAxisID: "y"
          },
          {
            label: "Speed",
            data: rows.map(r => r.avg_speed),
            borderColor: this.TEAL,
            tension: 0.3,
            yAxisID: "y1"
          }
        ]
      },
      options: {
        scales: {
          x: this.axis(),
          y: this.shortAxis(),
          y1: this.axis()
        }
      }
    });
  },

  // Daily chart: number of trips for each day of the week.
  renderDaily(rows) {
    this.draw("chart-daily", {
      type: "bar",
      data: {
        labels: rows.map(r => String(r.day)),
        datasets: [{
          label: "Trips",
          data: rows.map(r => r.trips),
          backgroundColor: this.TEAL_SOFT
        }]
      },
      options: {
        scales: {
          x: this.axis(),
          y: this.shortAxis()
        }
      }
    });
  },
};


