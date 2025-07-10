# MongoDB Integration Guide

This document provides information about the MongoDB integration in the Guides application.

## Overview

The application uses MongoDB as its primary database with Djongo as the Django-MongoDB connector. This allows us to leverage MongoDB's document-oriented features while maintaining compatibility with Django's ORM.

## Prerequisites

- Python 3.8+
- MongoDB 4.4+ (MongoDB Atlas recommended for production)
- Djongo
- PyMongo
- dnspython (for MongoDB Atlas SRV connection strings)

## Configuration

### Environment Variables

Set the following environment variables in your `.env` file or deployment environment:

```
# MongoDB connection string (required for MongoDB)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority

# Database name (optional, defaults to 'guides_db')
MONGO_DB_NAME=guides_db

# Set to 'False' in production
DEBUG=True
```

### Django Settings

The database configuration in `settings.py` automatically detects the MongoDB connection and falls back to SQLite if MongoDB is not available.

## Management Commands

### Create Admin User

Create a superuser with admin role:

```bash
python manage.py create_mongo_admin
```

### List Users

List all users with their roles:

```bash
# List all users
python manage.py list_users

# List only active users
python manage.py list_users --active-only

# Filter by role
python manage.py list_users --role admin

# Show password hashes (admin only)
python manage.py list_users --show-passwords
```

### Backup Database

Create a backup of the MongoDB database:

```bash
# Basic backup
python manage.py backup_mongodb

# Compressed backup
python manage.py backup_mongodb --compress

# Specify output directory
python manage.py backup_mongodb --output-dir /path/to/backups
```

### Restore Database

Restore the database from a backup:

```bash
# Restore from a directory (created by mongodump)
python manage.py restore_mongodb /path/to/backup

# Restore from a compressed archive
python manage.py restore_mongodb /path/to/backup.gz

# Drop collections before restoring
python manage.py restore_mongodb /path/to/backup --drop

# Skip confirmation prompt
python manage.py restore_mongodb /path/to/backup --noinput
```

## MongoDB Indexes

Indexes are automatically created when the application starts. The following indexes are created:

### auth_user Collection
- `email` (unique)
- `username` (unique)
- `role`
- `is_active`
- `date_joined` (descending)

### accounts_userprofile Collection
- `user` (unique)
- `created_at` (descending)

### accounts_userpreferences Collection
- `user` (unique)
- `language`

## Models

### CustomUser
- Uses MongoDB's `ObjectId` as primary key
- Email as the username field
- Role-based access control
- Active/inactive status

### UserProfile
- Stores additional user information
- Linked to CustomUser via ObjectId
- Profile picture as URL
- Creation timestamp

### UserPreferences
- Stores user preferences
- Linked to CustomUser via ObjectId
- Includes language and currency preferences

## Best Practices

1. **Backup Regularly**: Use the provided backup command to regularly back up your database.
2. **Use Indexes**: The application automatically creates necessary indexes, but be mindful of adding indexes for your queries.
3. **Monitor Performance**: Use MongoDB Atlas monitoring or similar tools to monitor database performance.
4. **Secure Your Connection**: Always use TLS/SSL for database connections, especially in production.
5. **Handle Large Files Externally**: Store large files (like profile pictures) in object storage (S3, Google Cloud Storage, etc.) and store only the URLs in MongoDB.

## Troubleshooting

### Connection Issues
- Verify your `MONGO_URI` is correct
- Check network connectivity to your MongoDB server
- Ensure your IP is whitelisted in MongoDB Atlas if using Atlas

### Performance Issues
- Check for missing indexes with `db.collection.explain().find({...})`
- Monitor slow queries using MongoDB's profiler
- Consider adding appropriate indexes for frequently queried fields

### Data Migration
For migrating from SQL to MongoDB, use the following approach:
1. Create a backup of your SQL database
2. Use Django's `dumpdata` to export your data
3. Update your models to use MongoDB fields
4. Create a migration script to transform and import the data
5. Test thoroughly before running in production
