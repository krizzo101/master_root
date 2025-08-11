# Pydantic Configuration Fix for OpenAI Structured Outputs
# All models need extra = "forbid" for OpenAI API compatibility


from pydantic import BaseModel


class StrictBaseModel(BaseModel):
    """Base model with strict validation for OpenAI structured outputs"""

    class Config:
        extra = "forbid"

    # Don't override model_json_schema - let Pydantic handle required fields correctly
    # OpenAI should accept the default Pydantic schema
