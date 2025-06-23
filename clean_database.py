#!/usr/bin/env python3
"""
Database cleanup script to remove invalid records
"""

from app import app, db
from sqlalchemy import text

def clean_database():
    with app.app_context():
        print("Cleaning database...")
        
        # Remove tasks with NULL or invalid IDs
        result = db.session.execute(text("""
            DELETE FROM task WHERE id IS NULL OR id = 0
        """))
        print(f"Removed {result.rowcount} invalid tasks")
        
        # Remove task templates with NULL or invalid IDs
        result = db.session.execute(text("""
            DELETE FROM task_template WHERE id IS NULL OR id = 0
        """))
        print(f"Removed {result.rowcount} invalid task templates")
        
        # Remove rewards with NULL or invalid IDs
        result = db.session.execute(text("""
            DELETE FROM reward WHERE id IS NULL OR id = 0
        """))
        print(f"Removed {result.rowcount} invalid rewards")
        
        # Remove task completions that reference non-existent tasks
        result = db.session.execute(text("""
            DELETE FROM task_completion 
            WHERE task_id NOT IN (SELECT id FROM task)
        """))
        print(f"Removed {result.rowcount} orphaned task completions")
        
        # Remove reward purchases that reference non-existent rewards
        result = db.session.execute(text("""
            DELETE FROM reward_purchase 
            WHERE reward_id NOT IN (SELECT id FROM reward)
        """))
        print(f"Removed {result.rowcount} orphaned reward purchases")
        
        db.session.commit()
        print("Database cleanup completed!")

if __name__ == "__main__":
    clean_database() 