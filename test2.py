import flet as ft
   import datetime
   import math
   import threading
   import time
   import os
   import sys
   from typing import Dict, Optional

   # Optional imports with graceful fallbacks
   try:
       import requests
   except ImportError: requests = None

   try:
       import psutil
   except ImportError: psutil = None

   # ... rest of the code
