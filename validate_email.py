import re


def validate_email(email):
    """
    Validates an email address using regex.

    Args:
        email (str): The email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


# Test the function
if __name__ == "__main__":
    test_emails = [
        "user@example.com",
        "john.doe+filter@company.co.uk",
        "invalid.email",
        "@example.com",
        "user@",
        "user@domain",
        "user.name@sub.domain.com",
    ]

    for email in test_emails:
        result = validate_email(email)
        print(f"{email}: {'Valid' if result else 'Invalid'}")
