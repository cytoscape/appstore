# Creates the apps_serviceappmetadata table.
#
# Stores extended metadata for Service-type apps: health status, last health
# check timestamp, spec version, and registration validation flag.
#
# Usage:
#   python add_service_app_metadata.py
#
# Update the connection credentials below before running.

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
        CREATE TABLE apps_serviceappmetadata (
            id                    INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            app_id                INT NOT NULL UNIQUE,
            service_url           VARCHAR(200) NOT NULL,
            service_spec_version  VARCHAR(31) NOT NULL DEFAULT '',
            registration_validated TINYINT(1) NOT NULL DEFAULT 0,
            health_status         VARCHAR(10) NOT NULL DEFAULT 'unknown',
            last_health_check     DATETIME NULL,
            CONSTRAINT fk_serviceappmeta_app
                FOREIGN KEY (app_id) REFERENCES apps_app(id)
                ON DELETE CASCADE,
            INDEX apps_serviceappmetadata_health_status_idx (health_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    con.commit()
    print("Migration successful: apps_serviceappmetadata table created.")
except mdb.Error as e:
    print(f"Migration failed: {e}")
    if con:
        con.rollback()
finally:
    if con:
        con.close()
