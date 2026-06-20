"""
The API. Every chart and table on the dashboard gets its data from one of the
addresses below (they all start with /api).

The chart endpoints accept the same filters, sent from the page:
    date_from, date_to     e.g. 2019-01-05   (which days to include)
    hour_from, hour_to     0..23             (which hours of the day)
    borough                e.g. Manhattan    (pickup borough)
    payment                1=card, 2=cash, 3=no charge, ...
    min_fare, max_fare     dollars
    min_dist, max_dist     miles

A note on speed
---------------
Adding up 7.4 million trips for every chart would be slow, so load_data.py
already built a small summary table (agg_zone_time) that holds the totals per
day / hour / zone / payment type. We read the charts from that summary, which
is quick. The summary has no fare or distance column, so when the user filters
by fare or distance we read the full trips table instead. That is the only
reason there are two versions of some queries below.

Safety: user input is always passed as a query parameter (%s), never glued
into the SQL text, and the sort option is checked against a fixed list. Both
stop SQL injection.
"""

from datetime import date

from flask import Blueprint, jsonify, request, send_file

from backend.algorithms.heap import top_k
from backend.config import Config
from backend.db import query_all, query_one

api = Blueprint("api", __name__)

SORT_COLUMNS = {
    "pickup_datetime": "t.pickup_datetime",
    "dropoff_datetime": "t.dropoff_datetime",
    "trip_distance": "t.trip_distance",
    "trip_duration_min": "t.trip_duration_min",
    "fare_amount": "t.fare_amount",
    "tip_amount": "t.tip_amount",
    "total_amount": "t.total_amount",
    "avg_speed_mph": "t.avg_speed_mph",
    "passenger_count": "t.passenger_count"
}

# Metrics the "top zones" chart can rank by.
TOP_METRICS = {"trips", "revenue", "avg_fare", "avg_speed", "avg_tip_pct"}

# The table to read from each case
TRIPS_FROM = "FROM trips t JOIN zones zpu ON zpu.zone_id = t.pu_location_id"
SUMMARY_FROM = "FROM agg_zone_time s JOIN zones zpu ON zpu.zone_id = s.pu_location_id"



def using_full_table(args):
    for key in ("min_fare", "max_fare", "min_dist", "max_dist"):
        if args.get(key) not in (None, ""):
            return True
    return False


def day_number(text, fallback):
    try:
        d = date.fromisoformat(text)
    except (TypeError, ValueError):
        return fallback
    return min(31, max(1, d.day))  # 1..31


def trips_where(args):
    parts = []
    values = []

    if args.get("date_from"):
        parts.append("t.pickup_datetime >= %s")
        values.append(args["date_from"] + " 00:00:00")
    if args.get("date_to"):
        parts.append("t.pickup_datetime <= %s")
        values.append(args["date_to"] + " 23:59:59")
    if args.get("hour_from") not in (None, ""):
        parts.append("t.pickup_hour >= %s")
        values.append(int(args["hour_from"]))
    if args.get("hour_to") not in (None, ""):
        parts.append("t.pickup_hour <= %s")
        values.append(int(args["hour_to"]))
    if args.get("borough"):
        parts.append("zpu.borough = %s")
        values.append(args["borough"])
    if args.get("payment"):
        parts.append("t.payment_type_id = %s")
        values.append(int(args["payment"]))
    if args.get("min_fare") not in (None, ""):
        parts.append("t.total_amount >= %s")
        values.append(float(args["min_fare"]))
    if args.get("max_fare") not in (None, ""):
        parts.append("t.total_amount <= %s")
        values.append(float(args["max_fare"]))
    if args.get("min_dist") not in (None, ""):
        parts.append("t.trip_distance >= %s")
        values.append(float(args["min_dist"]))
    if args.get("max_dist") not in (None, ""):
        parts.append("t.trip_distance <= %s")
        values.append(float(args["max_dist"]))
    where = " WHERE " + " AND ".join(parts) if parts else ""
    return where, values



