"""Mock data generator for testing."""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.models import Business, IntelligenceReport, Person, Query


class MockDataGenerator:
    """Generate mock data for testing."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the mock data generator."""
        if seed:
            random.seed(seed)

        self.first_names = [
            "John",
            "Jane",
            "Michael",
            "Sarah",
            "David",
            "Emily",
            "Robert",
            "Lisa",
        ]
        self.last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
        ]
        self.cities = [
            "New York",
            "Los Angeles",
            "Chicago",
            "Houston",
            "Phoenix",
            "Philadelphia",
            "San Antonio",
        ]
        self.states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX"]
        self.business_types = [
            "LLC",
            "Corporation",
            "Partnership",
            "Sole Proprietorship",
        ]
        self.industries = [
            "Technology",
            "Healthcare",
            "Finance",
            "Retail",
            "Manufacturing",
            "Education",
        ]

    def random_string(self, length: int = 10) -> str:
        """Generate a random string."""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def random_email(
        self, first_name: Optional[str] = None, last_name: Optional[str] = None
    ) -> str:
        """Generate a random email address."""
        if not first_name:
            first_name = random.choice(self.first_names)
        if not last_name:
            last_name = random.choice(self.last_names)

        domains = [
            "gmail.com",
            "yahoo.com",
            "outlook.com",
            "company.com",
            "example.org",
        ]
        return f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"

    def random_phone(self) -> str:
        """Generate a random phone number."""
        area_code = random.randint(200, 999)
        exchange = random.randint(200, 999)
        number = random.randint(1000, 9999)
        return f"({area_code}) {exchange}-{number}"

    def random_address(self) -> Dict[str, Any]:
        """Generate a random address."""
        street_number = random.randint(1, 9999)
        street_names = [
            "Main St",
            "Oak Ave",
            "Elm Rd",
            "Park Blvd",
            "Washington St",
            "First Ave",
        ]

        return {
            "street": f"{street_number} {random.choice(street_names)}",
            "city": random.choice(self.cities),
            "state": random.choice(self.states),
            "zip": f"{random.randint(10000, 99999)}",
            "country": "USA",
        }

    def create_person(self, **kwargs) -> Person:
        """Create a mock Person object."""
        first_name = kwargs.get("first_name", random.choice(self.first_names))
        last_name = kwargs.get("last_name", random.choice(self.last_names))

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "middle_name": kwargs.get(
                "middle_name", random.choice(["A", "B", "C", ""])
            ),
            "age": kwargs.get("age", random.randint(18, 80)),
            "date_of_birth": kwargs.get(
                "date_of_birth",
                (datetime.now() - timedelta(days=random.randint(6570, 29200))).strftime(
                    "%Y-%m-%d"
                ),
            ),
            "emails": kwargs.get("emails", [self.random_email(first_name, last_name)]),
            "phones": kwargs.get("phones", [self.random_phone()]),
            "addresses": kwargs.get("addresses", [self.random_address()]),
            "ssn_last_four": kwargs.get(
                "ssn_last_four", f"{random.randint(1000, 9999)}"
            ),
            "employment": kwargs.get(
                "employment",
                {
                    "company": f"{random.choice(['Tech', 'Global', 'United'])} {random.choice(['Corp', 'Inc', 'LLC'])}",
                    "position": random.choice(
                        ["Manager", "Engineer", "Director", "Analyst"]
                    ),
                    "start_date": (
                        datetime.now() - timedelta(days=random.randint(365, 3650))
                    ).strftime("%Y-%m-%d"),
                },
            ),
            "education": kwargs.get(
                "education",
                [
                    {
                        "institution": f"{random.choice(['State', 'City', 'National'])} University",
                        "degree": random.choice(["Bachelor's", "Master's", "PhD"]),
                        "field": random.choice(
                            ["Computer Science", "Business", "Engineering", "Medicine"]
                        ),
                        "graduation_year": random.randint(1990, 2023),
                    }
                ],
            ),
            "social_media": kwargs.get(
                "social_media",
                {
                    "linkedin": f"linkedin.com/in/{first_name.lower()}-{last_name.lower()}",
                    "twitter": f"@{first_name.lower()}{random.randint(100, 999)}",
                },
            ),
            "relatives": kwargs.get("relatives", []),
            "criminal_records": kwargs.get("criminal_records", []),
            "financial_records": kwargs.get(
                "financial_records", {"bankruptcies": [], "liens": [], "judgments": []}
            ),
            "metadata": kwargs.get(
                "metadata",
                {
                    "source": "mock_generator",
                    "confidence": random.uniform(0.7, 1.0),
                    "last_updated": datetime.now().isoformat(),
                },
            ),
        }

        return Person(**data)

    def create_business(self, **kwargs) -> Business:
        """Create a mock Business object."""
        business_name = kwargs.get(
            "name",
            f"{random.choice(['Tech', 'Global', 'United', 'Premier'])} "
            f"{random.choice(['Solutions', 'Services', 'Industries', 'Group'])} "
            f"{random.choice(self.business_types)}",
        )

        data = {
            "name": business_name,
            "type": kwargs.get("type", random.choice(self.business_types)),
            "ein": kwargs.get(
                "ein", f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
            ),
            "formation_date": kwargs.get(
                "formation_date",
                (datetime.now() - timedelta(days=random.randint(365, 7300))).strftime(
                    "%Y-%m-%d"
                ),
            ),
            "status": kwargs.get(
                "status", random.choice(["Active", "Inactive", "Dissolved"])
            ),
            "addresses": kwargs.get("addresses", [self.random_address()]),
            "phones": kwargs.get("phones", [self.random_phone()]),
            "website": kwargs.get(
                "website", f"www.{business_name.lower().replace(' ', '')}.com"
            ),
            "email": kwargs.get(
                "email", f"info@{business_name.lower().replace(' ', '')}.com"
            ),
            "industry": kwargs.get("industry", random.choice(self.industries)),
            "naics_code": kwargs.get("naics_code", f"{random.randint(100000, 999999)}"),
            "sic_code": kwargs.get("sic_code", f"{random.randint(1000, 9999)}"),
            "employees": kwargs.get("employees", random.randint(1, 10000)),
            "revenue": kwargs.get("revenue", random.randint(100000, 100000000)),
            "officers": kwargs.get(
                "officers",
                [
                    {
                        "name": f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
                        "title": random.choice(
                            ["CEO", "President", "CFO", "CTO", "Director"]
                        ),
                        "start_date": (
                            datetime.now() - timedelta(days=random.randint(365, 3650))
                        ).strftime("%Y-%m-%d"),
                    }
                ],
            ),
            "licenses": kwargs.get("licenses", []),
            "legal_filings": kwargs.get("legal_filings", []),
            "metadata": kwargs.get(
                "metadata",
                {
                    "source": "mock_generator",
                    "confidence": random.uniform(0.7, 1.0),
                    "last_updated": datetime.now().isoformat(),
                },
            ),
        }

        return Business(**data)

    def create_query(self, query_type: str = "person_search", **kwargs) -> Query:
        """Create a mock Query object."""
        parameters = kwargs.get("parameters", {})

        if query_type == "person_search" and not parameters:
            parameters = {
                "first_name": random.choice(self.first_names),
                "last_name": random.choice(self.last_names),
                "city": random.choice(self.cities),
                "state": random.choice(self.states),
            }
        elif query_type == "business_search" and not parameters:
            parameters = {
                "name": f"{random.choice(['Tech', 'Global'])} Solutions",
                "state": random.choice(self.states),
            }

        return Query(
            query_type=query_type,
            parameters=parameters,
            metadata=kwargs.get(
                "metadata",
                {
                    "request_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat(),
                    "user": "test_user",
                },
            ),
        )

    def create_intelligence_report(self, **kwargs) -> IntelligenceReport:
        """Create a mock Intelligence Report."""
        return IntelligenceReport(
            subject=kwargs.get(
                "subject",
                f"{random.choice(self.first_names)} {random.choice(self.last_names)}",
            ),
            summary=kwargs.get("summary", "Mock intelligence report summary"),
            findings=kwargs.get(
                "findings",
                [
                    {
                        "category": "personal",
                        "confidence": random.uniform(0.7, 1.0),
                        "data": self.create_person().__dict__,
                    },
                    {
                        "category": "business",
                        "confidence": random.uniform(0.6, 0.9),
                        "data": self.create_business().__dict__,
                    },
                ],
            ),
            risk_assessment=kwargs.get(
                "risk_assessment",
                {
                    "level": random.choice(["low", "medium", "high"]),
                    "factors": ["Factor 1", "Factor 2"],
                    "score": random.uniform(0, 100),
                },
            ),
            recommendations=kwargs.get(
                "recommendations",
                [
                    "Continue monitoring",
                    "Verify information through additional sources",
                    "No immediate action required",
                ],
            ),
            metadata=kwargs.get(
                "metadata",
                {
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "analyst": "mock_system",
                },
            ),
        )

    def create_bulk_persons(self, count: int = 10) -> List[Person]:
        """Create multiple mock Person objects."""
        return [self.create_person() for _ in range(count)]

    def create_bulk_businesses(self, count: int = 10) -> List[Business]:
        """Create multiple mock Business objects."""
        return [self.create_business() for _ in range(count)]

    def create_api_response(
        self, status: int = 200, data: Any = None, error: Optional[str] = None
    ) -> Dict:
        """Create a mock API response."""
        response = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4()),
        }

        if error:
            response["error"] = error
            response["message"] = f"Mock error: {error}"
        else:
            response["data"] = data if data is not None else []
            response["count"] = len(data) if isinstance(data, list) else 1

        return response
