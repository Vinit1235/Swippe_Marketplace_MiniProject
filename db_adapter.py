"""
Database Adapter - Automatic PostgreSQL/SQLite Selection
========================================================

This module provides a unified database connection interface that:
- Uses PostgreSQL when DATABASE_URL environment variable is set (Render)
- Falls back to SQLite for local development
- Handles SQL dialect differences automatically

Usage:
    from db_adapter import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    conn.close()
"""

import os
import sqlite3
from contextlib import contextmanager

# Check if we're using PostgreSQL or SQLite
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
        print("✅ Using PostgreSQL database")
    except ImportError:
        print("⚠️  WARNING: DATABASE_URL set but psycopg2 not installed!")
        print("    Install with: pip install psycopg2-binary")
        USE_POSTGRES = False
else:
    print("✅ Using SQLite database (local development)")


def get_db_connection():
    """
    Get a database connection (PostgreSQL or SQLite).
    
    Returns:
        connection object (psycopg2 or sqlite3)
    """
    if USE_POSTGRES:
        # PostgreSQL connection
        conn = psycopg2.connect(DATABASE_URL)
        # Use RealDictCursor for dictionary-like row access
        return conn
    else:
        # SQLite connection
        conn = sqlite3.connect('instance/swippe.db')
        conn.row_factory = sqlite3.Row  # Enable dictionary-like access
        
        # CRITICAL: Enable foreign key constraints (OFF by default in SQLite!)
        conn.execute("PRAGMA foreign_keys = ON")
        
        return conn


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with automatic connection handling.
    
    Args:
        query (str): SQL query to execute
        params (tuple/dict): Query parameters
        fetch_one (bool): Return single row
        fetch_all (bool): Return all rows
        commit (bool): Commit transaction
    
    Returns:
        Result rows, rowcount, or None
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        result = None
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            conn.commit()
            result = cursor.rowcount
        
        return result
    
    except Exception as e:
        conn.rollback()
        print(f"❌ Database error: {e}")
        raise
    
    finally:
        cursor.close()
        conn.close()


@contextmanager
def get_db_cursor():
    """
    Context manager for database operations.
    
    Usage:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM products")
            rows = cursor.fetchall()
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def adapt_sql(sql_query):
    """
    Adapt SQL query for PostgreSQL or SQLite dialect differences.
    
    Args:
        sql_query (str): Original SQL query
    
    Returns:
        str: Adapted SQL query
    """
    if USE_POSTGRES:
        # PostgreSQL uses %s for placeholders instead of ?
        sql_query = sql_query.replace('?', '%s')
        
        # PostgreSQL uses SERIAL instead of AUTOINCREMENT
        sql_query = sql_query.replace('AUTOINCREMENT', 'SERIAL')
        
        # PostgreSQL uses LIMIT x OFFSET y differently
        # (usually handled by the query itself)
    
    return sql_query


def get_database_info():
    """
    Get information about the current database configuration.
    
    Returns:
        dict: Database type, location, and connection status
    """
    info = {
        'type': 'PostgreSQL' if USE_POSTGRES else 'SQLite',
        'url': DATABASE_URL if USE_POSTGRES else 'instance/swippe.db',
        'connected': False
    }
    
    try:
        conn = get_db_connection()
        conn.close()
        info['connected'] = True
    except Exception as e:
        info['error'] = str(e)
    
    return info


if __name__ == '__main__':
    # Test the database connection
    print("\n🔍 Database Adapter Test")
    print("=" * 50)
    
    info = get_database_info()
    print(f"\n📊 Database Type: {info['type']}")
    print(f"📍 Location: {info['url']}")
    print(f"🔌 Connected: {'✅' if info['connected'] else '❌'}")
    
    if info['connected']:
        print("\n✅ Database adapter is working correctly!")
        
        # Test query
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            print(f"📦 Total products in database: {count}")
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not query products table: {e}")
    else:
        print(f"\n❌ Connection failed: {info.get('error', 'Unknown error')}")
