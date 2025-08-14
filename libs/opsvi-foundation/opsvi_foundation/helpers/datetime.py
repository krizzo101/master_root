"""DateTime helper utilities for opsvi-foundation.

Provides timezone utilities, formatting, and duration calculations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

try:
    import pytz

    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False
    pytz = None

try:
    from dateutil import parser as date_parser
    from dateutil.relativedelta import relativedelta

    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    date_parser = None
    relativedelta = None

logger = logging.getLogger(__name__)


class DateTimeHelper:
    """DateTime manipulation utilities."""

    # Common date formats
    FORMATS = {
        "iso": "%Y-%m-%dT%H:%M:%S%z",
        "iso_basic": "%Y-%m-%d %H:%M:%S",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
        "us_date": "%m/%d/%Y",
        "eu_date": "%d/%m/%Y",
        "rfc2822": "%a, %d %b %Y %H:%M:%S %z",
        "timestamp": "%Y%m%d%H%M%S",
    }

    @staticmethod
    def parse_datetime(
        date_string: str, format_str: Optional[str] = None, fuzzy: bool = False
    ) -> Optional[datetime]:
        """Parse datetime string into datetime object.

        Args:
            date_string: String to parse
            format_str: Optional format string
            fuzzy: Use fuzzy parsing (requires dateutil)

        Returns:
            Parsed datetime or None
        """
        if not date_string:
            return None

        try:
            # Try specific format if provided
            if format_str:
                return datetime.strptime(date_string, format_str)

            # Try dateutil parser if available
            if HAS_DATEUTIL and date_parser:
                return date_parser.parse(date_string, fuzzy=fuzzy)

            # Try common formats
            for fmt in DateTimeHelper.FORMATS.values():
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue

            # Try ISO format
            return datetime.fromisoformat(date_string)

        except Exception as e:
            logger.debug(f"Failed to parse datetime '{date_string}': {e}")
            return None

    @staticmethod
    def format_datetime(
        dt: datetime,
        format_str: Optional[str] = None,
        format_name: Optional[str] = None,
    ) -> str:
        """Format datetime to string.

        Args:
            dt: Datetime to format
            format_str: Format string
            format_name: Named format from FORMATS

        Returns:
            Formatted datetime string
        """
        if format_str:
            return dt.strftime(format_str)
        elif format_name and format_name in DateTimeHelper.FORMATS:
            return dt.strftime(DateTimeHelper.FORMATS[format_name])
        else:
            return dt.isoformat()

    @staticmethod
    def get_timezone(tz_name: str) -> Optional[timezone]:
        """Get timezone object by name.

        Args:
            tz_name: Timezone name (e.g., 'UTC', 'US/Eastern')

        Returns:
            Timezone object or None
        """
        if tz_name == "UTC":
            return timezone.utc

        if HAS_PYTZ and pytz:
            try:
                return pytz.timezone(tz_name)
            except pytz.exceptions.UnknownTimeZoneError:
                logger.error(f"Unknown timezone: {tz_name}")
                return None
        else:
            logger.warning("pytz not available, only UTC timezone supported")
            return timezone.utc if tz_name == "UTC" else None

    @staticmethod
    def convert_timezone(
        dt: datetime,
        from_tz: Optional[Union[str, timezone]] = None,
        to_tz: Optional[Union[str, timezone]] = None,
    ) -> datetime:
        """Convert datetime between timezones.

        Args:
            dt: Datetime to convert
            from_tz: Source timezone (name or object)
            to_tz: Target timezone (name or object)

        Returns:
            Converted datetime
        """
        # Get timezone objects
        if isinstance(from_tz, str):
            from_tz = DateTimeHelper.get_timezone(from_tz)
        if isinstance(to_tz, str):
            to_tz = DateTimeHelper.get_timezone(to_tz)

        # Make datetime aware if needed
        if dt.tzinfo is None and from_tz:
            dt = dt.replace(tzinfo=from_tz)

        # Convert to target timezone
        if to_tz:
            return dt.astimezone(to_tz)

        return dt

    @staticmethod
    def calculate_duration(
        start: datetime, end: datetime, unit: str = "seconds"
    ) -> Union[int, float]:
        """Calculate duration between two datetimes.

        Args:
            start: Start datetime
            end: End datetime
            unit: Unit for duration (seconds, minutes, hours, days)

        Returns:
            Duration in specified unit
        """
        delta = end - start
        total_seconds = delta.total_seconds()

        if unit == "seconds":
            return total_seconds
        elif unit == "minutes":
            return total_seconds / 60
        elif unit == "hours":
            return total_seconds / 3600
        elif unit == "days":
            return delta.days
        else:
            return total_seconds

    @staticmethod
    def add_duration(
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        weeks: int = 0,
        months: int = 0,
        years: int = 0,
    ) -> datetime:
        """Add duration to datetime.

        Args:
            dt: Base datetime
            days: Days to add
            hours: Hours to add
            minutes: Minutes to add
            seconds: Seconds to add
            weeks: Weeks to add
            months: Months to add (requires dateutil)
            years: Years to add (requires dateutil)

        Returns:
            New datetime
        """
        # Handle basic timedelta additions
        result = dt + timedelta(
            days=days, hours=hours, minutes=minutes, seconds=seconds, weeks=weeks
        )

        # Handle months and years if dateutil available
        if (months or years) and HAS_DATEUTIL and relativedelta:
            result = result + relativedelta(months=months, years=years)
        elif months or years:
            logger.warning(
                "Month/year addition requires dateutil package. "
                "Install with: pip install python-dateutil"
            )

        return result

    @staticmethod
    def subtract_duration(
        dt: datetime,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
        weeks: int = 0,
        months: int = 0,
        years: int = 0,
    ) -> datetime:
        """Subtract duration from datetime.

        Args:
            dt: Base datetime
            days: Days to subtract
            hours: Hours to subtract
            minutes: Minutes to subtract
            seconds: Seconds to subtract
            weeks: Weeks to subtract
            months: Months to subtract (requires dateutil)
            years: Years to subtract (requires dateutil)

        Returns:
            New datetime
        """
        return DateTimeHelper.add_duration(
            dt,
            days=-days,
            hours=-hours,
            minutes=-minutes,
            seconds=-seconds,
            weeks=-weeks,
            months=-months,
            years=-years,
        )

    @staticmethod
    def is_past(dt: datetime, reference: Optional[datetime] = None) -> bool:
        """Check if datetime is in the past.

        Args:
            dt: Datetime to check
            reference: Reference datetime (default: now)

        Returns:
            True if in past
        """
        reference = reference or datetime.now(dt.tzinfo)
        return dt < reference

    @staticmethod
    def is_future(dt: datetime, reference: Optional[datetime] = None) -> bool:
        """Check if datetime is in the future.

        Args:
            dt: Datetime to check
            reference: Reference datetime (default: now)

        Returns:
            True if in future
        """
        reference = reference or datetime.now(dt.tzinfo)
        return dt > reference

    @staticmethod
    def time_until(dt: datetime, reference: Optional[datetime] = None) -> timedelta:
        """Calculate time until a datetime.

        Args:
            dt: Target datetime
            reference: Reference datetime (default: now)

        Returns:
            Timedelta until target
        """
        reference = reference or datetime.now(dt.tzinfo)
        return dt - reference

    @staticmethod
    def time_since(dt: datetime, reference: Optional[datetime] = None) -> timedelta:
        """Calculate time since a datetime.

        Args:
            dt: Past datetime
            reference: Reference datetime (default: now)

        Returns:
            Timedelta since target
        """
        reference = reference or datetime.now(dt.tzinfo)
        return reference - dt

    @staticmethod
    def get_timestamp(dt: Optional[datetime] = None) -> float:
        """Get Unix timestamp from datetime.

        Args:
            dt: Datetime (default: now)

        Returns:
            Unix timestamp
        """
        dt = dt or datetime.now()
        return dt.timestamp()

    @staticmethod
    def from_timestamp(timestamp: float, tz: Optional[timezone] = None) -> datetime:
        """Create datetime from Unix timestamp.

        Args:
            timestamp: Unix timestamp
            tz: Timezone for result

        Returns:
            Datetime object
        """
        return datetime.fromtimestamp(timestamp, tz=tz)

    @staticmethod
    def humanize_duration(seconds: float) -> str:
        """Convert duration to human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Human-readable duration
        """
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
        else:
            days = seconds / 86400
            return f"{days:.1f} days"


# Convenience functions
def parse_datetime(
    date_string: str, format_str: Optional[str] = None, fuzzy: bool = False
) -> Optional[datetime]:
    """Parse datetime string."""
    return DateTimeHelper.parse_datetime(date_string, format_str, fuzzy)


def format_datetime(
    dt: datetime, format_str: Optional[str] = None, format_name: Optional[str] = None
) -> str:
    """Format datetime to string."""
    return DateTimeHelper.format_datetime(dt, format_str, format_name)


def get_timezone(tz_name: str) -> Optional[timezone]:
    """Get timezone object by name."""
    return DateTimeHelper.get_timezone(tz_name)


def convert_timezone(
    dt: datetime,
    from_tz: Optional[Union[str, timezone]] = None,
    to_tz: Optional[Union[str, timezone]] = None,
) -> datetime:
    """Convert datetime between timezones."""
    return DateTimeHelper.convert_timezone(dt, from_tz, to_tz)


def calculate_duration(
    start: datetime, end: datetime, unit: str = "seconds"
) -> Union[int, float]:
    """Calculate duration between two datetimes."""
    return DateTimeHelper.calculate_duration(start, end, unit)


def add_duration(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    weeks: int = 0,
    months: int = 0,
    years: int = 0,
) -> datetime:
    """Add duration to datetime."""
    return DateTimeHelper.add_duration(
        dt, days, hours, minutes, seconds, weeks, months, years
    )


def subtract_duration(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0,
    weeks: int = 0,
    months: int = 0,
    years: int = 0,
) -> datetime:
    """Subtract duration from datetime."""
    return DateTimeHelper.subtract_duration(
        dt, days, hours, minutes, seconds, weeks, months, years
    )


def is_past(dt: datetime, reference: Optional[datetime] = None) -> bool:
    """Check if datetime is in the past."""
    return DateTimeHelper.is_past(dt, reference)


def is_future(dt: datetime, reference: Optional[datetime] = None) -> bool:
    """Check if datetime is in the future."""
    return DateTimeHelper.is_future(dt, reference)


def time_until(dt: datetime, reference: Optional[datetime] = None) -> timedelta:
    """Calculate time until a datetime."""
    return DateTimeHelper.time_until(dt, reference)


def time_since(dt: datetime, reference: Optional[datetime] = None) -> timedelta:
    """Calculate time since a datetime."""
    return DateTimeHelper.time_since(dt, reference)


def get_timestamp(dt: Optional[datetime] = None) -> float:
    """Get Unix timestamp from datetime."""
    return DateTimeHelper.get_timestamp(dt)


def from_timestamp(timestamp: float, tz: Optional[timezone] = None) -> datetime:
    """Create datetime from Unix timestamp."""
    return DateTimeHelper.from_timestamp(timestamp, tz)


__all__ = [
    "DateTimeHelper",
    "parse_datetime",
    "format_datetime",
    "get_timezone",
    "convert_timezone",
    "calculate_duration",
    "add_duration",
    "subtract_duration",
    "is_past",
    "is_future",
    "time_until",
    "time_since",
    "get_timestamp",
    "from_timestamp",
]
