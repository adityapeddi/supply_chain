#!/usr/bin/env python3
"""
WSGI entry point for the Retail Inventory Optimization System web application.
This file is used by Gunicorn to serve the application in production.

Author: [Your Name]
Date: March 31, 2025
"""

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
