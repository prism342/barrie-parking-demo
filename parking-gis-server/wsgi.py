import os
import json
from random import randint
import numpy as np
import itertools
import re 
import pyodbc

from flask import Flask, request, render_template
from flask_cors import CORS

from db_config import ConnectionString


hotspots = json.loads(open("./hotspots.json").read())

cnxn = pyodbc.connect(ConnectionString)
cursor = cnxn.cursor()


app = Flask(__name__)
CORS(app)


def get_color_by_scale(scale: float):
    color_map = np.array([
        [0/29, 51, 147, 193],
        [1/29, 61, 151, 192],
        [2/29, 80, 156, 187],
        [3/29, 96, 166, 187],
        [4/29, 114, 170, 176],
        [5/29, 133, 179, 172],
        [6/29, 143, 185, 167],
        [7/29, 159, 194, 154],
        [8/29, 172, 200, 150],
        [9/29, 183, 208, 138],
        [10/29, 196, 216, 137],
        [11/29, 212, 222, 129],
        [12/29, 225, 234, 121],
        [13/29, 229, 238, 113],
        [14/29, 247, 247, 103],
        [15/29, 254, 243, 97],
        [16/29, 253, 227, 89],
        [17/29, 253, 213, 83],
        [18/29, 255, 195, 78],
        [19/29, 255, 180, 68],
        [20/29, 251, 171, 61],
        [21/29, 251, 148, 61],
        [22/29, 251, 137, 53],
        [23/29, 247, 127, 46],
        [24/29, 246, 105, 37],
        [25/29, 248, 93, 38],
        [26/29, 244, 79, 32],
        [27/29, 241, 60, 31],
        [28/29, 235, 42, 24],
        [29/29, 225, 18, 19],
    ])

    color_scale = np.abs((color_map[:, 0] - scale)).argmin()

    color = color_map[color_scale][1:].copy().tolist()
    color.append(0.8)

    return color


@app.route("/")
def index():
    return "hello"

@app.route("/get_mock_data")
def get_mock_data():
    data_list = []
    
    for hotspotID in hotspots.keys():
        hotspot = hotspots[hotspotID]

        data = {}
        revenue = randint(1000, 5000)
        revenue_scaled = (revenue - 1000) / 4000
        data["name"] = hotspot["name"]
        data["description"] = "HotSpotID: {}\nCapacity: {}\nTotal Revenue: {}$\nRevenue per spot:{}".format(hotspotID, hotspot["capacity"], revenue, revenue/hotspot["capacity"])
        data["rings"] = hotspot["outerBoundaries"]

        data["revenue"] = revenue
        data["color"] = get_color_by_scale(revenue_scaled)
        data_list.append(data)
    return json.dumps(data_list)

def calc_upper_bound(data):
    q3, q1 = np.percentile(data, [75 ,25])
    iqr = q3 - q1
    upper_bound = q3 + (1.5 * iqr)
    return upper_bound

@app.route("/get_gis_revenue_data")
def get_gis_revenue_data():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    date_pattern = re.compile("^\d\d\d\d-\d\d-\d\d$")
    assert(date_pattern.match(start_date))
    assert(date_pattern.match(end_date))

    result = cursor.execute("select HotspotID, sum(Amount) from Purchases where PurchaseDateLocal > '{}' and PurchaseDateLocal < '{}' group by HotspotID order by HotspotID".format(start_date, end_date)).fetchall()
    
    revenue_data = {}
    for (HotspotID, revenue) in result:
        if HotspotID is None: continue
        revenue_data[HotspotID.strip()] = revenue

    revenue_upper_bound = calc_upper_bound(list(revenue_data.values()))

    data_list = []
    for hotspotID in hotspots.keys():
        hotspot = hotspots[hotspotID]
        
        revenue = 0
        color = [128, 128, 128, 0.8]
        if hotspotID in revenue_data:
            revenue = revenue_data[hotspotID]
            revenue_scaled = revenue / revenue_upper_bound
            color = get_color_by_scale(revenue_scaled)

        capacity = None 
        revenue_per_cap = None 
        if "capacity" in hotspot:
            capacity = hotspot["capacity"]
            revenue_per_cap = revenue / capacity

        data = {}
        data["name"] = hotspot["name"]
        if capacity is not None:
            data["description"] = "HotSpotID: {}\nCapacity: {}\nTotal Revenue: {:,.0f}$\nRevenue per space: {:,.0f}$".format(hotspotID, capacity, revenue, revenue_per_cap)
        else:
            data["description"] = "HotSpotID: {}\nCapacity: {}\nTotal Revenue: {:,.0f}$\nRevenue per space: {}$".format(hotspotID, capacity, revenue, revenue_per_cap)

        data["rings"] = hotspot["outerBoundaries"]
        data["color"] = color
        data_list.append(data)

    return json.dumps({"color_revenue_range":[0, "{:,.0f}".format(revenue_upper_bound)], "data":data_list})


@app.route("/get_gis_revenue_per_space_data")
def get_gis_revenue_per_space_data():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    date_pattern = re.compile("^\d\d\d\d-\d\d-\d\d$")
    assert(date_pattern.match(start_date))
    assert(date_pattern.match(end_date))

    result = cursor.execute("select HotspotID, sum(Amount) from Purchases where PurchaseDateLocal > '{}' and PurchaseDateLocal < '{}' group by HotspotID order by HotspotID".format(start_date, end_date)).fetchall()
    
    revenue_data = {}
    for (HotspotID, revenue) in result:
        if HotspotID is None: continue
        revenue_data[HotspotID.strip()] = revenue

    # calculete revenue per space
    revenue_per_space_data = {}
    for HotspotID in revenue_data.keys():
        revenue = revenue_data[HotspotID]
        hotspot = hotspots[HotspotID]

        if "capacity" in hotspot:
            capacity = hotspot["capacity"]
            revenue_per_space = revenue / capacity
            revenue_per_space_data[HotspotID] = revenue_per_space

    revenue_upper_bound = calc_upper_bound(list(revenue_per_space_data.values()))

    data_list = []
    for hotspotID in hotspots.keys():
        hotspot = hotspots[hotspotID]
        
        revenue = 0
        color = [128, 128, 128, 0.8]
        capacity = None 
        revenue_per_cap = None 

        if hotspotID in revenue_data and "capacity" in hotspot:
            revenue = revenue_data[hotspotID]
            capacity = hotspot["capacity"]
            revenue_per_cap = revenue / capacity
            revenue_scaled = revenue_per_cap / revenue_upper_bound
            color = get_color_by_scale(revenue_scaled)

        data = {}
        data["name"] = hotspot["name"]
        if capacity is not None:
            data["description"] = "HotSpotID: {}\nCapacity: {}\nTotal Revenue: {:,.0f}$\nRevenue per space: {:,.0f}$".format(hotspotID, capacity, revenue, revenue_per_cap)
        else:
            data["description"] = "HotSpotID: {}\nCapacity: {}\nTotal Revenue: {:,.0f}$\nRevenue per space: {}$".format(hotspotID, capacity, revenue, revenue_per_cap)

        data["rings"] = hotspot["outerBoundaries"]
        data["color"] = color
        data_list.append(data)

    return json.dumps({"color_revenue_range":[0, "{:,.0f}".format(revenue_upper_bound)], "data":data_list})


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8001)
