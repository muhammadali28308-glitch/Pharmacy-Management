import json
import os
import html
import webbrowser
from pathlib import Path
from datetime import datetime

# Apne main program se receipt function test karenge
from pharmacy import generate_receipt

generate_receipt(
    "BILL-TEST-0001",
    "Paracetamol",
    2,
    50.00,
    100.00
)