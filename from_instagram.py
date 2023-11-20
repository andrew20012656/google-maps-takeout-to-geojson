import json
from common_utils import convert_to_timestamp
from geojson import Point


def extract_stories_with_exif_data(path_to_stories_data):
    """
    Extract the exif data from photo stories which contain exif data. The extracted exif data contains: `latitude`, `longitude`, `url`, `datetime_original` (some may not have it)

    Parameters:
        - path_to_stories_data (str): path to the stories.json file

    Returns:
        - stories_info (list): a list of dict each of which contains the exif data of stories
    """
    with open(path_to_stories_data, "r") as json_file:
        try:
            stories_data = json.load(json_file)
        except json.JSONDecodeError:
            print(f"Error parsing JSON in file: {path_to_stories_data}")

    stories_info = []
    for story in stories_data["ig_stories"]:
        story_data = {}
        if "media_metadata" in story and "photo_metadata" in story["media_metadata"] and "exif_data" in story["media_metadata"]["photo_metadata"]:
            exif_data = story["media_metadata"]["photo_metadata"]["exif_data"]
            if len(exif_data) == 2:
                story_data["latitude"] = exif_data[0]["latitude"]
                story_data["longitude"] = exif_data[0]["longitude"]
                if "date_time_original" in exif_data[1]:
                    story_data["datetime_original"] = exif_data[1]["date_time_original"]
                story_data["url"] = story["uri"]
                stories_info.append(story_data)

    return stories_info


def extract_media_path(media_path):
    """
    Parameters:
        - `media_path` (str): a string representing the path to a story media (photo)

    Returns:
        - `path` (str): extracted path

    Example Input:
        - media/stories/202108/232972524_784218242254668_6118226980962968239_n_17868053870536088.jpg
    """
    parts = media_path.split("media/")
    if len(parts) >= 2:
        return parts[1]
    else:
        print("The input string does not contain 'media/stories'")


def create_story_point(stories_info):
    """
    Parameters: 
        - `stories_info` (list): a list of extracted exif data from the Instagram stories

    Returns:
        - `points` (list): a list of geojson Points each of which contains the geojson data of where the image used in that story was taken along with the timestamp and corresponding url to the image
    """
    points = []
    for story_info in stories_info:
        properties = {}
        if "longitude" in story_info and "latitude" in story_info:
            properties["longitude"] = story_info["longitude"]
            properties["latitude"] = story_info["latitude"]
            if "datetime_original" in story_info:
                properties["timestamp"] = convert_to_timestamp(
                    story_info["datetime_original"])
            properties["url"] = "https://instagram-data-jose.s3.amazonaws.com/" + \
                str(extract_media_path(story_info["url"]))
            point_and_properties = (
                Point((story_info["longitude"], story_info["latitude"])), properties)
            points.append(point_and_properties)
    return points
