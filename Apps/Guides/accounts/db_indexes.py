"""
This module contains functions to manage PostgreSQL indexes for the accounts app.

PostgreSQL uses Django's migration system to create indexes defined in models.
This utility file provides additional index management capabilities if needed.
"""
from django.db import connection
from django.conf import settings
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

def ensure_db_indexes():
    """
    Verify that all required PostgreSQL indexes are created.
    
    This function checks if critical indexes exist on the database and
    logs warnings if any expected indexes are missing. It doesn't create
    indexes directly (Django's migrations handle this) but can be used
    for monitoring and verification purposes.
    
    Args:
        None
    
    Returns:
        bool: True if all indexes are present, False otherwise
    """
    try:
        # Get a database cursor
        with connection.cursor() as cursor:
            # Get list of all existing indexes in the accounts app tables
            cursor.execute("""
                SELECT 
                    tablename, 
                    indexname 
                FROM 
                    pg_indexes 
                WHERE 
                    schemaname = 'public' AND 
                    (tablename LIKE 'accounts_%' OR tablename LIKE 'auth_%')
            """)
            
            existing_indexes = cursor.fetchall()
            existing_index_names = [idx[1] for idx in existing_indexes]
            
            # Define expected indexes based on model definitions
            expected_indexes = [
                # User model indexes
                'accounts_customuser_email_idx',
                'accounts_customuser_username_idx',
                'accounts_customuser_role_idx', 
                'accounts_customuser_is_active_idx',
                'accounts_customuser_date_joined_idx',
                
                # UserProfile model indexes
                'accounts_userprofile_user_id_idx',
                'accounts_userprofile_created_at_idx',
                
                # UserPreferences model indexes
                'accounts_userpreferences_user_id_idx',
                'accounts_userpreferences_language_idx',
            ]
            
            # Check if any expected indexes are missing
            missing_indexes = [idx for idx in expected_indexes if idx not in existing_index_names]
            
            if missing_indexes:
                for idx in missing_indexes:
                    logger.warning(f"Missing expected index: {idx}")
                logger.info("Run 'python manage.py makemigrations' followed by 'python manage.py migrate' to create missing indexes")
                return False
            else:
                logger.info("All expected database indexes exist")
                return True
                
    except Exception as e:
        logger.error(f"Error checking database indexes: {e}", exc_info=True)
        return False

def get_table_stats():
    """
    Get statistics about database tables in the accounts app.
    
    This function retrieves information about table sizes and row counts
    which can be useful for monitoring and optimization purposes.
    
    Args:
        None
        
    Returns:
        dict: Dictionary containing table statistics with table names as keys
    """
    stats = {}
    
    try:
        with connection.cursor() as cursor:
            # Get table row counts
            cursor.execute("""
                SELECT 
                    relname AS table_name,
                    n_live_tup AS row_count
                FROM 
                    pg_stat_user_tables
                WHERE 
                    relname LIKE 'accounts_%' OR relname LIKE 'auth_%'
                ORDER BY 
                    n_live_tup DESC
            """)
            
            tables = cursor.fetchall()
            
            for table in tables:
                table_name, row_count = table
                stats[table_name] = {
                    'row_count': row_count,
                }
                
                # Get table and index sizes
                cursor.execute(f"""
                    SELECT
                        pg_size_pretty(pg_total_relation_size('{table_name}')) AS total_size,
                        pg_size_pretty(pg_relation_size('{table_name}')) AS table_size,
                        pg_size_pretty(pg_indexes_size('{table_name}')) AS index_size
                """)
                
                size_info = cursor.fetchone()
                if size_info:
                    stats[table_name].update({
                        'total_size': size_info[0],
                        'table_size': size_info[1],
                        'index_size': size_info[2],
                    })
            
            return stats
            
    except Exception as e:
        logger.error(f"Error getting table statistics: {e}", exc_info=True)
        return {}
