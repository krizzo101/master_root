def bubble_sort(arr):
    """Simple bubble sort algorithm"""
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


# Test with sample list
sample_list = [5, 2, 8, 1, 9]
print(f"Original list: {sample_list}")
sorted_list = bubble_sort(sample_list.copy())
print(f"Sorted list: {sorted_list}")
