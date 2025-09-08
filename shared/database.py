import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Database configuration
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "smarthome")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        
    def init_engine(self):
        """Initialize SQLAlchemy engine"""
        try:
            self.engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        if not self.SessionLocal:
            self.init_engine()
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

# Global database manager instance
db_manager = DatabaseManager()

def get_connection():
    """Get raw psycopg2 connection for backward compatibility"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=RealDictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch:
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount
        else:
            conn.commit()
            return cursor.lastrowid if hasattr(cursor, 'lastrowid') else None
            
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database query error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_many(query, params_list):
    """Execute query with multiple parameter sets"""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return cursor.rowcount
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database executemany error: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def check_connection():
    """Check if database connection is working"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

# SQLAlchemy base for ORM models
Base = declarative_base()
