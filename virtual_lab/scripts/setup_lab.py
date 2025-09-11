#!/usr/bin/env python3
"""
Setup script for the virtual lab environment.

This script helps set up the virtual lab environment by:
1. Creating necessary directories
2. Installing dependencies
3. Validating configuration
4. Running initial tests
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_directories():
    """Create necessary directories for the virtual lab."""
    logger.info("Creating virtual lab directories...")
    
    directories = [
        "virtual_lab/logs",
        "virtual_lab/data",
        "virtual_lab/results",
        "virtual_lab/configs/backup"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def install_dependencies():
    """Install required dependencies."""
    logger.info("Installing virtual lab dependencies...")
    
    requirements_file = "virtual_lab/requirements.txt"
    
    if not os.path.exists(requirements_file):
        logger.error(f"Requirements file not found: {requirements_file}")
        return False
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ], check=True)
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def validate_configuration():
    """Validate the lab configuration."""
    logger.info("Validating lab configuration...")
    
    config_file = "virtual_lab/configs/lab_config.yml"
    
    if not os.path.exists(config_file):
        logger.error(f"Configuration file not found: {config_file}")
        return False
    
    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Basic validation
        required_sections = ['lab', 'topology', 'data_generation', 'scaling', 'message_bus']
        for section in required_sections:
            if section not in config:
                logger.error(f"Missing required configuration section: {section}")
                return False
        
        logger.info("Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def run_tests():
    """Run component tests."""
    logger.info("Running component tests...")
    
    test_script = "virtual_lab/scripts/test_components.py"
    
    if not os.path.exists(test_script):
        logger.error(f"Test script not found: {test_script}")
        return False
    
    try:
        result = subprocess.run([sys.executable, test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Component tests passed")
            return True
        else:
            logger.error(f"Component tests failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        return False


def create_sample_config():
    """Create a sample configuration if none exists."""
    config_file = "virtual_lab/configs/lab_config.yml"
    
    if os.path.exists(config_file):
        logger.info("Configuration file already exists")
        return True
    
    logger.info("Creating sample configuration...")
    
    sample_config = """# Virtual Lab Configuration
lab:
  name: "BGP Anomaly Detection Virtual Lab"
  version: "1.0.0"

topology:
  devices:
    spine_switches:
      count: 2
      model: "Cisco Nexus 9000"
      interfaces: 48
    tor_switches:
      count: 4
      model: "Cisco Nexus 3000"
      interfaces: 24
    leaf_switches:
      count: 8
      model: "Cisco Catalyst 9300"
      interfaces: 12

data_generation:
  bgp_telemetry:
    enabled: true
    update_frequency: 1.0
    base_announcements_per_second: 10
    base_withdrawals_per_second: 2
  syslog:
    enabled: true
    base_messages_per_second: 5
    severity_distribution:
      info: 0.6
      warning: 0.25
      error: 0.1
      critical: 0.05

scaling:
  phases:
    - name: "baseline"
      duration_minutes: 5
      bgp_multiplier: 1.0
      syslog_multiplier: 1.0
    - name: "stress_test"
      duration_minutes: 5
      bgp_multiplier: 5.0
      syslog_multiplier: 3.0

message_bus:
  type: "nats"
  servers: ["nats://localhost:4222"]
  subjects:
    bgp_updates: "bgp.updates"
    syslog_messages: "syslog.messages"
    telemetry_data: "telemetry.data"
    processed_features: "features.processed"
    anomaly_alerts: "anomaly.alerts"

preprocessing:
  feature_extraction:
    time_windows: [30, 60, 300]
    features:
      bgp:
        - "announcement_rate"
        - "withdrawal_rate"
        - "as_path_churn"
      syslog:
        - "error_rate"
        - "warning_rate"
        - "message_frequency"
  feature_selection:
    method: "mutual_information"
    max_features: 20
    correlation_threshold: 0.8
"""
    
    try:
        with open(config_file, 'w') as f:
            f.write(sample_config)
        logger.info(f"Created sample configuration: {config_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to create sample configuration: {e}")
        return False


def main():
    """Main setup function."""
    logger.info("Setting up virtual lab environment...")
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    steps = [
        ("Creating directories", create_directories),
        ("Creating sample config", create_sample_config),
        ("Installing dependencies", install_dependencies),
        ("Validating configuration", validate_configuration),
        ("Running tests", run_tests)
    ]
    
    success = True
    for step_name, step_func in steps:
        logger.info(f"Step: {step_name}")
        if not step_func():
            logger.error(f"Step failed: {step_name}")
            success = False
            break
        logger.info(f"Step completed: {step_name}")
    
    if success:
        logger.info("🎉 Virtual lab setup completed successfully!")
        logger.info("You can now run the lab with: python virtual_lab/scripts/start_lab.py")
    else:
        logger.error("❌ Virtual lab setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
