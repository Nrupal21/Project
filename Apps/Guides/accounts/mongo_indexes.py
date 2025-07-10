"""
This module contains functions to manage MongoDB indexes for the accounts app.
"""
from django.conf import settings
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.errors import OperationFailure
import logging

logger = logging.getLogger(__name__)

def ensure_mongo_indexes():
    """
    Ensure all required MongoDB indexes are created.
    This function should be called during application startup.
    """
    if not hasattr(settings, 'MONGO_DB'):
        logger.warning("MongoDB database not configured. Skipping index creation.")
        return
    
    db = settings.MONGO_DB
    
    # Define indexes for auth_user collection
    auth_user_indexes = [
        IndexModel([("email", ASCENDING)], name="email_idx", unique=True, background=True),
        IndexModel([("username", ASCENDING)], name="username_idx", unique=True, background=True),
        IndexModel([("role", ASCENDING)], name="role_idx", background=True),
        IndexModel([("is_active", ASCENDING)], name="is_active_idx", background=True),
        IndexModel([("date_joined", DESCENDING)], name="date_joined_idx", background=True),
    ]
    
    # Define indexes for accounts_userprofile collection
    user_profile_indexes = [
        IndexModel([("user", ASCENDING)], name="user_idx", unique=True, background=True),
        IndexModel([("created_at", DESCENDING)], name="created_at_idx", background=True),
    ]
    
    # Define indexes for accounts_userpreferences collection
    user_preferences_indexes = [
        IndexModel([("user", ASCENDING)], name="user_idx", unique=True, background=True),
        IndexModel([("language", ASCENDING)], name="language_idx", background=True),
    ]
    
    try:
        # Create indexes for auth_user
        if 'auth_user' in db.list_collection_names():
            db.auth_user.create_indexes(auth_user_indexes)
            logger.info("Created/verified indexes for auth_user collection")
        
        # Create indexes for accounts_userprofile
        if 'accounts_userprofile' in db.list_collection_names():
            db.accounts_userprofile.create_indexes(user_profile_indexes)
            logger.info("Created/verified indexes for accounts_userprofile collection")
        
        # Create indexes for accounts_userpreferences
        if 'accounts_userpreferences' in db.list_collection_names():
            db.accounts_userpreferences.create_indexes(user_preferences_indexes)
            logger.info("Created/verified indexes for accounts_userpreferences collection")
            
    except OperationFailure as e:
        logger.error(f"Failed to create MongoDB indexes: {e}")
    except Exception as e:
        logger.error(f"Unexpected error creating MongoDB indexes: {e}", exc_info=True)
