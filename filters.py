#!/usr/bin/env python3
"""
Custom Jinja2 filters for the Retail Inventory Optimization System web application.

Author: [Your Name]
Date: March 31, 2025
"""

import markdown as md

def markdown(text):
    """
    Convert markdown text to HTML
    
    Args:
        text: Markdown text to convert
        
    Returns:
        HTML representation of the markdown text
    """
    return md.markdown(text, extensions=['tables', 'fenced_code'])
