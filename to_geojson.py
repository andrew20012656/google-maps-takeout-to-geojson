import sys
import json
import requests
from geojson import LineString, Point
import googlemaps
import datetime
from datetime import timedelta
from config import API_KEY
import pprint

# https://developers.google.com/maps/documentation/javascript/examples/geocoding-place-id

URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

PARAMS = {
    "key": API_KEY,
    "fields": ["routes.polyline"],
}

gmaps = googlemaps.Client(key=API_KEY)


def timestamp_conversion(time_str: str):
    """
    Return a POSIX timestamp 

    Parameters:
    - time_str (str): a string representing a timestamp following ISO 8601 Standard
    """
    date_formats = ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"]
    start_datetime = None
    for date_format in date_formats:
        try:
            start_datetime = datetime.datetime.strptime(time_str, date_format)
            break
        except ValueError:
            continue

    return start_datetime.timestamp()


def placeID_to_coordinates(segment):
    """
    Converts all roadSegments in an activitySegment's wayPointPath (containing only placeId and inferred duration) to corresponding (longitude, latitude, altitude (default 0), timestamp)

    Parameters:
        - segment (activitySegment): an activitySegement from Google Maps Takeout data
    
    Returns:
    A list of tuple each of which consists of:
        - longitude: the longitude of the corresponding roadSegment
        - latitude: the latitude of the corresponding roadSegment
        - altitude : the altitude of the roadSegment, default 0
        - timestamp: a POSIX timestamp representing the first point in time at this segement
    
    Notes: 
    The format of the tuple is specified because of its later usage in visualization at Kepler.gl
    """
    start_timestamp = timestamp_conversion(segment["duration"]["startTimestamp"])

    waypoints = []
    road_segment_datetime = datetime.datetime.fromtimestamp(start_timestamp)  # The time at a given roadSegment

    if "roadSegment" in segment["waypointPath"]:
        for roadSegment in segment["waypointPath"]["roadSegment"]:
            placeId = roadSegment["placeId"]
            duration = int(roadSegment["duration"][0:-1]) # Example duration from takeout-data: "23s"
            geocode_result = gmaps.geocode(place_id=placeId)
            if geocode_result: # If Google Maps found a place corresponding to this placeId
                long = geocode_result[0]["geometry"]["location"]["lng"]
                lat = geocode_result[0]["geometry"]["location"]["lat"]
                delta = timedelta(seconds=duration)
                road_segment_datetime += delta
                waypoints.append(
                    (long, lat, 0, road_segment_datetime.timestamp()))
    return waypoints


def activity_segment(segment):
    """
    Returns the LineString object corresponding to the given activitySegment

    Parameters:
        - segment: an activitySegment
    
    Returns:
    A tuple consisting of:
        - lineString (LineString)
        - an empty dict: intended for later conversion 
    """
    return (
            LineString(
                [
                    (
                        segment["startLocation"]["longitudeE7"] / 10e6,
                        segment["startLocation"]["latitudeE7"] / 10e6,
                        0,
                        timestamp_conversion(
                            segment["duration"]["startTimestamp"])
                    ),
                    *(
                        placeID_to_coordinates(segment)
                        if "waypointPath" in segment
                        else []
                    ),
                    (
                        segment["endLocation"]["longitudeE7"] / 10e6,
                        segment["endLocation"]["latitudeE7"] / 10e6,
                        0,
                        timestamp_conversion(
                            segment["duration"]["endTimestamp"])
                    ),
                ]
            ),
            {}
        )
        

def place_visit(visit):
    """
    Returns the placeVisit object as a Point object

    Paramters: 
        - visit: placeVisit in Google Maps Takeout data
    
    Returns:
        - point (Point): an Geometry object representing the place as a Point
    """
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
    print(f"Request {request_count}")
    resp = requests.post(URL, json=body, params=PARAMS)
    if not resp.ok:
        raise Exception(resp.text)
    print("Recieved")
    request_count += 1
    return (resp.json()["routes"][0]["polyline"]["geoJsonLinestring"], {})


def routed_activity_segment(segment):
    return activity_segment(segment)
    # if segment["activityType"] == "FLYING":
    #     tmp = activity_segment(segment)
    #     pprint.pprint(tmp)
    #     return tmp
    # else:
    #     tmp = activity_segment(segment)
    #     pprint.pprint(tmp)
    #     return tmp
    # else:
    #     return send_route_request(route_request(segment))


def features_and_properties(maps_json):
    return [
        routed_activity_segment(x["activitySegment"])
        if "activitySegment" in x
        else place_visit(x["placeVisit"])
        if "placeVisit" in x
        else (None, None)
        for x in maps_json["timelineObjects"]
    ]


def make_geojson(fs_and_ps):
    lst = []
    for i in fs_and_ps:
        if i is not None:
            lst.append(i)

    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": properties, "geometry": feature}
            for feature, properties in lst
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
