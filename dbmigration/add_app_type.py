# Adds app_type column to apps_app table.
#
# app_type replaces the insufficient is_service boolean and supports three
# platform states: 'desktop' (default), 'web', and 'service'.
#
# Existing rows are defaulted to 'desktop' to preserve backward compatibility.
#
# Usage:
#   python add_app_type.py
#
# Make sure to update the connection credentials below before running.

import MySQLdb as mdb

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = ''
DB_NAME = 'CyAppStore'

con = None
try:
    con = mdb.connect(DB_HOST, DB_USER, DB_PASS, DB_NAME)
    cur = con.cursor()

    cur.execute("""
        ALTER TABLE apps_app
        ADD COLUMN app_type VARCHAR(10) NOT NULL DEFAULT 'desktop'
        AFTER active
    """)

    cur.execute("""
        ALTER TABLE apps_app
        ADD INDEX apps_app_app_type_idx (app_type)
    """)

    con.commit()
    print("Migration successful: app_type column added to apps_app.")
except mdb.Error as e:
    print(f"Migration failed: {e}")
    if con:
        con.rollback()
finally:
    if con:
        con.close()
