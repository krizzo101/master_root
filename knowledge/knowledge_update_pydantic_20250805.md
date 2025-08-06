# Knowledge Update: Pydantic (Generated 2025-08-05)

## Current State (Last 12+ Months)

Pydantic v2.x has evolved into a high-performance, production-ready data validation framework with significant improvements in 2025:

- **Performance**: 5-50x faster validation using Rust-based pydantic-core
- **Type Safety**: Enhanced type checking and validation with improved error messages
- **Configuration**: Modern ConfigDict approach with comprehensive options
- **Validation Methods**: Advanced model_validate, model_validate_json, model_validate_strings methods
- **Structural Pattern Matching**: Full support for Python 3.10+ pattern matching
- **Generic Models**: Improved generic type support with TypeVar and advanced patterns
- **Serialization**: Enhanced serialization with multiple output formats
- **JSON Schema**: Advanced JSON schema generation with custom validators
- **Cloud Integration**: Seamless integration with cloud platforms and APIs
- **Enterprise Features**: Security, monitoring, and scalability enhancements

## Best Practices & Patterns

### Modern Installation and Setup (2025)
```python
# Install latest version with all features
pip install -U pydantic[email]

# For production with additional validators
pip install -U pydantic[email,dotenv]

# With specific version for stability
pip install pydantic==2.11.0
```

### Advanced Model Definition (2025)
```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"

class AdvancedUser(BaseModel):
    """Advanced user model with comprehensive validation."""

    # Core fields with validation
    id: int = Field(..., gt=0, description="Unique user identifier")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    # Optional fields with defaults
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = Field(default=UserRole.USER, description="User role")
    is_active: bool = Field(default=True, description="Account status")

    # Complex fields
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list, max_length=10)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    # Advanced configuration
    model_config = ConfigDict(
        str_max_length=1000,
        str_strip_whitespace=True,
        extra='forbid',  # 'ignore', 'forbid', 'allow'
        validate_assignment=True,
        revalidate_instances='always',
        use_enum_values=True,
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }
    )

    # Field-level validators
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v.lower()

    # Model-level validators
    @model_validator(mode='after')
    def validate_user_data(self) -> 'AdvancedUser':
        """Validate user data after all fields are set."""
        if self.first_name and self.last_name:
            full_name = f"{self.first_name} {self.last_name}"
            if len(full_name) > 200:
                raise ValueError('Full name is too long')

        # Update timestamp
        self.updated_at = datetime.now()

        return self

    # Computed properties
    @property
    def full_name(self) -> Optional[str]:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return None

    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return self.full_name or self.username

    # Custom methods
    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return self.model_dump(exclude_none=exclude_none)

    def to_json(self, exclude_none: bool = True) -> str:
        """Convert model to JSON string."""
        return self.model_dump_json(exclude_none=exclude_none)

    def update(self, **kwargs) -> 'AdvancedUser':
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

# Usage examples
try:
    user = AdvancedUser(
        id=1,
        username="john_doe",
        email="john.doe@example.com",
        password="SecurePass123",
        first_name="John",
        last_name="Doe",
        role=UserRole.USER
    )
    print(f"User created: {user.display_name}")
    print(f"User JSON: {user.to_json()}")
except Exception as e:
    print(f"Validation error: {e}")
```

