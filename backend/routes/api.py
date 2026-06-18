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