def summary_where(args):
    parts = ["s.pickup_day BETWEEN %s AND %s"]
    values = [day_number(args.get("date_from"), 1), 
              day_number(args.get("date_to"), 31)]
    if args.get("hour_from") not in (None, ""):
        parts.append("s.pickup_hour >= %s")
        values.append(int(args["hour_from"]))
    if args.get("hour_to") not in (None, ""):
        parts.append("s.pickup_hour <= %s")
        values.append(int(args["hour_to"]))
    if args.get("borough"):
        parts.append("zpu.borough = %s")
        values.append(args["borough"])
    if args.get("payment"):
        parts.append("s.payment_type_id = %s")
        values.append(int(args["payment"]))
    return " WHERE " + " AND ".join(parts), values


def grouped(args, trips_select, summary_select, group_by=""):
    if using_full_table(args):
        where, values = trips_where(args)
        sql = f"SELECT {trips_select} {TRIPS_FROM} {where} {group_by}"
    else:
        where, values = summary_where(args)
        sql = f"SELECT {summary_select} {SUMMARY_FROM} {where} {group_by}"
    return query_all(sql, values)




@api.get("/meta")
def meta():
    # Values the page needs to fill its filter boxes: the date range, the list
    # of boroughs, and the list of payment types.
    bounds = query_one("SELECT MIN(pickup_datetime) AS lo, "
                       "MAX(pickup_datetime) AS hi FROM trips")
    boroughs = query_all("SELECT DISTINCT borough FROM zones "
                         "WHERE borough NOT IN ('Unknown', 'N/A') "
                         "ORDER BY borough")
    payments = query_all("SELECT payment_type_id, description "
                         "FROM payment_types ORDER BY payment_type_id")
    return jsonify({
        "date_min": str(bounds["lo"])[:10] if bounds["lo"] else None,
        "date_max": str(bounds["hi"])[:10] if bounds["hi"] else None,
        "boroughs": [b["borough"] for b in boroughs],
        "payment_types": payments,
    })


@api.get("/summary")
def summary():
    # The six big numbers at the top of the page.
    trips_select = """
        COUNT(*) AS trips, COALESCE(SUM(t.total_amount), 0) AS revenue,
        AVG(t.fare_amount) AS avg_fare, AVG(t.trip_distance) AS avg_distance,
        AVG(t.trip_duration_min) AS avg_duration,
        AVG(t.avg_speed_mph) AS avg_speed, AVG(t.tip_pct) AS avg_tip_pct
    """
    summary_select = """
        SUM(s.trips_n) AS trips, COALESCE(SUM(s.sum_total), 0) AS revenue,
        SUM(s.sum_fare) / SUM(s.trips_n) AS avg_fare,
        SUM(s.sum_distance) / SUM(s.trips_n) AS avg_distance,
        SUM(s.sum_duration) / SUM(s.trips_n) AS avg_duration,
        SUM(s.sum_speed) / SUM(s.trips_n) AS avg_speed,
        SUM(s.sum_tip_pct) / SUM(s.trips_n) AS avg_tip_pct
    """
    row = grouped(request.args, trips_select, summary_select)[0]
    # trips is a whole number; everything else is a dollar/number average.
    result = {}
    for key, value in row.items():
        if value is None:
            result[key] = None
        elif key == "trips":
            result[key] = int(value)
        else:
            result[key] = float(value)
    return jsonify(result)



