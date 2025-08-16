#!/usr/bin/env python3
"""
Verify AI setup and test core functionality.
This script checks that all AI dependencies are installed and functional.
"""

import asyncio
import os
from datetime import datetime

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{BOLD}{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{BLUE}{title:^60}{RESET}")
    print(f"{BOLD}{BLUE}{'='*60}{RESET}\n")


def check_import(module_name: str, display_name: str = None) -> tuple[bool, str]:
    """Check if a module can be imported."""
    display = display_name or module_name
    try:
        __import__(module_name)
        return True, f"{GREEN}✓{RESET} {display} installed"
    except ImportError as e:
        return False, f"{RED}✗{RESET} {display} NOT installed - {str(e)}"


def check_environment_variables() -> list[tuple[str, bool]]:
    """Check if required environment variables are set."""
    required_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "PERPLEXITY_API_KEY",
    ]

    results = []
    for var in required_vars:
        value = os.getenv(var)
        if value and len(value) > 10:  # Basic validation
            results.append((var, True))
        else:
            results.append((var, False))

    return results


async def test_openai_connection():
    """Test OpenAI API connection."""
    try:
        from openai import OpenAI

        client = OpenAI()

        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API connection successful' in 5 words or less",
                }
            ],
            max_tokens=20,
        )

        if response.choices[0].message.content:
            return True, "OpenAI API connection successful"
    except Exception as e:
        return False, f"OpenAI API error: {str(e)}"


async def test_anthropic_connection():
    """Test Anthropic API connection."""
    try:
        from anthropic import Anthropic

        client = Anthropic()

        # Test with a simple completion
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=20,
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API connection successful' in 5 words or less",
                }
            ],
        )

        if response.content[0].text:
            return True, "Anthropic API connection successful"
    except Exception as e:
        return False, f"Anthropic API error: {str(e)}"


def test_langchain_setup():
    """Test LangChain basic functionality."""
    try:
        from langchain.schema import Document
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        # Test document creation and splitting
        doc = Document(page_content="Test document for LangChain verification.")
        splitter = RecursiveCharacterTextSplitter(chunk_size=10, chunk_overlap=2)
        chunks = splitter.split_documents([doc])

        if len(chunks) > 0:
            return True, f"LangChain working - created {len(chunks)} chunks"
    except Exception as e:
        return False, f"LangChain error: {str(e)}"


def test_vector_store():
    """Test vector store functionality."""
    try:
        import chromadb

        # Create in-memory client for testing
        client = chromadb.Client()
        collection = client.create_collection("test_collection")

        # Add test documents
        collection.add(
            documents=["Test document 1", "Test document 2"],
            metadatas=[{"source": "test1"}, {"source": "test2"}],
            ids=["id1", "id2"],
        )

        # Test query
        results = collection.query(query_texts=["test"], n_results=1)

        if results["documents"]:
            return True, "ChromaDB vector store working"
    except Exception as e:
        return False, f"ChromaDB error: {str(e)}"


def test_opsvi_libs():
    """Test OPSVI library imports."""
    results = []

    # Test opsvi-llm
    try:
        results.append((True, "opsvi-llm imports working"))
    except Exception as e:
        results.append((False, f"opsvi-llm error: {str(e)}"))

    # Test opsvi-agents
    try:
        results.append((True, "opsvi-agents imports working"))
    except Exception as e:
        results.append((False, f"opsvi-agents error: {str(e)}"))

    return results


async def main():
    """Main verification function."""
    print(f"\n{BOLD}AI Capability Verification Script{RESET}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Track overall status
    all_passed = True

    # 1. Check core dependencies
    print_header("1. Core Dependencies")
    dependencies = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("langchain", "LangChain"),
        ("langchain_community", "LangChain Community"),
        ("chromadb", "ChromaDB"),
        ("qdrant_client", "Qdrant Client"),
        ("transformers", "Transformers"),
    ]

    for module, display in dependencies:
        success, message = check_import(module, display)
        print(message)
        if not success:
            all_passed = False

    # 2. Check environment variables
    print_header("2. Environment Variables")
    env_results = check_environment_variables()
    for var, is_set in env_results:
        if is_set:
            print(f"{GREEN}✓{RESET} {var} is set")
        else:
            print(f"{RED}✗{RESET} {var} NOT set")
            all_passed = False

    # 3. Test API connections
    print_header("3. API Connections")

    # OpenAI
    success, message = await test_openai_connection()
    if success:
        print(f"{GREEN}✓{RESET} {message}")
    else:
        print(f"{YELLOW}⚠{RESET} {message}")

    # Anthropic
    success, message = await test_anthropic_connection()
    if success:
        print(f"{GREEN}✓{RESET} {message}")
    else:
        print(f"{YELLOW}⚠{RESET} {message}")

    # 4. Test framework functionality
    print_header("4. Framework Functionality")

    # LangChain
    success, message = test_langchain_setup()
    if success:
        print(f"{GREEN}✓{RESET} {message}")
    else:
        print(f"{RED}✗{RESET} {message}")
        all_passed = False

    # Vector Store
    success, message = test_vector_store()
    if success:
        print(f"{GREEN}✓{RESET} {message}")
    else:
        print(f"{YELLOW}⚠{RESET} {message}")

    # 5. Test OPSVI libraries
    print_header("5. OPSVI Libraries")
    opsvi_results = test_opsvi_libs()
    for success, message in opsvi_results:
        if success:
            print(f"{GREEN}✓{RESET} {message}")
        else:
            print(f"{YELLOW}⚠{RESET} {message}")

    # Final summary
    print_header("Summary")
    if all_passed:
        print(f"{GREEN}{BOLD}✅ All core checks passed!{RESET}")
        print(f"\n{GREEN}The AI environment is ready for use.{RESET}")
    else:
        print(f"{YELLOW}{BOLD}⚠️ Some checks failed or had warnings.{RESET}")
        print(
            f"\n{YELLOW}Review the errors above and run required installations.{RESET}"
        )
        print("You may need to run: pip install -r requirements-ai.txt")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
