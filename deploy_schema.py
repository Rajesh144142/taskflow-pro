#!/usr/bin/env python3
"""
Database schema deployment script for Railway PostgreSQL
Run this script to initialize your database with the required tables
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def deploy_schema():
    """Deploy database schema to Railway PostgreSQL"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable is not set")
        print("Please set your Railway database URL:")
        print("export DATABASE_URL='postgresql://username:password@host:port/database'")
        return False
    
    print("🚀 Deploying database schema to Railway...")
    print(f"✅ Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("✅ Connected successfully!")
        
        # Read and execute the SQL schema
        with open('app/migrations/init_db.sql', 'r') as file:
            sql_script = file.read()
        
        print("📊 Creating database tables...")
        cursor.execute(sql_script)
        
        print("✅ Database schema deployed successfully!")
        print("📊 Tables created:")
        print("   - users")
        print("   - tasks") 
        print("   - meetings")
        print("   - meeting_participants")
        print("   - meeting_reminders")
        print("")
        print("🎉 Your Task Management Dashboard database is ready!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = deploy_schema()
    sys.exit(0 if success else 1)
