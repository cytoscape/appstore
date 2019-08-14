# Converts the Release model object from a many-to-many relationship to a one-to-many relationship.

import MySQLdb as mdb

tbl_prefix = 'apps_'
m2m_tbl = tbl_prefix + 'app_releases'
target_tbl = tbl_prefix  + 'release'

con = None
try:
    con = mdb.connect('localhost', 'root', '', 'CyAppStore')
    cur = con.cursor()
    cur.execute('SELECT * FROM %s' % m2m_tbl)
    for (_, app_id, ss_id) in list(cur.fetchall()):
        cur.execute('UPDATE {0} SET app_id={1} WHERE id={2}'.format(target_tbl, app_id, ss_id))
finally:
    if con:
        con.close()
