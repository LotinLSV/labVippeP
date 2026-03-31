import sqlite3

def run_migration():
    conn = sqlite3.connect(r"c:\Users\lucas\OneDrive\Documentos\VIPPE\data\vippe.db")
    cursor = conn.cursor()
    
    # Tables and Columns to ensure
    migrations = [
        ("projects", "out_of_scope", "TEXT"),
        ("projects", "justification", "TEXT"),
        ("projects", "objectives", "TEXT"),
        ("projects", "requirements", "TEXT"),
        ("projects", "assumptions", "TEXT"),
        ("projects", "restrictions", "TEXT"),
        ("projects", "risks", "TEXT"),
        ("projects", "baseline_start_date", "DATETIME"),
        ("projects", "baseline_end_date", "DATETIME"),
        ("users", "typebot_link", "TEXT"),
        ("users", "minion_link", "TEXT"),
        ("users", "lovable_link", "TEXT"),
        ("users", "open_claw_link", "TEXT"),
        ("users", "quickcharts_link", "TEXT"),
        ("users", "dify_link", "TEXT"),
        ("users", "chatwoot_link", "TEXT"),
        ("users", "show_projects", "BOOLEAN DEFAULT 0"),
        ("chat_messages", "project_id", "INTEGER")
    ]
    
    for table, col_name, col_type in migrations:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to {table}")
        except sqlite3.OperationalError:
            # Column likely already exists
            print(f"Skipping {table}.{col_name}: Already exists")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
