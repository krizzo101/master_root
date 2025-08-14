def factorial(n, depth=0):
    """
    Calculate factorial recursively with call stack visualization.

    Args:
        n: The number to calculate factorial for
        depth: Current recursion depth (for visualization)

    Returns:
        The factorial of n
    """
    # Indentation for visualization
    indent = "  " * depth

    # Print entering the function
    print(f"{indent}factorial({n}) called")

    # Base case: factorial of 0 or 1 is 1
    if n <= 1:
        print(f"{indent}Base case reached: factorial({n}) = 1")
        return 1

    # Recursive case: n! = n * (n-1)!
    print(f"{indent}Computing: {n} * factorial({n-1})")
    result = n * factorial(n - 1, depth + 1)

    # Print the result of this recursive call
    print(f"{indent}factorial({n}) = {n} * {result // n} = {result}")

    return result


def main():
    """Main function to demonstrate factorial calculation."""
    print("=" * 60)
    print("RECURSIVE FACTORIAL CALCULATION")
    print("=" * 60)

    n = 5
    print(f"\nCalculating factorial of {n} recursively...")
    print("\nRECURSIVE CALL STACK:")
    print("-" * 40)

    # Calculate factorial
    result = factorial(n)

    print("-" * 40)
    print(f"\nFINAL RESULT: {n}! = {result}")

    # Show the mathematical expansion
    print("\nMATHEMATICAL EXPANSION:")
    print(f"{n}! = ", end="")
    for i in range(n, 0, -1):
        if i > 1:
            print(f"{i} × ", end="")
        else:
            print(f"{i}", end="")
    print(f" = {result}")

    # Additional explanation
    print("\n" + "=" * 60)
    print("EXPLANATION:")
    print("=" * 60)
    print(
        f"""
The factorial function works recursively by:
1. Base case: If n ≤ 1, return 1
2. Recursive case: Return n × factorial(n-1)

For factorial(5):
- factorial(5) calls factorial(4)
- factorial(4) calls factorial(3)
- factorial(3) calls factorial(2)
- factorial(2) calls factorial(1)
- factorial(1) returns 1 (base case)

Then the results bubble back up:
- factorial(2) = 2 × 1 = 2
- factorial(3) = 3 × 2 = 6
- factorial(4) = 4 × 6 = 24
- factorial(5) = 5 × 24 = 120

Time Complexity: O(n) - n recursive calls
Space Complexity: O(n) - n frames on the call stack
"""
    )


if __name__ == "__main__":
    main()