@api.get("/trips")
def trips():
    # The paginated, sortable table of individual trips. This always reads the
    # full trips table because it shows single rows, not totals.
    args = request.args
    where, values = trips_where(args)

    sort = SORT_COLUMNS.get(args.get("sort", "pickup_datetime"), "t.pickup_datetime")
    order = "ASC" if args.get("order", "desc").lower() == "asc" else "DESC"
    limit = min(int(args.get("limit", 25)), 200)
    page = max(int(args.get("page", 1)), 1)
    offset = (page - 1) * limit

    # How many trips match (needed to show the page count). When the summary
    # table can be used, getting the count from it is much faster.
    if using_full_table(args):
        total = query_one(f"SELECT COUNT(*) AS n {TRIPS_FROM} {where}", values)["n"]
    else:
        s_where, s_values = summary_where(args)
        total = int(query_one(
            f"SELECT COALESCE(SUM(s.trips_n), 0) AS n {SUMMARY_FROM} {s_where}",
            s_values)["n"])

    # The page of rows. We also join the dropoff zone (zdo) and payment type.
    rows = query_all(f"""
        SELECT t.trip_id, t.pickup_datetime, t.dropoff_datetime,
               t.passenger_count, t.trip_distance, t.trip_duration_min,
               t.avg_speed_mph, t.fare_amount, t.tip_amount, t.tip_pct,
               t.total_amount,
               zpu.zone_name AS pickup_zone,  zpu.borough AS pickup_borough,
               zdo.zone_name AS dropoff_zone, zdo.borough AS dropoff_borough,
               pt.description AS payment
        {TRIPS_FROM}
        JOIN zones zdo ON zdo.zone_id = t.do_location_id
        JOIN payment_types pt ON pt.payment_type_id = t.payment_type_id
        {where}
        ORDER BY {sort} {order}
        LIMIT %s OFFSET %s
    """, values + [limit, offset])

    # Turn datetimes into text and the money columns into plain numbers.
    for row in rows:
        row["pickup_datetime"] = str(row["pickup_datetime"])
        row["dropoff_datetime"] = str(row["dropoff_datetime"])
        for col in ("trip_distance", "trip_duration_min", "avg_speed_mph",
                    "fare_amount", "tip_amount", "tip_pct", "total_amount"):
            row[col] = float(row[col])

    return jsonify({"total": total, "page": page, "limit": limit, "rows": rows})



@api.get("/trends/hourly")
def trends_hourly():
    # Trips and average speed for each hour of the day (0..23).
    rows = grouped(
        request.args,
        trips_select="t.pickup_hour AS hour, COUNT(*) AS trips, "
                     "AVG(t.fare_amount) AS avg_fare, "
                     "AVG(t.avg_speed_mph) AS avg_speed, "
                     "AVG(t.tip_pct) AS avg_tip_pct",
        summary_select="s.pickup_hour AS hour, SUM(s.trips_n) AS trips, "
                       "SUM(s.sum_fare) / SUM(s.trips_n) AS avg_fare, "
                       "SUM(s.sum_speed) / SUM(s.trips_n) AS avg_speed, "
                       "SUM(s.sum_tip_pct) / SUM(s.trips_n) AS avg_tip_pct",
        group_by="GROUP BY hour ORDER BY hour",
    )
    return jsonify([{
        "hour": int(r["hour"]),
        "trips": int(r["trips"]),
        "avg_fare": round(float(r["avg_fare"]), 2),
        "avg_speed": round(float(r["avg_speed"]), 2),
        "avg_tip_pct": round(float(r["avg_tip_pct"]), 2),
    } for r in rows])


@api.get("/trends/daily")
def trends_daily():
    # Trips and revenue for each day of the month.
    rows = grouped(
        request.args,
        trips_select="t.pickup_day AS day, COUNT(*) AS trips, "
                     "COALESCE(SUM(t.total_amount), 0) AS revenue, "
                     "MAX(t.is_weekend) AS is_weekend",
        summary_select="s.pickup_day AS day, SUM(s.trips_n) AS trips, "
                       "COALESCE(SUM(s.sum_total), 0) AS revenue, "
                       "MAX(s.is_weekend) AS is_weekend",
        group_by="GROUP BY day ORDER BY day",
    )
    return jsonify([{
        "day": int(r["day"]),
        "trips": int(r["trips"]),
        "revenue": round(float(r["revenue"]), 2),
        "is_weekend": int(r["is_weekend"]),
    } for r in rows])