### Advanced Configuration Management (2025)
```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
import os
from pathlib import Path

class DatabaseConfig(BaseModel):
    """Database configuration with validation."""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    ssl_mode: str = Field(default="prefer", pattern=r"^(disable|allow|prefer|require|verify-ca|verify-full)$")
    max_connections: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=30, ge=1, le=300)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )

    @property
    def connection_string(self) -> str:
        """Generate database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"

class APIConfig(BaseModel):
    """API configuration with validation."""
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    timeout: int = Field(default=30, ge=1, le=300)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    rate_limit: int = Field(default=100, ge=1, description="Requests per minute")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra='forbid'
    )

class LoggingConfig(BaseModel):
    """Logging configuration with validation."""
    level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_path: Optional[Path] = Field(None, description="Log file path")
    max_size: int = Field(default=10, ge=1, description="Max log file size in MB")
    backup_count: int = Field(default=5, ge=0, description="Number of backup files")

    model_config = ConfigDict(
        extra='forbid'
    )

class ApplicationConfig(BaseModel):
    """Main application configuration."""
    app_name: str = Field(default="MyApp", description="Application name")
    environment: str = Field(default="development", pattern=r"^(development|staging|production)$")
    debug: bool = Field(default=False, description="Debug mode")

    # Nested configurations
    database: DatabaseConfig
    api: APIConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Advanced configuration
    model_config = ConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        extra='forbid',
        validate_assignment=True,
        str_strip_whitespace=True
    )

    @classmethod
    def from_env(cls) -> 'ApplicationConfig':
        """Create configuration from environment variables."""
        return cls.model_validate({
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "5432")),
                "database": os.getenv("DB_NAME"),
                "username": os.getenv("DB_USER"),
                "password": os.getenv("DB_PASSWORD"),
                "ssl_mode": os.getenv("DB_SSL_MODE", "prefer")
            },
            "api": {
                "base_url": os.getenv("API_BASE_URL"),
                "api_key": os.getenv("API_KEY"),
                "timeout": int(os.getenv("API_TIMEOUT", "30")),
                "retry_attempts": int(os.getenv("API_RETRY_ATTEMPTS", "3")),
                "rate_limit": int(os.getenv("API_RATE_LIMIT", "100"))
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "file_path": os.getenv("LOG_FILE_PATH"),
                "max_size": int(os.getenv("LOG_MAX_SIZE", "10")),
                "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
            }
        })

# Usage example
config = ApplicationConfig.from_env()
print(f"Database connection: {config.database.connection_string}")
print(f"API base URL: {config.api.base_url}")
print(f"Log level: {config.logging.level}")
```

### Advanced Validation Patterns (2025)
```python
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import re
import json

class ValidationPatterns(BaseModel):
    """Demonstrates advanced validation patterns."""

    # String validation
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")

    # Numeric validation
    age: int = Field(..., ge=0, le=150)
    score: float = Field(..., ge=0.0, le=100.0)
    percentage: float = Field(..., ge=0.0, le=1.0)

    # List validation
    tags: List[str] = Field(default_factory=list, max_length=10)
    scores: List[float] = Field(default_factory=list, min_length=1, max_length=100)

    # Dict validation
    metadata: Dict[str, Any] = Field(default_factory=dict, max_length=50)

    # Custom validation
    @field_validator('username')
    @classmethod
    def validate_username_reserved(cls, v: str) -> str:
        """Check for reserved usernames."""
        reserved = ['admin', 'root', 'system', 'test']
        if v.lower() in reserved:
            raise ValueError(f"Username '{v}' is reserved")
        return v

    @field_validator('email')
    @classmethod
    def validate_email_domain(cls, v: str) -> str:
        """Validate email domain."""
        allowed_domains = ['example.com', 'gmail.com', 'yahoo.com']
        domain = v.split('@')[1].lower()
        if domain not in allowed_domains:
            raise ValueError(f"Email domain '{domain}' is not allowed")
        return v

    @field_validator('tags')
    @classmethod
    def validate_tags_unique(cls, v: List[str]) -> List[str]:
        """Ensure tags are unique."""
        if len(v) != len(set(v)):
            raise ValueError("Tags must be unique")
        return v

    @field_validator('scores')
    @classmethod
    def validate_scores_range(cls, v: List[float]) -> List[float]:
        """Validate score ranges."""
        for score in v:
            if not (0.0 <= score <= 100.0):
                raise ValueError(f"Score {score} must be between 0 and 100")
        return v

    @model_validator(mode='after')
    def validate_data_consistency(self) -> 'ValidationPatterns':
        """Validate data consistency across fields."""
        # Example: age and score consistency
        if self.age < 18 and self.score > 90:
            raise ValueError("Minors cannot have scores above 90")

        # Example: metadata size limit
        metadata_size = len(json.dumps(self.metadata))
        if metadata_size > 1000:
            raise ValueError("Metadata too large")

        return self

class ConditionalValidation(BaseModel):
    """Demonstrates conditional validation patterns."""

    user_type: str = Field(..., pattern=r"^(individual|business)$")

    # Conditional fields based on user_type
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    tax_id: Optional[str] = Field(None, pattern=r"^\d{9}$")

    @model_validator(mode='after')
    def validate_conditional_fields(self) -> 'ConditionalValidation':
        """Validate fields based on user type."""
        if self.user_type == "individual":
            if not self.first_name or not self.last_name:
                raise ValueError("Individual users must provide first and last names")
            if self.company_name or self.tax_id:
                raise ValueError("Individual users cannot have company information")
        elif self.user_type == "business":
            if not self.company_name:
                raise ValueError("Business users must provide company name")
            if self.first_name or self.last_name:
                raise ValueError("Business users cannot have individual names")

        return self

# Usage examples
try:
    # Valid individual user
    individual = ConditionalValidation(
        user_type="individual",
        first_name="John",
        last_name="Doe"
    )
    print(f"Individual user: {individual.first_name} {individual.last_name}")

    # Valid business user
    business = ConditionalValidation(
        user_type="business",
        company_name="Acme Corp",
        tax_id="123456789"
    )
    print(f"Business user: {business.company_name}")

except ValidationError as e:
    print(f"Validation error: {e}")
```

