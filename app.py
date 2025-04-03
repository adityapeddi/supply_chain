#!/usr/bin/env python3
"""
Update to the Flask application to include custom filters and production settings.

Author: [Your Name]
Date: March 31, 2025
"""

import os
import sys
import json
import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import threading
import time
import importlib.util
import traceback
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import custom filters
from filters import markdown

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebApp")

# Initialize Flask app
app = Flask(__name__)

# Register custom filters
app.jinja_env.filters['markdown'] = markdown

# Add current datetime to templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Configuration
class Config:
    """Configuration for the web application"""
    
    def __init__(self):
        """Initialize configuration with default values"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, "retail_data.db")
        self.output_dir = os.path.join(self.base_dir, "output")
        self.agent_paths = {
            "data_extraction": os.path.join(self.base_dir, "..", "thesis_implementation", "agents", "data_extraction_agent.py"),
            "eda": os.path.join(self.base_dir, "..", "thesis_implementation", "agents", "exploratory_data_analysis_agent.py"),
            "decision": os.path.join(self.base_dir, "..", "thesis_implementation", "agents", "decision_optimization_agent.py"),
            "mcu": os.path.join(self.base_dir, "..", "thesis_implementation", "mcu.py")
        }
        self.mcu_config_path = os.path.join(self.base_dir, "mcu_config.json")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "analysis_results"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "optimization_results"), exist_ok=True)
        
        # Create MCU config if it doesn't exist
        self._create_mcu_config()
    
    def _create_mcu_config(self):
        """Create MCU configuration file if it doesn't exist"""
        if not os.path.exists(self.mcu_config_path):
            config = {
                "base_dir": self.base_dir,
                "db_path": self.db_path,
                "output_dir": self.output_dir,
                "data_extraction_agent_path": self.agent_paths["data_extraction"],
                "eda_agent_path": self.agent_paths["eda"],
                "decision_agent_path": self.agent_paths["decision"],
                "execution_interval": 3600,
                "parallel_execution": False
            }
            
            with open(self.mcu_config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Created MCU configuration at {self.mcu_config_path}")

# Initialize configuration
config = Config()

# System state
system_state = {
    "initialized": False,
    "running": False,
    "last_execution_time": None,
    "execution_count": 0,
    "data_extraction_completed": False,
    "eda_completed": False,
    "decision_completed": False,
    "error": None
}

# MCU instance
mcu_instance = None

def load_module(module_path, module_name):
    """
    Load a Python module from file path
    
    Args:
        module_path: Path to the module file
        module_name: Name to assign to the module
        
    Returns:
        Loaded module or None if failed
    """
    try:
        if not os.path.exists(module_path):
            logger.error(f"Module file not found: {module_path}")
            return None
        
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module
        
    except Exception as e:
        logger.error(f"Error loading module {module_name} from {module_path}: {str(e)}")
        return None

def initialize_system():
    """
    Initialize the system by loading the MCU and agents
    
    Returns:
        True if successful, False otherwise
    """
    global mcu_instance, system_state
    
    try:
        logger.info("Initializing system")
        
        # Load MCU module
        mcu_module = load_module(config.agent_paths["mcu"], "MasterControlUnit")
        if not mcu_module:
            system_state["error"] = "Failed to load MCU module"
            return False
        
        # Create MCU instance
        mcu_class = getattr(mcu_module, "MasterControlUnit")
        mcu_instance = mcu_class(config_path=config.mcu_config_path)
        
        # Initialize agents
        if not mcu_instance.initialize_agents():
            system_state["error"] = "Failed to initialize agents"
            return False
        
        # Update system state
        system_state["initialized"] = True
        system_state["error"] = None
        
        logger.info("System initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing system: {str(e)}")
        system_state["error"] = str(e)
        return False

def execute_system():
    """
    Execute the system in a separate thread
    
    Returns:
        True if execution started, False otherwise
    """
    global system_state
    
    if not system_state["initialized"]:
        if not initialize_system():
            return False
    
    if system_state["running"]:
        return False
    
    # Create and start execution thread
    execution_thread = threading.Thread(target=_execute_system_thread)
    execution_thread.daemon = True
    execution_thread.start()
    
    return True

def _execute_system_thread():
    """Thread function for system execution"""
    global mcu_instance, system_state
    
    try:
        logger.info("Starting system execution")
        
        # Update system state
        system_state["running"] = True
        system_state["error"] = None
        
        # Execute system
        results = mcu_instance.execute()
        
        # Check for errors
        if "error" in results:
            logger.error(f"System execution failed: {results['error']}")
            system_state["error"] = results["error"]
        else:
            logger.info("System execution completed successfully")
            
            # Update system state
            system_state["last_execution_time"] = datetime.now()
            system_state["execution_count"] += 1
            system_state["data_extraction_completed"] = mcu_instance.execution_state["data_extraction_completed"]
            system_state["eda_completed"] = mcu_instance.execution_state["eda_completed"]
            system_state["decision_completed"] = mcu_instance.execution_state["decision_completed"]
        
    except Exception as e:
        logger.error(f"Error in system execution thread: {str(e)}")
        system_state["error"] = str(e)
    
    finally:
        # Update system state
        system_state["running"] = False

def get_database_tables():
    """
    Get list of tables in the database
    
    Returns:
        List of table names
    """
    try:
        if not os.path.exists(config.db_path):
            return []
        
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        
        # Query for table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return tables
        
    except Exception as e:
        logger.error(f"Error getting database tables: {str(e)}")
        return []

def get_table_data(table_name, limit=100):
    """
    Get data from a database table
    
    Args:
        table_name: Name of the table
        limit: Maximum number of rows to return
        
    Returns:
        DataFrame containing table data
    """
    try:
        if not os.path.exists(config.db_path):
            return pd.DataFrame()
        
        conn = sqlite3.connect(config.db_path)
        
        # Query for table data
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Error getting data from table {table_name}: {str(e)}")
        return pd.DataFrame()

def get_report_files():
    """
    Get list of report files
    
    Returns:
        Dictionary mapping report types to file paths
    """
    try:
        reports = {}
        
        # Check for system summary report
        system_report_path = os.path.join(config.output_dir, "system_summary_report.md")
        if os.path.exists(system_report_path):
            reports["system"] = system_report_path
        
        # Check for EDA report
        eda_report_path = os.path.join(config.output_dir, "analysis_results", "eda_summary_report.md")
        if os.path.exists(eda_report_path):
            reports["eda"] = eda_report_path
        
        # Check for decision optimization report
        decision_report_path = os.path.join(config.output_dir, "optimization_results", "decision_optimization_report.md")
        if os.path.exists(decision_report_path):
            reports["decision"] = decision_report_path
        
        return reports
        
    except Exception as e:
        logger.error(f"Error getting report files: {str(e)}")
        return {}

def get_visualization_files():
    """
    Get list of visualization files
    
    Returns:
        Dictionary mapping visualization types to file paths
    """
    try:
        visualizations = {}
        
        # Check for EDA visualizations
        eda_viz_dir = os.path.join(config.output_dir, "analysis_results")
        if os.path.exists(eda_viz_dir):
            eda_viz_files = [f for f in os.listdir(eda_viz_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            visualizations["eda"] = [os.path.join(eda_viz_dir, f) for f in eda_viz_files]
        
        # Check for decision optimization visualizations
        decision_viz_dir = os.path.join(config.output_dir, "optimization_results")
        if os.path.exists(decision_viz_dir):
            decision_viz_files = [f for f in os.listdir(decision_viz_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
            visualizations["decision"] = [os.path.join(decision_viz_dir, f) for f in decision_viz_files]
        
        return visualizations
        
    except Exception as e:
        logger.error(f"Error getting visualization files: {str(e)}")
        return {}

def read_markdown_file(file_path):
    """
    Read a markdown file
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        String containing file contents
    """
    try:
        if not os.path.exists(file_path):
            return ""
        
        with open(file_path, "r") as f:
            content = f.read()
        
        return content
        
    except Exception as e:
        logger.error(f"Error reading markdown file {file_path}: {str(e)}")
        return ""

def generate_sample_data():
    """
    Generate sample data for demonstration purposes
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create database connection
        conn = sqlite3.connect(config.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales_data (
            id INTEGER PRIMARY KEY,
            date TEXT,
            product_id TEXT,
            category TEXT,
            sales REAL,
            quantity INTEGER,
            store_id TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS supplier_data (
            id INTEGER PRIMARY KEY,
            supplier_id TEXT,
            product_id TEXT,
            lead_time_days INTEGER,
            cost_per_unit REAL,
            reliability_score REAL
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS shipping_data (
            id INTEGER PRIMARY KEY,
            shipping_id TEXT,
            origin TEXT,
            destination TEXT,
            transit_time_days INTEGER,
            cost REAL,
            carrier TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_data (
            id INTEGER PRIMARY KEY,
            date TEXT,
            indicator TEXT,
            value REAL,
            region TEXT
        )
        ''')
        
        # Insert sample data
        # Sales data
        sales_data = [
            ('2025-01-01', 'P001', 'electronics', 1200.50, 5, 'S001'),
            ('2025-01-01', 'P002', 'clothing', 450.75, 9, 'S001'),
            ('2025-01-01', 'P003', 'groceries', 125.30, 25, 'S001'),
            ('2025-01-02', 'P001', 'electronics', 980.25, 4, 'S001'),
            ('2025-01-02', 'P002', 'clothing', 520.80, 10, 'S001'),
            ('2025-01-02', 'P003', 'groceries', 145.60, 30, 'S001'),
            ('2025-01-03', 'P001', 'electronics', 1500.00, 6, 'S001'),
            ('2025-01-03', 'P002', 'clothing', 380.40, 8, 'S001'),
            ('2025-01-03', 'P003', 'groceries', 110.25, 22, 'S001'),
            ('2025-01-01', 'P001', 'electronics', 950.75, 4, 'S002'),
            ('2025-01-01', 'P002', 'clothing', 620.30, 12, 'S002'),
            ('2025-01-01', 'P003', 'groceries', 180.90, 35, 'S002'),
            ('2025-01-02', 'P001', 'electronics', 1100.00, 5, 'S002'),
            ('2025-01-02', 'P002', 'clothing', 490.50, 10, 'S002'),
            ('2025-01-02', 'P003', 'groceries', 160.25, 32, 'S002'),
            ('2025-01-03', 'P001', 'electronics', 1300.80, 6, 'S002'),
            ('2025-01-03', 'P002', 'clothing', 550.90, 11, 'S002'),
            ('2025-01-03', 'P003', 'groceries', 140.60, 28, 'S002')
        ]
        
        cursor.executemany('''
        INSERT INTO sales_data (date, product_id, category, sales, quantity, store_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', sales_data)
        
        # Supplier data
        supplier_data = [
            ('SUP001', 'P001', 5, 200.00, 0.95),
            ('SUP001', 'P002', 3, 40.00, 0.92),
            ('SUP002', 'P001', 7, 190.00, 0.98),
            ('SUP002', 'P003', 2, 4.50, 0.90),
            ('SUP003', 'P002', 4, 42.00, 0.94),
            ('SUP003', 'P003', 3, 4.00, 0.96)
        ]
        
        cursor.executemany('''
        INSERT INTO supplier_data (supplier_id, product_id, lead_time_days, cost_per_unit, reliability_score)
        VALUES (?, ?, ?, ?, ?)
        ''', supplier_data)
        
        # Shipping data
        shipping_data = [
            ('SH001', 'Warehouse A', 'Store S001', 2, 150.00, 'Carrier X'),
            ('SH002', 'Warehouse A', 'Store S002', 3, 180.00, 'Carrier X'),
            ('SH003', 'Warehouse B', 'Store S001', 1, 120.00, 'Carrier Y'),
            ('SH004', 'Warehouse B', 'Store S002', 2, 140.00, 'Carrier Y'),
            ('SH005', 'Supplier SUP001', 'Warehouse A', 4, 250.00, 'Carrier Z'),
            ('SH006', 'Supplier SUP002', 'Warehouse A', 5, 280.00, 'Carrier Z'),
            ('SH007', 'Supplier SUP003', 'Warehouse B', 3, 220.00, 'Carrier X')
        ]
        
        cursor.executemany(''
(Content truncated due to size limit. Use line ranges to read in chunks)