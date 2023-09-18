# Required imports
from flask_cors import CORS
from flask import Flask, jsonify, request, abort
import requests
from json import dumps
import logging
from datetime import datetime, timedelta

# Set up basic logging configuration for the app
logging.basicConfig(filename='app.log', level=logging.DEBUG)

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# API endpoints to fetch Carbon Intensity and COVID-19 data
CARBON_INTENSITY_URL = "https://api.carbonintensity.org.uk/regional/intensity/{from_date}/{to_date}/regionid/{regionid}"
COVID_API_ENDPOINT = "https://api.coronavirus.data.gov.uk/v1/data"

# Mapping the region id to the equivalent COVID-19 area name
REGION_MAPPING = {
    "1": "scotland",
    "2": "scotland",
    "3": "england",
    "4": "england",
    "5": "england",
    "6": "wales",
    "7": "wales",
    "8": "england",
    "9": "england",
    "10": "england",
    "11": "england",
    "12": "england",
    "13": "england",
    "14": "england",
    "15": "england",
    "16": "scotland",
    "17": "wales"
}

# Mapping of region ids to their respective names for detailed COVID-19 data
COVID_REGION_MAPPING = {
    "1": "North Scotland",
    "2": "South Scotland",
    "3": "North West England",
    "4": "North East England",
    "5": "Yorkshire",
    "6": "North Wales",
    "7": "South Wales",
    "8": "West Midlands",
    "9": "East Midlands",
    "10": "East England",
    "11": "South West England",
    "12": "South England",
    "13": "London",
    "14": "South East England",
    "15": "England",
    "16": "Scotland",
    "17": "Wales"
}

def fetch_covid_data(area_type, area_name, from_date, to_date):
    """
    Fetch COVID-19 data based on given parameters.

    Args:
    - area_type: The type of area (e.g., 'region', 'nation')
    - area_name: Name of the area to fetch data for
    - from_date, to_date: Date range for which to fetch data

    Returns:
    - JSON response if successful, None otherwise
    """

    # Define filters to fetch specific data
    filters = [
        f"areaType={area_type}",
        f"areaName={area_name}",
        f"date>={from_date}",
        f"date<={to_date}"
    ]

    # Define structure for how the returned data should be formatted
    structure = {
        "date": "date",
        "name": "areaName",
        "code": "areaCode",
        "dailyCases": "newCasesByPublishDate",
        "cumulativeCases": "cumCasesByPublishDate",
        "dailyDeaths": "newDeaths28DaysByPublishDate",
        "cumulativeDeaths": "cumDeaths28DaysByPublishDate"
    }

    api_params = {
        "filters": str.join(";", filters),
        "structure": dumps(structure, separators=(",", ":"))
    }

    # Request data from the COVID API
    response = requests.get(COVID_API_ENDPOINT, params=api_params, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None


@app.route("/region-data/<regionid>/<from_date>/<to_date>", methods=["GET"])
def get_region_data(regionid, from_date, to_date):
    """
    Endpoint to fetch combined Carbon Intensity and COVID-19 data 
    for a given region and date range.

    Args:
    - regionid: ID of the region
    - from_date, to_date: Date range for which to fetch data

    Returns:
    - JSON response with combined data
    """

    # Validate the input parameters
    if not regionid or not from_date or not to_date:
        abort(400, description="regionid, from_date, and to_date are required parameters")

    if regionid not in REGION_MAPPING:
        abort(400, description="Invalid regionid")

    # Date validation
    try:
        start_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(to_date, '%Y-%m-%d').date()
    except ValueError:
        abort(400, description="Invalid date format. Please use YYYY-MM-DD.")

    # More date validations (range, order, etc.)
    if start_date == end_date:
        abort(400, description="Start and end date cannot be the same.")
    if end_date < start_date:
        abort(400, description="End date cannot be before start date.")
    if (end_date - start_date).days > 59:
        abort(400, description="Dates cannot be more than 59 days apart.")

    # Fetch Carbon Intensity data for the region and date range
    response_ci = requests.get(
        CARBON_INTENSITY_URL.format(
            from_date=from_date, to_date=to_date, regionid=regionid),
        headers={"Accept": "application/json"}
    )
    if response_ci.status_code != 200:
        app.logger.error(
            "Failed to fetch Carbon Intensity data. Response: %s", response_ci.text)
        abort(500, description="Failed to fetch Carbon Intensity data")

    carbon_data = response_ci.json()

    # Fetch COVID-19 data based on region mapping
    area_name = COVID_REGION_MAPPING[regionid]
    covid_data = fetch_covid_data("region", area_name, from_date, to_date)

    # If region-specific data is unavailable, fallback to general area data
    if not covid_data:
        fallback_area_name = REGION_MAPPING[regionid]
        covid_data = fetch_covid_data(
            "nation", fallback_area_name, from_date, to_date)

    # Combine the fetched data into a single response
    combined_data = {
        "carbon_intensity": carbon_data,
        "covid_data": covid_data
    }

    return jsonify(combined_data)


# Run the Flask app if the script is the main point of execution
if __name__ == "__main__":
    app.run(debug=True)