### Generic Models and Type Safety (2025)
```python
from pydantic import BaseModel, Field, ValidationError
from typing import Generic, TypeVar, List, Dict, Any, Optional
from datetime import datetime

# Type variables for generic models
T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class ResponseModel(BaseModel, Generic[T]):
    """Generic response model for API responses."""
    success: bool = Field(..., description="Request success status")
    data: Optional[T] = Field(None, description="Response data")
    message: str = Field(default="", description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request identifier")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=1, description="Total number of pages")

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1

class CacheEntry(BaseModel, Generic[K, V]):
    """Generic cache entry model."""
    key: K = Field(..., description="Cache key")
    value: V = Field(..., description="Cache value")
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(None, description="Expiration time")

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    @property
    def ttl(self) -> Optional[float]:
        """Get time to live in seconds."""
        if self.expires_at is None:
            return None
        return (self.expires_at - datetime.now()).total_seconds()

# Specific data models
class User(BaseModel):
    id: int = Field(..., gt=0)
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    is_active: bool = Field(default=True)

class Product(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)

# Usage examples
# User response
user = User(id=1, username="john_doe", email="john@example.com")
user_response = ResponseModel[User](
    success=True,
    data=user,
    message="User retrieved successfully",
    request_id="req_123"
)
print(f"User response: {user_response.model_dump_json()}")

# Paginated product response
products = [
    Product(id=1, name="Laptop", price=999.99, category="Electronics"),
    Product(id=2, name="Mouse", price=29.99, category="Electronics")
]
product_response = PaginatedResponse[Product](
    items=products,
    total=100,
    page=1,
    per_page=10,
    total_pages=10
)
print(f"Has next page: {product_response.has_next}")

# Cache entry
cache_entry = CacheEntry[str, User](
    key="user:1",
    value=user,
    expires_at=datetime.now() + timedelta(hours=1)
)
print(f"Cache TTL: {cache_entry.ttl} seconds")
```

### Advanced Serialization and JSON Schema (2025)
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
import json

