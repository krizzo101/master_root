"""
WTForms form for city name input.
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp


class CitySearchForm(FlaskForm):
    """
    WTForm for weather city search input.
    """

    city = StringField(
        "City",
        validators=[
            DataRequired(message="Please enter a city name."),
            Length(min=2, max=64, message="City name must be 2-64 characters long."),
            # Accept basic alpha chars, spaces, commas, hyphens
            Regexp(r"^[A-Za-zÀ-ÿ ,.-]+$", message="City contains invalid characters."),
        ],
    )
    submit = SubmitField("Get Weather")
