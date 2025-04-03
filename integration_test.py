#!/usr/bin/env python3
"""
Integration Test Script for Multi-Agent Retail Inventory Optimization System

This script tests the integration of all components:
1. Data Extraction Agent
2. Exploratory Data Analysis Agent
3. Decision Optimization Agent
4. Master Control Unit (MCU)

Author: [Your Name]
Date: March 31, 2025
"""

import os
import sys
import json
import time
import logging
import argparse
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import traceback
import importlib.util

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integration_test.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("IntegrationTest")

class IntegrationTest:
    """Integration test for the multi-agent system"""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the integration test
        
        Args:
            base_dir: Base directory for the system
        """
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, "retail_data.db")
        self.output_dir = os.path.join(self.base_dir, "test_output")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set up paths to agent modules
        self.agent_paths = {
            "data_extraction": os.path.join(self.base_dir, "agents", "data_extraction_agent.py"),
            "eda": os.path.join(self.base_dir, "agents", "exploratory_data_analysis_agent.py"),
            "decision": os.path.join(self.base_dir, "agents", "decision_optimization_agent.py"),
            "mcu": os.path.join(self.base_dir, "mcu.py")
        }
        
        # Initialize test results
        self.test_results = {
            "data_extraction": {"status": "not_tested", "details": {}},
            "eda": {"status": "not_tested", "details": {}},
            "decision": {"status": "not_tested", "details": {}},
            "mcu": {"status": "not_tested", "details": {}},
            "integration": {"status": "not_tested", "details": {}}
        }
        
        logger.info("Integration test initialized")
    
    def _load_module(self, module_path: str, module_name: str):
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
    
    def _create_test_database(self):
        """
        Create a test database with sample data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create or connect to database
            conn = sqlite3.connect(self.db_path)
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
            
            cursor.executemany('''
            INSERT INTO shipping_data (shipping_id, origin, destination, transit_time_days, cost, carrier)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', shipping_data)
            
            # Economic data
            economic_data = [
                ('2025-01-01', 'inflation_rate', 2.1, 'US'),
                ('2025-01-01', 'consumer_confidence', 98.5, 'US'),
                ('2025-01-01', 'unemployment_rate', 3.8, 'US'),
                ('2025-01-02', 'inflation_rate', 2.2, 'US'),
                ('2025-01-02', 'consumer_confidence', 97.8, 'US'),
                ('2025-01-02', 'unemployment_rate', 3.7, 'US'),
                ('2025-01-03', 'inflation_rate', 2.1, 'US'),
                ('2025-01-03', 'consumer_confidence', 98.2, 'US'),
                ('2025-01-03', 'unemployment_rate', 3.8, 'US')
            ]
            
            cursor.executemany('''
            INSERT INTO economic_data (date, indicator, value, region)
            VALUES (?, ?, ?, ?)
            ''', economic_data)
            
            # Commit changes and close connection
            conn.commit()
            conn.close()
            
            logger.info(f"Created test database at {self.db_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating test database: {str(e)}")
            return False
    
    def test_data_extraction_agent(self):
        """
        Test the Data Extraction Agent
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            logger.info("Testing Data Extraction Agent")
            
            # Load the agent module
            module = self._load_module(self.agent_paths["data_extraction"], "DataExtractionAgent")
            if not module:
                self.test_results["data_extraction"] = {
                    "status": "failed",
                    "details": {"error": "Failed to load module"}
                }
                return False
            
            # Check if the agent class exists
            if not hasattr(module, "DataExtractionAgent"):
                self.test_results["data_extraction"] = {
                    "status": "failed",
                    "details": {"error": "DataExtractionAgent class not found in module"}
                }
                return False
            
            # Create an instance of the agent
            agent_class = getattr(module, "DataExtractionAgent")
            agent = agent_class()
            
            # Test basic functionality
            # For this test, we'll just check if the agent has the required methods
            required_methods = [
                "extract_stock_data",
                "extract_sales_data",
                "extract_shipping_data",
                "extract_supplier_data",
                "extract_economic_data",
                "extract_all_data",
                "get_data_for_analysis"
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(agent, method) or not callable(getattr(agent, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                self.test_results["data_extraction"] = {
                    "status": "failed",
                    "details": {"error": f"Missing required methods: {', '.join(missing_methods)}"}
                }
                return False
            
            # Test successful
            self.test_results["data_extraction"] = {
                "status": "passed",
                "details": {"methods_checked": required_methods}
            }
            
            logger.info("Data Extraction Agent test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing Data Extraction Agent: {str(e)}")
            self.test_results["data_extraction"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_eda_agent(self):
        """
        Test the Exploratory Data Analysis Agent
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            logger.info("Testing EDA Agent")
            
            # Load the agent module
            module = self._load_module(self.agent_paths["eda"], "EDAAgent")
            if not module:
                self.test_results["eda"] = {
                    "status": "failed",
                    "details": {"error": "Failed to load module"}
                }
                return False
            
            # Check if the agent class exists
            if not hasattr(module, "EDAAgent"):
                self.test_results["eda"] = {
                    "status": "failed",
                    "details": {"error": "EDAAgent class not found in module"}
                }
                return False
            
            # Create an instance of the agent
            agent_class = getattr(module, "EDAAgent")
            agent = agent_class(db_path=self.db_path, output_dir=os.path.join(self.output_dir, "analysis_results"))
            
            # Test basic functionality
            # For this test, we'll just check if the agent has the required methods
            required_methods = [
                "load_data",
                "analyze_sales_trends",
                "analyze_stock_performance",
                "analyze_supplier_performance",
                "analyze_shipping_efficiency",
                "analyze_economic_impact",
                "generate_visualizations",
                "run_analysis",
                "get_recommendations",
                "get_summary_report_path"
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(agent, method) or not callable(getattr(agent, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                self.test_results["eda"] = {
                    "status": "failed",
                    "details": {"error": f"Missing required methods: {', '.join(missing_methods)}"}
                }
                return False
            
            # Test successful
            self.test_results["eda"] = {
                "status": "passed",
                "details": {"methods_checked": required_methods}
            }
            
            logger.info("EDA Agent test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing EDA Agent: {str(e)}")
            self.test_results["eda"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_decision_agent(self):
        """
        Test the Decision Optimization Agent
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            logger.info("Testing Decision Optimization Agent")
            
            # Load the agent module
            module = self._load_module(self.agent_paths["decision"], "DecisionOptimizationAgent")
            if not module:
                self.test_results["decision"] = {
                    "status": "failed",
                    "details": {"error": "Failed to load module"}
                }
                return False
            
            # Check if the agent class exists
            if not hasattr(module, "DecisionOptimizationAgent"):
                self.test_results["decision"] = {
                    "status": "failed",
                    "details": {"error": "DecisionOptimizationAgent class not found in module"}
                }
                return False
            
            # Create an instance of the agent
            agent_class = getattr(module, "DecisionOptimizationAgent")
            agent = agent_class(db_path=self.db_path, output_dir=os.path.join(self.output_dir, "optimization_results"))
            
            # Test basic functionality
            # For this test, we'll just check if the agent has the required methods
            required_methods = [
                "load_data",
                "prepare_product_data",
                "optimize_inventory_policies",
                "generate_decision_recommendations"
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(agent, method) or not callable(getattr(agent, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                self.test_results["decision"] = {
                    "status": "failed",
                    "details": {"error": f"Missing required methods: {', '.join(missing_methods)}"}
                }
                return False
            
            # Test successful
            self.test_results["decision"] = {
                "status": "passed",
                "details": {"methods_checked": required_methods}
            }
            
            logger.info("Decision Optimization Agent test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing Decision Optimization Agent: {str(e)}")
            self.test_results["decision"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_mcu(self):
        """
        Test the Master Control Unit
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            logger.info("Testing Master Control Unit")
            
            # Load the MCU module
            module = self._load_module(self.agent_paths["mcu"], "MasterControlUnit")
            if not module:
                self.test_results["mcu"] = {
                    "status": "failed",
                    "details": {"error": "Failed to load module"}
                }
                return False
            
            # Check if the MCU class exists
            if not hasattr(module, "MasterControlUnit"):
                self.test_results["mcu"] = {
                    "status": "failed",
                    "details": {"error": "MasterControlUnit class not found in module"}
                }
                return False
            
            # Create an instance of the MCU
            mcu_class = getattr(module, "MasterControlUnit")
            
            # Create a test configuration
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
            
            # Save config to file
            config_path = os.path.join(self.output_dir, "test_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            # Initialize MCU with config
            mcu = mcu_class(config_path=config_path)
            
            # Test basic functionality
            # For this test, we'll just check if the MCU has the required methods
            required_methods = [
                "initialize_agents",
                "execute_sequential",
                "execute_parallel",
                "execute",
                "generate_summary_report",
                "get_system_status"
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(mcu, method) or not callable(getattr(mcu, method)):
                    missing_methods.append(method)
            
            if missing_methods:
                self.test_results["mcu"] = {
                    "status": "failed",
                    "details": {"error": f"Missing required methods: {', '.join(missing_methods)}"}
                }
                return False
            
            # Test successful
            self.test_results["mcu"] = {
                "status": "passed",
                "details": {"methods_checked": required_methods}
            }
            
            logger.info("Master Control Unit test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error testing Master Control Unit: {str(e)}")
            self.test_results["mcu"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def test_integration(self):
        """
        Test the integration of all components
        
        Returns:
            True if test passed, False otherwise
        """
        try:
            logger.info("Testing integration of all components")
            
            # Create test database
            if not self._create_test_database():
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": "Failed to create test database"}
                }
                return False
            
            # Load the MCU module
            module = self._load_module(self.agent_paths["mcu"], "MasterControlUnit")
            if not module:
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": "Failed to load MCU module"}
                }
                return False
            
            # Create an instance of the MCU
            mcu_class = getattr(module, "MasterControlUnit")
            
            # Create a test configuration
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
            
            # Save config to file
            config_path = os.path.join(self.output_dir, "test_config.json")
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            # Initialize MCU with config
            mcu = mcu_class(config_path=config_path)
            
            # Initialize agents
            if not mcu.initialize_agents():
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": "Failed to initialize agents"}
                }
                return False
            
            # Execute the system
            results = mcu.execute()
            
            if "error" in results:
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": f"Execution failed: {results['error']}"}
                }
                return False
            
            # Generate summary report
            report_path = mcu.generate_summary_report()
            
            if not report_path or not os.path.exists(report_path):
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": "Failed to generate summary report"}
                }
                return False
            
            # Check system status
            status = mcu.get_system_status()
            
            if "error" in status:
                self.test_results["integration"] = {
                    "status": "failed",
                    "details": {"error": f"Failed to get system status: {status['error']}"}
                }
                return False
            
            # Test successful
            self.test_results["integration"] = {
                "status": "passed",
                "details": {
                    "execution_state": mcu.execution_state,
                    "report_path": report_path,
                    "system_status": status
                }
            }
            
            logger.info("Integration test passed")
            return True
            
        except Exception as e:
            logger.error(f"Error in integration test: {str(e)}")
            self.test_results["integration"] = {
                "status": "failed",
                "details": {"error": str(e)}
            }
            return False
    
    def run_all_tests(self):
        """
        Run all tests
        
        Returns:
            Dictionary containing test results
        """
        try:
            logger.info("Running all tests")
            
            # Test individual components
            self.test_data_extraction_agent()
            self.test_eda_agent()
            self.test_decision_agent()
            self.test_mcu()
            
            # Test integration
            self.test_integration()
            
            # Save test results
            results_path = os.path.join(self.output_dir, "test_results.json")
            with open(results_path, "w") as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"All tests completed. Results saved to {results_path}")
            
            return self.test_results
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            return {"error": str(e)}
    
    def generate_test_report(self):
        """
        Generate a test report
        
        Returns:
            Path to the generated report
        """
        try:
            report = []
            
            report.append("# Multi-Agent Retail Inventory Optimization System Test Report")
            report.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Overall status
            all_passed = all(result["status"] == "passed" for result in self.test_results.values())
            overall_status = "PASSED" if all_passed else "FAILED"
            
            report.append(f"## Overall Status: {overall_status}\n")
            
            # Component status
            report.append("## Component Test Results")
            
            for component, result in self.test_results.items():
                status = result["status"].upper()
                status_emoji = "✅" if status == "PASSED" else "❌"
                
                report.append(f"### {component.replace('_', ' ').title()} - {status_emoji} {status}")
                
                if status == "FAILED":
                    error = result["details"].get("error", "Unknown error")
                    report.append(f"**Error:** {error}")
                
                if "methods_checked" in result["details"]:
                    methods = result["details"]["methods_checked"]
                    report.append("\n**Methods Checked:**")
                    for method in methods:
                        report.append(f"- `{method}`")
                
                report.append("")
            
            # Integration test details
            if self.test_results["integration"]["status"] == "passed":
                report.append("## Integration Test Details")
                
                details = self.test_results["integration"]["details"]
                
                if "execution_state" in details:
                    exec_state = details["execution_state"]
                    report.append("\n**Execution State:**")
                    report.append(f"- Data Extraction Completed: {exec_state.get('data_extraction_completed', False)}")
                    report.append(f"- EDA Completed: {exec_state.get('eda_completed', False)}")
                    report.append(f"- Decision Optimization Completed: {exec_state.get('decision_completed', False)}")
                    report.append(f"- Execution Count: {exec_state.get('execution_count', 0)}")
                
                if "report_path" in details:
                    report_path = details["report_path"]
                    report.append(f"\n**System Report:** [{os.path.basename(report_path)}]({report_path})")
                
                report.append("")
            
            # Recommendations
            report.append("## Recommendations")
            
            if all_passed:
                report.append("The system has passed all tests and is ready for deployment. Consider the following next steps:")
                report.append("1. Deploy the system in a production environment")
                report.append("2. Set up scheduled execution")
                report.append("3. Implement monitoring and alerting")
                report.append("4. Develop a user interface for interacting with the system")
            else:
                report.append("The system has failed one or more tests. Consider the following next steps:")
                
                failed_components = [comp for comp, result in self.test_results.items() if result["status"] == "failed"]
                
                for component in failed_components:
                    error = self.test_results[component]["details"].get("error", "Unknown error")
                    report.append(f"1. Fix issues with {component.replace('_', ' ').title()}: {error}")
                
                report.append("2. Run tests again after fixing the issues")
            
            # Write report to file
            report_path = os.path.join(self.output_dir, "test_report.md")
            with open(report_path, "w") as f:
                f.write("\n".join(report))
            
            logger.info(f"Generated test report at {report_path}")
            
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating test report: {str(e)}")
            return ""


def main():
    """Main function to run the integration test"""
    parser = argparse.ArgumentParser(description="Integration Test for Multi-Agent Retail Inventory Optimization System")
    parser.add_argument("--base-dir", help="Base directory for the system")
    args = parser.parse_args()
    
    try:
        # Initialize and run tests
        test = IntegrationTest(base_dir=args.base_dir)
        test.run_all_tests()
        
        # Generate test report
        report_path = test.generate_test_report()
        
        # Print summary
        all_passed = all(result["status"] == "passed" for result in test.test_results.values())
        overall_status = "PASSED" if all_passed else "FAILED"
        
        print("\n" + "=" * 50)
        print(f"Integration Test: {overall_status}")
        print("=" * 50)
        
        for component, result in test.test_results.items():
            status = result["status"].upper()
            status_symbol = "✓" if status == "PASSED" else "✗"
            print(f"{status_symbol} {component.replace('_', ' ').title()}: {status}")
        
        print("\nTest Report:", report_path)
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
