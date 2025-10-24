#!/usr/bin/env python3
"""
SmartBed Dashboard Startup Script
This script starts the Flask application with proper configuration.
"""

import os
import sys
from app import app

def main():
    """Main function to start the application."""
    print("🚀 Starting SmartBed Dashboard...")
    
    # Check if MongoDB URI is set
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/smart_bed_db')
    print(f"📊 MongoDB URI: {mongodb_uri}")
    
    # Check if Flask environment is set
    flask_env = os.getenv('FLASK_ENV', 'development')
    flask_debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"🌐 Flask Environment: {flask_env}")
    print(f"🐛 Debug Mode: {flask_debug}")
    print("📡 MQTT Broker: broker.hivemq.com:1883")
    print("🔄 Starting Flask server...")
    print("=" * 50)
    
    # Start the Flask application
    app.run(
        debug=flask_debug,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )

if __name__ == '__main__':
    main()
