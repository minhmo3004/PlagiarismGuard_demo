#!/usr/bin/env python3
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def fix_db_schema():
    print("🚀 Checking database schema for missing columns...")
    
    # Create engine directly from settings
    engine = create_engine(settings.DATABASE_URL)
    
    # Columns to check and add (Name, SQL Type)
    columns_to_add = [
        ("page_count", "INTEGER"),
        ("error_message", "TEXT"),
        ("topic", "VARCHAR(255)"),
        ("owner_id", "UUID"),
        ("s3_path", "VARCHAR(500)")
    ]
    
    try:
        with engine.connect() as conn:
            # Check for table documents
            res = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'documents');"))
            if not res.scalar():
                print("❌ Table 'documents' does not exist. Please run initial setup first.")
                return
            
            for col_name, col_type in columns_to_add:
                # Check if column exists
                check_sql = text(f"""
                    SELECT count(*) 
                    FROM information_schema.columns 
                    WHERE table_name='documents' AND column_name='{col_name}';
                """)
                exists = conn.execute(check_sql).scalar()
                
                if exists == 0:
                    print(f"➕ Adding missing column: {col_name} ({col_type})")
                    try:
                        # For owner_id we might need foreign key check, but let's just add the column for now
                        alter_sql = text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type};")
                        conn.execute(alter_sql)
                        # Commit for safety (some DB drivers need it)
                        conn.commit()
                        print(f"✅ Column {col_name} added successfully.")
                    except Exception as e:
                        print(f"⚠️  Error adding column {col_name}: {e}")
                else:
                    print(f"ℹ️  Column {col_name} already exists.")
            
            print("\n🎉 Database schema update complete!")
            
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    fix_db_schema()
