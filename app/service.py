"""Small business rules: independently testable, no HTTP or database dependencies."""


def normalize_title(value):
    if not isinstance(value, str):
        raise ValueError("title must be a string")
    title = value.strip()
    if not 1 <= len(title) <= 120:
        raise ValueError("title must contain 1 to 120 characters")
    return title
