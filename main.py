def add(a, b):
    """Returns the sum of a and b."""
    return a + b


def subtract(a, b):
    """Returns the difference of a and b."""
    return a - b


def multiply(a, b):
    """Returns the product of a and b."""
    return a * b


def divide(a, b):
    """Returns the quotient of a and b. Raises ValueError if b is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero!")
    return a / b


def run_operations():
    """Runs the mathematical operations with some example values."""
    x = 10
    y = 5

    print(f"Addition of {x} and {y}: {add(x, y)}")
    print(f"Subtraction of {x} and {y}: {subtract(x, y)}")
    print(f"Multiplication of {x} and {y}: {multiply(x, y)}")
    print(f"Division of {x} and {y}: {divide(x, y)}")


if __name__ == "__main__":
    run_operations()
