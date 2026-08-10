import os
try:
    os.remove('testy.py')
    print("Deleted testy.py")
except FileNotFoundError:
    print("File not found")
