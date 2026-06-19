// Talks  to the backend. Every chart asks this helper for its data instead of
// calling fetch() itself, so all the URL building lives in one place.

const API = {
    base: "/api",
}