def zone_totals(args):
    # Totals per pickup zone. Used by both the map and the "top zones" chart.
    rows = grouped(
        args,
        trips_select="t.pu_location_id AS zone_id, zpu.zone_name AS zone, "
                     "zpu.borough AS borough, COUNT(*) AS trips, "
                     "COALESCE(SUM(t.total_amount), 0) AS revenue, "
                     "AVG(t.fare_amount) AS avg_fare, "
                     "AVG(t.avg_speed_mph) AS avg_speed, "
                     "AVG(t.tip_pct) AS avg_tip_pct",
        summary_select="s.pu_location_id AS zone_id, zpu.zone_name AS zone, "
                       "zpu.borough AS borough, SUM(s.trips_n) AS trips, "
                       "COALESCE(SUM(s.sum_total), 0) AS revenue, "
                       "SUM(s.sum_fare) / SUM(s.trips_n) AS avg_fare, "
                       "SUM(s.sum_speed) / SUM(s.trips_n) AS avg_speed, "
                       "SUM(s.sum_tip_pct) / SUM(s.trips_n) AS avg_tip_pct",
        group_by="GROUP BY zone_id, zone, borough",
    )
    for r in rows:
        r["zone_id"] = int(r["zone_id"])
        r["trips"] = int(r["trips"])
        r["revenue"] = round(float(r["revenue"]), 2)
        r["avg_fare"] = round(float(r["avg_fare"]), 2)
        r["avg_speed"] = round(float(r["avg_speed"]), 2)
        r["avg_tip_pct"] = round(float(r["avg_tip_pct"]), 2)
    return rows


@api.get("/zones/stats")
def zone_stats():
    # Colors the map: one total per pickup zone.
    return jsonify(zone_totals(request.args))




@api.get("/zones/top")
def zones_top():
    # The "top zones" chart. We get the per-zone totals (in no order) and then
    # rank them with our own hand-written heap, not a SQL ORDER BY.
    args = request.args
    metric = args.get("metric", "trips")
    if metric not in TOP_METRICS:
        return jsonify({"error": f"metric must be one of {sorted(TOP_METRICS)}"}), 400
    k = min(int(args.get("k", 10)), 50)

    zones = zone_totals(args)
    ranked = top_k(zones, lambda z: float(z[metric]), k)

    for position, zone in enumerate(ranked, start=1):
        zone["rank"] = position
        zone["trip_count"] = zone["trips"]   # the chart reads this name

    return jsonify({"metric": metric, "k": k,
                    "ranked_by": "hand-written min-heap, O(N log K)",
                    "zones": ranked})




@api.get("/breakdown/payment")
def breakdown_payment():
    # Trips and average tip for each payment type. Needs the payment_types
    # join on both paths, so it writes its own SQL.
    args = request.args
    if using_full_table(args):
        where, values = trips_where(args)
        rows = query_all(f"""
            SELECT pt.description AS payment, COUNT(*) AS trips,
                   AVG(t.tip_pct) AS avg_tip_pct
            {TRIPS_FROM}
            JOIN payment_types pt ON pt.payment_type_id = t.payment_type_id
            {where}
            GROUP BY pt.description
        """, values)
    else:
        where, values = summary_where(args)
        rows = query_all(f"""
            SELECT pt.description AS payment, SUM(s.trips_n) AS trips,
                   SUM(s.sum_tip_pct) / SUM(s.trips_n) AS avg_tip_pct
            {SUMMARY_FROM}
            JOIN payment_types pt ON pt.payment_type_id = s.payment_type_id
            {where}
            GROUP BY pt.description
        """, values)
    return jsonify([{
        "payment": r["payment"],
        "trips": int(r["trips"]),
        "avg_tip_pct": round(float(r["avg_tip_pct"]), 2),
    } for r in rows])




@api.get("/breakdown/borough")
def breakdown_borough():
    # Trips, revenue and average speed for each pickup borough.
    rows = grouped(
        request.args,
        trips_select="zpu.borough AS borough, COUNT(*) AS trips, "
                     "COALESCE(SUM(t.total_amount), 0) AS revenue, "
                     "AVG(t.avg_speed_mph) AS avg_speed",
        summary_select="zpu.borough AS borough, SUM(s.trips_n) AS trips, "
                       "COALESCE(SUM(s.sum_total), 0) AS revenue, "
                       "SUM(s.sum_speed) / SUM(s.trips_n) AS avg_speed",
        group_by="GROUP BY borough",
    )
    return jsonify([{
        "borough": r["borough"],
        "trips": int(r["trips"]),
        "revenue": round(float(r["revenue"]), 2),
        "avg_speed": round(float(r["avg_speed"]), 2),
    } for r in rows])


@api.get("/zones/geojson")
def zones_geojson():
    # The map outlines, built once by pipeline/zones_geojson.py.
    return send_file(Config.GEOJSON_PATH, mimetype="application/geo+json")


