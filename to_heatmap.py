import sys
import json
import requests
from geojson import LineString, Point
import googlemaps
import datetime
from datetime import timedelta
from config import API_KEY
from tqdm import tqdm
import os
import pprint


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
    if "longitudeE7" in visit["location"]:
        properties["longitude"] = visit["location"]["longitudeE7"] / 10e6
    if "latitudeE7" in visit["location"]:
        properties["latitude"] = visit["location"]["latitudeE7"] / 10e6
    if "duration" in visit:
        if "startTimestamp" in visit["duration"]:
            properties["timestamp"] = timestamp_conversion(
                visit["duration"]["startTimestamp"])

    return (
        Point(
            (
                visit["location"]["longitudeE7"] / 10e6,
                visit["location"]["latitudeE7"] / 10e6,
            )
        ),
        properties,
    )


def features_and_properties(timeline_objects):
    lst = []
    for timeline_object in tqdm(timeline_objects, desc="Processing"):
        if "placeVisit" in timeline_object:
            lst.append(place_visit(timeline_object["placeVisit"]))
        else:
            lst.append((None, None))
    return lst


def make_geojson(fs_and_ps):
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": properties, "geometry": feature}
            for feature, properties in fs_and_ps
            if feature
        ],
    }


if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    subfolders = [f for f in os.listdir(
        input_dir) if os.path.isdir(os.path.join(input_dir, f))]
    places_visited = []
    for subfolder in subfolders:
        subfolder_path = os.path.join(input_dir, subfolder)
        print(f"Processing subfolder: {subfolder_path}")
        for filename in os.listdir(subfolder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(subfolder_path, filename)
                with open(file_path, 'r') as json_file:
                    try:
                        maps_json = json.load(json_file)
                    except json.JSONDecodeError:
                        print(f"Error parsing JSON in file: {file_path}")

                for timeline_object in maps_json["timelineObjects"]:
                    # places_visited.append(extract_long_lat(timeline_object))
                    if "placeVisit" in timeline_object:
                        places_visited.append(place_visit(
                            timeline_object["placeVisit"]))

    output_geojson = make_geojson(places_visited)
    json.dump(output_geojson, open(output_dir, "w"), indent=2)
    # json.dump(places_visited, open(output_dir, "w"), indent=2)
