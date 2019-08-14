# Converts the ipaddr text field to a numerical quantity stored in ip4addr.

import MySQLdb as mdb

tbl_prefix = 'apps_'
m2m_tbl = tbl_prefix + 'app_releases'
target_tbl = tbl_prefix  + 'release'

tbl = 'apps_download'
src_col = 'ipaddr'
trg_col = 'ip4addr'

con = None
try:
    con = mdb.connect('localhost', 'root', '', 'CyAppStore')
    cur = con.cursor()
    cur.execute('SELECT id, {0} FROM {1}'.format(src_col, tbl))
    for (id, old) in list(cur.fetchall()):
        oct1, oct2, oct3, oct4 = old.split('.')
        oct1, oct2, oct3, oct4 = (long(oct1), long(oct2), long(oct3), long(oct4))
        new = oct4 + (256L * oct3) + (256L ** 2) * oct2 + (256L ** 3) * oct1
        cur.execute('UPDATE %s SET ip4addr=%d WHERE id=%s' % (tbl, new, id))
finally:
    if con:
        con.close()
