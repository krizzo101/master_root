"""
RESTful API resource for AJAX-based weather data refresh (JSON)
"""
from flask_restful import Resource, reqparse
from flask import current_app


class WeatherResource(Resource):
    def __init__(self, weather_service):
        self.weather_service = weather_service
        # Parser for input validation
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            "location",
            type=str,
            required=False,
            help="Location (city or city,country code)",
        )

    def get(self):
        """
        Returns current weather info as JSON. Accepts optional 'location' arg.
        """
        args = self.reqparse.parse_args()
        location = (
            args.get("location") or current_app.config["WEATHER_DEFAULT_LOCATION"]
        )
        try:
            weather = self.weather_service.fetch_weather(location)
            return {"success": True, "data": weather}, 200
        except Exception as ex:
            return {"success": False, "error": str(ex)}, 400
