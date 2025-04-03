#!/usr/bin/env python3
"""
Production configuration for the Retail Inventory Optimization System web application.
This file configures Gunicorn as the WSGI server for production deployment.

Author: [Your Name]
Date: March 31, 2025
"""

import multiprocessing

# Bind to 0.0.0.0:8000
bind = "0.0.0.0:8000"

# Number of worker processes
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class
worker_class = "sync"

# Timeout in seconds
timeout = 120

# Access log file
accesslog = "access.log"

# Error log file
errorlog = "error.log"

# Log level
loglevel = "info"

# Preload application
preload_app = True

# Daemon mode
daemon = False
