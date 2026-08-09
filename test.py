import os

# Define the file to be deleted
file_to_delete = "review.py"

try:
    if os.path.exists(file_to_delete):
        os.remove(file_to_delete)
        print(f"Successfully deleted '{file_to_delete}'.")
    else:
        print(f"File '{file_to_delete}' not found, nothing to delete.")
except PermissionError:
    print(f"Permission denied: Cannot delete '{file_to_delete}'.")
except Exception as e:
    print(f"An error occurred: {e}")
