def quicksort(arr):
    """
    Sorts an array using the quicksort algorithm.

    Args:
        arr: List of comparable elements to sort

    Returns:
        A new sorted list
    """
    # Base case: arrays with 0 or 1 element are already sorted
    if len(arr) <= 1:
        return arr

    # Choose the middle element as the pivot
    pivot = arr[len(arr) // 2]

    # Partition the array into three parts:
    # - Elements less than the pivot
    left = [x for x in arr if x < pivot]

    # - Elements equal to the pivot (handles duplicates)
    middle = [x for x in arr if x == pivot]

    # - Elements greater than the pivot
    right = [x for x in arr if x > pivot]

    # Recursively sort the left and right partitions, then combine
    return quicksort(left) + middle + quicksort(right)


def quicksort_inplace(arr, low=0, high=None):
    """
    Sorts an array in-place using the quicksort algorithm.
    More memory efficient than the basic version.

    Args:
        arr: List to sort in-place
        low: Starting index of the subarray to sort
        high: Ending index of the subarray to sort
    """
    if high is None:
        high = len(arr) - 1

    # Only sort if there are at least 2 elements
    if low < high:
        # Partition the array and get the pivot index
        pivot_index = partition(arr, low, high)

        # Recursively sort elements before and after partition
        quicksort_inplace(arr, low, pivot_index - 1)
        quicksort_inplace(arr, pivot_index + 1, high)


def partition(arr, low, high):
    """
    Partitions the array around a pivot element.

    Args:
        arr: Array to partition
        low: Starting index
        high: Ending index (pivot position)

    Returns:
        The final position of the pivot element
    """
    # Choose the rightmost element as pivot
    pivot = arr[high]

    # Index of the smaller element - indicates
    # the right position of pivot found so far
    i = low - 1

    # Traverse through the array
    # If current element is smaller than or equal to pivot,
    # swap it with the element at i+1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]

    # Swap the pivot element with the element at i+1
    # This puts the pivot in its correct sorted position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]

    return i + 1


# Example usage
if __name__ == "__main__":
    # Test the basic quicksort
    test_array = [64, 34, 25, 12, 22, 11, 90]
    print("Original array:", test_array)
    sorted_array = quicksort(test_array)
    print("Sorted array (basic):", sorted_array)

    # Test the in-place quicksort
    test_array2 = [64, 34, 25, 12, 22, 11, 90]
    print("\nOriginal array:", test_array2)
    quicksort_inplace(test_array2)
    print("Sorted array (in-place):", test_array2)
