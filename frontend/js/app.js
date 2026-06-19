// Talks  to the backend. Every chart asks this helper for its data instead of
// calling fetch() itself, so all the URL building lives in one place.

const API = {
    base: "/api",

    // Read whatever the filter boxes currently say into one plain object.
    currentFilters() {
        const value = (id) => document.getElementById(id).value;
        return {
            date_from: value("f-date-from"),
            date_to: value("f-date-to"),
            hour_from: value("f-hour-from"),
            hour_to: value("f-hour-to"),
            borough: value("f-borough"),
            payment: value("f-payment"),
            min_fare: value("f-min-fare"),
            max_fare: value("f-max-fare"),
            min_dist: value("f-min-dist"),
            max_dist: value("f-max-dist"),
        };
    },
};