import sys
import json
from geojson import Point
from tqdm import tqdm
import os
from from_instagram import *
from common_utils import *


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
            properties["timestamp"] = convert_to_timestamp(
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

    path_to_stories_data = "data/Instagram-Jose/content/stories.json"
    stories_info = extract_stories_with_exif_data(path_to_stories_data)
    points = create_story_point(stories_info)

    for point in points:
        places_visited.append(point)

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
                    if "placeVisit" in timeline_object:
                        places_visited.append(place_visit(
                            timeline_object["placeVisit"]))

    output_geojson = make_geojson(places_visited)
    json.dump(output_geojson, open(output_dir, "w"), indent=2)