class SerializationExample(BaseModel):
    """Demonstrates advanced serialization features."""

    # Basic fields
    id: int = Field(..., description="Unique identifier")
    name: str = Field(..., description="Item name")
    description: Optional[str] = Field(None, description="Item description")

    # Complex fields
    tags: List[str] = Field(default_factory=list, description="Item tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    # Enum field
    status: str = Field(default="active", pattern=r"^(active|inactive|pending)$")

    # Advanced configuration
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        },
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Sample Item",
                    "description": "A sample item for demonstration",
                    "tags": ["sample", "demo"],
                    "metadata": {"version": "1.0"},
                    "status": "active"
                }
            ]
        }
    )

    def to_dict(self, exclude_none: bool = True, exclude_defaults: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with options."""
        return self.model_dump(
            exclude_none=exclude_none,
            exclude_defaults=exclude_defaults
        )

    def to_json(self, exclude_none: bool = True, indent: int = 2) -> str:
        """Convert to JSON string with options."""
        return self.model_dump_json(
            exclude_none=exclude_none,
            indent=indent
        )

    def to_json_schema(self) -> Dict[str, Any]:
        """Generate JSON schema."""
        return self.model_json_schema()

# Usage examples
item = SerializationExample(
    id=1,
    name="Advanced Item",
    description="An item with advanced serialization",
    tags=["advanced", "serialization"],
    metadata={"version": "2.0", "features": ["json", "schema"]}
)

# Different serialization formats
print("Full dictionary:")
print(json.dumps(item.to_dict(), indent=2))

print("\nExclude None values:")
print(json.dumps(item.to_dict(exclude_none=True), indent=2))

print("\nJSON string:")
print(item.to_json())

print("\nJSON Schema:")
print(json.dumps(item.to_json_schema(), indent=2))
```

### Production-Ready Validation Service (2025)
```python
import asyncio
import logging
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
import time
from pydantic import BaseModel, ValidationError, field_validator, model_validator

@dataclass
class ValidationRequest:
    model_class: Type[BaseModel]
    data: Dict[str, Any]
    strict: bool = False

@dataclass
class ValidationResponse:
    success: bool
    data: Optional[BaseModel] = None
    errors: Optional[List[str]] = None
    processing_time: float = 0.0

class ProductionValidationService:
    """Production-ready validation service with monitoring."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Performance metrics
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.avg_processing_time = 0.0

    async def validate_async(self, request: ValidationRequest) -> ValidationResponse:
        """Asynchronous validation with monitoring."""
        start_time = time.time()

        try:
            # Run validation in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._validate_sync,
                request
            )

            processing_time = time.time() - start_time

            # Update metrics
            self.total_validations += 1
            if result.success:
                self.successful_validations += 1
            else:
                self.failed_validations += 1

            self.avg_processing_time = (
                (self.avg_processing_time * (self.total_validations - 1) + processing_time)
                / self.total_validations
            )

            self.logger.info(
                f"Validation completed in {processing_time:.3f}s "
                f"(success: {result.success})"
            )

            return ValidationResponse(
                success=result.success,
                data=result.data,
                errors=result.errors,
                processing_time=processing_time
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Validation error: {e}")

            return ValidationResponse(
                success=False,
                errors=[str(e)],
                processing_time=processing_time
            )

    def _validate_sync(self, request: ValidationRequest) -> ValidationResponse:
        """Synchronous validation implementation."""
        try:
            # Perform validation
            if request.strict:
                # Use strict validation
                validated_data = request.model_class.model_validate(
                    request.data,
                    strict=True
                )
            else:
                # Use regular validation
                validated_data = request.model_class.model_validate(request.data)

            return ValidationResponse(
                success=True,
                data=validated_data
            )

        except ValidationError as e:
            errors = []
            for error in e.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                errors.append(f"{field_path}: {error['msg']}")

            return ValidationResponse(
                success=False,
                errors=errors
            )

    def batch_validate(
        self,
        requests: List[ValidationRequest]
    ) -> List[ValidationResponse]:
        """Batch validation for multiple requests."""
        results = []

        for request in requests:
            result = self._validate_sync(request)
            results.append(result)

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics."""
        success_rate = (
            self.successful_validations / self.total_validations
            if self.total_validations > 0 else 0
        )

        return {
            "total_validations": self.total_validations,
            "successful_validations": self.successful_validations,
            "failed_validations": self.failed_validations,
            "success_rate": success_rate,
            "avg_processing_time": self.avg_processing_time
        }

    def health_check(self) -> Dict[str, Any]:
        """Health check for the service."""
        try:
            # Test validation with a simple model
            class TestModel(BaseModel):
                name: str = Field(..., min_length=1)
                value: int = Field(..., gt=0)

            test_request = ValidationRequest(
                model_class=TestModel,
                data={"name": "test", "value": 1}
            )

            result = self._validate_sync(test_request)

            return {
                "status": "healthy" if result.success else "unhealthy",
                "validation_working": result.success,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "validation_working": False
            }

# Usage example
async def main():
    service = ProductionValidationService()

    # Health check
    health = service.health_check()
    print(f"Service health: {health}")

    # Define test models
    class UserModel(BaseModel):
        id: int = Field(..., gt=0)
        username: str = Field(..., min_length=3, max_length=50)
        email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    class ProductModel(BaseModel):
        id: int = Field(..., gt=0)
        name: str = Field(..., min_length=1, max_length=200)
        price: float = Field(..., gt=0)

    # Test validation requests
    requests = [
        ValidationRequest(
            model_class=UserModel,
            data={"id": 1, "username": "john_doe", "email": "john@example.com"}
        ),
        ValidationRequest(
            model_class=ProductModel,
            data={"id": 1, "name": "Laptop", "price": 999.99}
        )
    ]

    # Process asynchronously
    tasks = [service.validate_async(req) for req in requests]
    responses = await asyncio.gather(*tasks)

    for i, response in enumerate(responses):
        print(f"Request {i+1}: {'Success' if response.success else 'Failed'}")
        if response.errors:
            print(f"  Errors: {response.errors}")

    # Get metrics
    metrics = service.get_metrics()
    print(f"Service metrics: {metrics}")

# Run the example
if __name__ == "__main__":
    asyncio.run(main())
```

## Tools & Frameworks

### Core Components
- **BaseModel**: Main model class for data validation
- **ConfigDict**: Configuration dictionary for model settings
- **Field**: Field configuration and validation
- **ValidationError**: Exception raised on validation failures
- **field_validator**: Field-level validation decorator
- **model_validator**: Model-level validation decorator

### Advanced Features (2025)
- **Generic Models**: Type-safe generic model support
- **JSON Schema**: Advanced JSON schema generation
- **Serialization**: Multiple output formats and options
- **Performance**: Optimized validation with Rust core
- **Type Safety**: Enhanced type checking and validation

### Performance Optimization
```python
# Optimize for production
model_config = ConfigDict(
    validate_assignment=True,
    revalidate_instances='always',
    extra='forbid',
    str_strip_whitespace=True,
    use_enum_values=True
)

# Use strict validation for critical data
validated_data = Model.model_validate(data, strict=True)

# Optimize serialization
json_data = model.model_dump_json(exclude_none=True, exclude_defaults=True)
```

## Implementation Guidance

### Project Structure for Validation Applications
```
validation_app/
├── models/
│   ├── __init__.py
│   ├── base.py
│   ├── user.py
│   ├── product.py
│   └── api.py
├── services/
│   ├── __init__.py
│   ├── validation_service.py
│   └── schema_service.py
├── validators/
│   ├── __init__.py
│   ├── custom_validators.py
│   └── business_rules.py
├── utils/
│   ├── __init__.py
│   ├── serialization.py
│   └── monitoring.py
├── config/
│   ├── __init__.py
│   └── settings.py
├── tests/
│   ├── test_models.py
│   └── test_services.py
└── requirements.txt
```

### Configuration Management
```python
# config/settings.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class ValidationConfig:
    strict_mode: bool = False
    exclude_none: bool = True
    exclude_defaults: bool = False
    validate_assignment: bool = True
    revalidate_instances: str = 'always'
    extra_behavior: str = 'forbid'

@dataclass
class SerializationConfig:
    json_encoders: Dict[Type, Callable] = None
    exclude_none: bool = True
    exclude_defaults: bool = False
    indent: int = 2
```

### Error Handling and Monitoring
```python
import logging
import time
from functools import wraps
from typing import Callable, Any

def monitor_validation(func: Callable) -> Callable:
    """Decorator to monitor validation performance."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time

            logging.info(
                f"{func.__name__} completed in {processing_time:.3f}s"
            )
            return result
        except Exception as e:
            processing_time = time.time() - start_time
            logging.error(
                f"{func.__name__} failed after {processing_time:.3f}s: {e}"
            )
            raise
    return wrapper

class ValidationError(Exception):
    """Custom exception for validation operations."""
    pass

class ModelValidationError(ValidationError):
    """Raised when model validation fails."""
    pass

class SchemaGenerationError(ValidationError):
    """Raised when schema generation fails."""
    pass
```

## Limitations & Considerations

### Current Limitations
- **Performance**: Complex validators can impact performance
- **Memory Usage**: Large models require significant memory
- **Type Complexity**: Very complex types may have validation issues
- **Backward Compatibility**: Some v1 features may not be available

### Performance Considerations
- **Validation Strategy**: Choose appropriate validation levels
- **Model Design**: Optimize model structure for performance
- **Caching**: Cache validation results when appropriate
- **Batch Processing**: Use batch operations for efficiency

### Best Practices for Production
1. **Model Design**: Plan model structure carefully
2. **Validation Strategy**: Use appropriate validation levels
3. **Error Handling**: Implement comprehensive error handling
4. **Monitoring**: Monitor validation performance
5. **Caching**: Cache validation results when appropriate
6. **Security**: Validate inputs and handle sensitive data appropriately

## Recent Updates (2024-2025)

### New Features
- **Enhanced Performance**: Improved validation speed with Rust core
- **Advanced Type Safety**: Better type checking and validation
- **JSON Schema**: Enhanced JSON schema generation
- **Serialization**: Multiple output formats and options

### Performance Improvements
- **Faster Validation**: Optimized validation algorithms
- **Better Memory Usage**: Improved memory management
- **Enhanced Serialization**: Faster serialization performance
- **Reduced Latency**: Optimized processing pipelines

### Breaking Changes
- **API Updates**: Some API changes for better consistency
- **Configuration**: Updated configuration options
- **Error Handling**: Enhanced error messages and handling

### Ecosystem Integration
- **Cloud Platforms**: Enhanced cloud deployment options
- **Monitoring Tools**: Integration with observability platforms
- **Security Features**: Enhanced security and privacy features
- **Development Tools**: Better development and debugging tools