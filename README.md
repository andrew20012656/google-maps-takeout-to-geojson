# google-maps-takeout-to-geojson

A tool to process Google Maps Takeout data to GeoJSON format, and the transformed data can be used in [Kepler.gl](https://kepler.gl) to visualize trips.

- [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
- [Usage](#usage)
- [Sample Input Data](#sample-input-data)
- [Relevant Documentation](#relevant-documentations)
- [Acknowledgments](#acknowledgments)

## Getting Started

### Prerequisites
You will need your personal Google Maps Platform API Key in order to use the tools. For instructions on how to acquire Google Maps Platform API Key, please refer to [link](https://developers.google.com/maps/documentation/javascript/get-api-key).
### Installation
- `pip install -r requirements.txt`

## Usage

1. To map the `waypoints` in `activitySegment` attribute in Google Takeout data
    - `python waypoints_to_geojson.py <path-to-source-data> <path-to-output-file>`
2. To map the `roadSegment` in `activitySegment` attribute in Google Takeout data
    - `python road_segment_to_geojson.py <path-to-source-data> <path-to-output-file>`
3. To visualize all the 'placeVisit' points
    - `python to_heapmap.py <path-to-source-data-directory> <path-to-output-file>`

## Sample Input Data
For sample input data, please refer to `data` folder. The corresponding output file in GeoJSON format named `output1.json` can be found in `output` folder.

## Relevant Documentations
1. [Google Maps Platform: Get the Address for a Place ID](https://developers.google.com/maps/documentation/javascript/examples/geocoding-place-id)
2. [Google Maps Platform: Geocoding API](https://developers.google.com/maps/documentation/geocoding/)
3. [Google Maps Platform: Use API Keys](https://developers.google.com/maps/documentation/javascript/get-api-key)

## Acknowledgments

I would like to acknowledge and thank the following individuals and projects for their inspiration:

- [mmcqd](https://github.com/mmcqd/hi-res-google-takeout-geojson)

