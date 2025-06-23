#!/usr/bin/env python3
"""
Database migration script for ChoresApp
Adds new features: task templates, always available tasks, and parent approval system
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        # Check if new tables/columns already exist
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        print("Starting database migration...")
        
        # Create TaskTemplate table if it doesn't exist
        if 'task_template' not in existing_tables:
            print("Creating task_template table...")
            with db.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE task_template (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR(100) NOT NULL,
                        description TEXT,
                        points INTEGER DEFAULT 0,
                        difficulty VARCHAR(20) DEFAULT 'easy',
                        created_by INTEGER NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (created_by) REFERENCES user (id)
                    )
                """))
                conn.commit()
            print("✓ task_template table created")
        else:
            print("✓ task_template table already exists")
        
        # Add new columns to Task table
        task_columns = [col['name'] for col in inspector.get_columns('task')]
        
        if 'always_available' not in task_columns:
            print("Adding always_available column to task table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task ADD COLUMN always_available BOOLEAN DEFAULT 0"))
                conn.commit()
            print("✓ always_available column added")
        else:
            print("✓ always_available column already exists")
        
        if 'template_id' not in task_columns:
            print("Adding template_id column to task table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task ADD COLUMN template_id INTEGER"))
                conn.commit()
            print("✓ template_id column added")
        else:
            print("✓ template_id column already exists")
        
        # Add new columns to TaskCompletion table
        completion_columns = [col['name'] for col in inspector.get_columns('task_completion')]
        
        if 'approved_by_parent' not in completion_columns:
            print("Adding approved_by_parent column to task_completion table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task_completion ADD COLUMN approved_by_parent BOOLEAN DEFAULT 0"))
                conn.commit()
            print("✓ approved_by_parent column added")
        else:
            print("✓ approved_by_parent column already exists")
        
        if 'approved_at' not in completion_columns:
            print("Adding approved_at column to task_completion table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task_completion ADD COLUMN approved_at DATETIME"))
                conn.commit()
            print("✓ approved_at column added")
        else:
            print("✓ approved_at column already exists")
        
        if 'approved_by' not in completion_columns:
            print("Adding approved_by column to task_completion table...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE task_completion ADD COLUMN approved_by INTEGER"))
                conn.commit()
            print("✓ approved_by column added")
        else:
            print("✓ approved_by column already exists")
        
        # Update existing completed tasks to be approved (for backward compatibility)
        print("Updating existing completed tasks...")
        with db.engine.connect() as conn:
            conn.execute(text("""
                UPDATE task_completion 
                SET approved_by_parent = 1, approved_at = completed_at 
                WHERE approved_by_parent IS NULL
            """))
            conn.commit()
        print("✓ Existing completed tasks marked as approved")
        
        # Check if auto_available_days column exists
        result = db.session.execute(text("PRAGMA table_info(task)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'auto_available_days' not in columns:
            print("Adding auto_available_days column to task table...")
            db.session.execute(text("ALTER TABLE task ADD COLUMN auto_available_days INTEGER"))
            print("✓ auto_available_days column added")
        
        if 'assigned_children' not in columns:
            print("Adding assigned_children column to task table...")
            db.session.execute(text("ALTER TABLE task ADD COLUMN assigned_children VARCHAR(200)"))
            print("✓ assigned_children column added")
        
        db.session.commit()
        print("Database migration completed successfully!")
        print("New features available:")
        print("- Task templates for reusable task definitions")
        print("- Always available tasks that can be repeated")
        print("- Parent approval system for task completion")

def migrate_remove_created_by():
    with app.app_context():
        # Remove created_by from task_template
        result = db.session.execute(text("""
            PRAGMA table_info(task_template)
        """))
        columns = [row[1] for row in result.fetchall()]
        if 'created_by' in columns:
            print("Dropping created_by from task_template...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS task_template_new AS SELECT id, title, description, points, difficulty, created_at FROM task_template;
            """))
            db.session.execute(text("DROP TABLE task_template;"))
            db.session.execute(text("ALTER TABLE task_template_new RENAME TO task_template;"))

        # Remove created_by from task
        result = db.session.execute(text("""
            PRAGMA table_info(task)
        """))
        columns = [row[1] for row in result.fetchall()]
        if 'created_by' in columns:
            print("Dropping created_by from task...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS task_new AS SELECT id, title, description, points, difficulty, status, assigned_to, created_at, completed_at, due_date, always_available, auto_available_days, assigned_children, template_id FROM task;
            """))
            db.session.execute(text("DROP TABLE task;"))
            db.session.execute(text("ALTER TABLE task_new RENAME TO task;"))

        # Remove created_by from reward
        result = db.session.execute(text("""
            PRAGMA table_info(reward)
        """))
        columns = [row[1] for row in result.fetchall()]
        if 'created_by' in columns:
            print("Dropping created_by from reward...")
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS reward_new AS SELECT id, title, description, points_cost, created_at, is_active, assigned_children FROM reward;
            """))
            db.session.execute(text("DROP TABLE reward;"))
            db.session.execute(text("ALTER TABLE reward_new RENAME TO reward;"))

        db.session.commit()
        print("\nMigration to remove created_by columns completed successfully!")

if __name__ == '__main__':
    migrate_database()
    migrate_remove_created_by() 