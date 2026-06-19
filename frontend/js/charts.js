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
};
