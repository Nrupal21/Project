"""
Database setup script for PostgreSQL.

This script helps create and initialize the PostgreSQL database for the Guides application.
It provides an interactive way to set up the database, create tables, and load initial data.
"""
import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info("Loaded environment variables from .env file")
    else:
        logger.warning("No .env file found. Using system environment variables.")

def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'dbname': os.getenv('DB_NAME', 'guides_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
    }

def test_connection(config):
    """Test database connection."""
    try:
        conn = psycopg2.connect(**config)
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist."""
    config = get_db_config()
    db_name = config.pop('dbname')  # Remove dbname to connect to postgres database
    
    try:
        # Connect to the default 'postgres' database
        conn = psycopg2.connect(**{**config, 'dbname': 'postgres'})
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{db_name}'...")
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            logger.info(f"Database '{db_name}' created successfully.")
        else:
            logger.info(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

def run_sql_file(file_path, db_config):
    """Execute SQL commands from a file."""
    try:
        with open(file_path, 'r') as f:
            sql_commands = f.read()
        
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Execute each command separately
        cursor.execute(sql_commands)
        
        logger.info(f"Successfully executed {file_path}")
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error executing SQL file {file_path}: {e}")
        return False

def setup_database():
    """Main function to set up the database."""
    logger.info("Starting database setup...")
    
    # Load environment variables
    load_environment()
    db_config = get_db_config()
    
    # Test database connection
    logger.info("Testing database connection...")
    if not test_connection({**db_config, 'dbname': 'postgres'}):
        logger.error("Could not connect to PostgreSQL server. Please check your settings.")
        return False
    
    # Create database
    if not create_database():
        return False
    
    # Run schema script
    schema_file = os.path.join(os.path.dirname(__file__), 'sql', '01_schema.sql')
    if os.path.exists(schema_file):
        logger.info("Setting up database schema...")
        if not run_sql_file(schema_file, db_config):
            return False
    else:
        logger.error(f"Schema file not found: {schema_file}")
        return False
    
    logger.info("Database setup completed successfully!")
    return True

if __name__ == "__main__":
    if setup_database():
        logger.info("You can now start the Django development server.")
        logger.info("Run: python manage.py runserver")
    else:
        logger.error("Database setup failed. Please check the error messages above.")
        sys.exit(1)
