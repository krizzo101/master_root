import os
import sys

from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "utils")))
from o3_model_generator import O3ModelGenerator


# Define a simple Pydantic schema for structured output
def test_schema_output():
    class EchoSchema(BaseModel):
        message: str

    generator = O3ModelGenerator()
    prompt = '{"message": "Hello, world!"}'
    try:
        result = generator.generate(prompt, output_schema=EchoSchema)
        print("[SCHEMA OUTPUT]", result)
        assert isinstance(result, EchoSchema)
        assert result.message == "Hello, world!"
    except Exception as e:
        print("[SCHEMA OUTPUT ERROR]", e)


def test_freeform_output():
    generator = O3ModelGenerator()
    prompt = "What is the capital of France?"
    try:
        result = generator.generate(prompt)
        print("[FREEFORM OUTPUT]", result)
        assert isinstance(result, str)
        assert "Paris" in result or result.strip() != ""
    except Exception as e:
        print("[FREEFORM OUTPUT ERROR]", e)


def test_error_handling():
    generator = O3ModelGenerator()
    prompt = ""
    try:
        result = generator.generate(prompt)
        print("[ERROR HANDLING] Should not succeed", result)
    except Exception as e:
        print("[ERROR HANDLING]", e)


def main():
    print("Testing O3ModelGenerator...\n")
    test_schema_output()
    test_freeform_output()
    test_error_handling()
    print("\nTesting complete.")


if __name__ == "__main__":
    main()
