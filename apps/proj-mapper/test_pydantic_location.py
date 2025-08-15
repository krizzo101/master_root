from src.proj_mapper.models.code import Location, LocationModel
from pydantic import BaseModel
class TestModel(BaseModel):
    loc: Location
model = TestModel(loc=Location(file_path="/test.py"))
print(model.model_dump())
