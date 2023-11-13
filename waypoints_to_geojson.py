import sys
import json
import requests
from geojson import LineString, Point
import googlemaps
from config import API_KEY
from tqdm import tqdm

# https://developers.google.com/maps/documentation/javascript/examples/geocoding-place-id
URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# https://googlemaps.github.io/google-maps-services-python/docs/index.html#googlemaps.Client.place

gmaps = googlemaps.Client(key=API_KEY)

# Geocoding an address

PARAMS = {
    "key": API_KEY,
    "fields": ["routes.polyline"],
}


def activity_segment(segment):
    return (
        LineString(
            [
                (
                    segment["startLocation"]["longitudeE7"] / 10e6,
                    segment["startLocation"]["latitudeE7"] / 10e6,
                ),
                *(
                    [
                        (waypoint["lngE7"] / 10e6, waypoint["latE7"] / 10e6)
                        for waypoint in segment["waypointPath"]["waypoints"]
                    ]
                    if "waypointPath" in segment
                    else []
                ),
                (
                    segment["endLocation"]["longitudeE7"] / 10e6,
                    segment["endLocation"]["latitudeE7"] / 10e6,
                ),
            ]
        ),
        {},
    )


def place_visit(visit):
    properties = {}
    if "name" in visit["location"]:
        properties["name"] = visit["location"]["name"]
    if "address" in visit["location"]:
        properties["address"] = visit["location"]["address"]

    return (
        Point(
            (
                visit["location"]["longitudeE7"] / 10e6,
                visit["location"]["latitudeE7"] / 10e6,
            )
        ),
        properties,
    )


def waypoint(lat, lng):
    return {
        "via": False,
        "vehicleStopover": False,
        "sideOfRoad": False,
        "location": {"latLng": {"latitude": lat, "longitude": lng}},
    }


def travel_mode(activity_segment):
    if activity_segment["activityType"] == "WALKING":
        return "WALK"
    elif activity_segment["activityType"] == "CYCLING":
        return "BICYCLE"
    else:
        return "DRIVE"


def route_request(activity_segment):
    return {
        "origin": waypoint(
            activity_segment["startLocation"]["latitudeE7"] / 10e6,
            activity_segment["startLocation"]["longitudeE7"] / 10e6,
        ),
        "destination": waypoint(
            activity_segment["endLocation"]["latitudeE7"] / 10e6,
            activity_segment["endLocation"]["longitudeE7"] / 10e6,
        ),
        "intermediates": [
            waypoint(wp["latE7"] / 10e6, wp["lngE7"] / 10e6)
            for wp in activity_segment["waypointPath"]["waypoints"]
        ]
        if "waypointPath" in activity_segment
        else [],
        "travelMode": travel_mode(activity_segment),
        "polylineEncoding": "GEO_JSON_LINESTRING",
    }


request_count = 0


def send_route_request(body):
    global request_count
    # print(f"Request {request_count}")
    resp = requests.post(URL, json=body, params=PARAMS)
    if not resp.ok:
        raise Exception(resp.text)
    # print("Recieved")
    request_count += 1
    # print(resp.json()["routes"][0]["polyline"]["geoJsonLinestring"])
    return (resp.json()["routes"][0]["polyline"]["geoJsonLinestring"], {})


def routed_activity_segment(segment):
    if segment["activityType"] == "FLYING":
        return activity_segment(segment)
    else:
        return send_route_request(route_request(segment))


def features_and_properties(maps_json):
    return [
        routed_activity_segment(x["activitySegment"])
        if "activitySegment" in x
        else place_visit(x["placeVisit"])
        if "placeVisit" in x
        else (None, None)
        for x in tqdm(maps_json["timelineObjects"], desc="Processing")
    ]


def make_geojson(fs_and_ps):
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": properties, "geometry": feature}
            for feature, properties in fs_and_ps
            if feature
        ],
    }


def convert_fine_grained(maps_json):
    return make_geojson(features_and_properties(maps_json))


if __name__ == "__main__":
    input_json = sys.argv[1]
    output_file = sys.argv[2]

    output_geosjon = convert_fine_grained(json.load(open(input_json)))
    json.dump(output_geosjon, open(output_file, "w"), indent=2)
