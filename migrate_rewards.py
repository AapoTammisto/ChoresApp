#!/usr/bin/env python3
"""
Database migration script to add reward tables and approval fields
"""

from app import app, db
from sqlalchemy import text

def migrate_rewards():
    with app.app_context():
        # Check if reward table already exists
        result = db.session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reward'
        """))
        
        if result.fetchone() is None:
            print("Creating reward table...")
            db.session.execute(text("""
                CREATE TABLE reward (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(100) NOT NULL,
                    description TEXT,
                    points_cost INTEGER NOT NULL,
                    created_by INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    assigned_children VARCHAR(200)
                )
            """))
            print("✓ Reward table created")
        else:
            # Check if assigned_children column exists
            result = db.session.execute(text("""
                PRAGMA table_info(reward)
            """))
            columns = [row[1] for row in result.fetchall()]
            
            if 'assigned_children' not in columns:
                print("Adding assigned_children column to reward table...")
                db.session.execute(text("""
                    ALTER TABLE reward 
                    ADD COLUMN assigned_children VARCHAR(200)
                """))
        
        # Check if reward_purchase table already exists
        result = db.session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='reward_purchase'
        """))
        
        if result.fetchone() is None:
            print("Creating reward_purchase table...")
            db.session.execute(text("""
                CREATE TABLE reward_purchase (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reward_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    points_spent INTEGER NOT NULL,
                    purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved_by_parent BOOLEAN DEFAULT 0,
                    approved_at DATETIME,
                    approved_by INTEGER
                )
            """))
            print("✓ Reward purchase table created")
        else:
            # Check if approval fields exist
            result = db.session.execute(text("""
                PRAGMA table_info(reward_purchase)
            """))
            columns = [row[1] for row in result.fetchall()]
            
            if 'approved_by_parent' not in columns:
                print("Adding approved_by_parent column...")
                db.session.execute(text("""
                    ALTER TABLE reward_purchase 
                    ADD COLUMN approved_by_parent BOOLEAN DEFAULT 0
                """))
            
            if 'approved_at' not in columns:
                print("Adding approved_at column...")
                db.session.execute(text("""
                    ALTER TABLE reward_purchase 
                    ADD COLUMN approved_at DATETIME
                """))
            
            if 'approved_by' not in columns:
                print("Adding approved_by column...")
                db.session.execute(text("""
                    ALTER TABLE reward_purchase 
                    ADD COLUMN approved_by INTEGER
                """))
        
        db.session.commit()
        print("\nMigration completed successfully!")

if __name__ == '__main__':
    migrate_rewards() 