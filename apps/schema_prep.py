"""
Brings an old MySQL/MariaDB App Store database up to what the migrations need, before they run.

The production database predates Django's InnoDB and utf8 defaults:
- Many of its tables are MyISAM. InnoDB foreign keys cannot reference a MyISAM table, so a
  migration adding one fails with errno 150 "Foreign key constraint is incorrectly formed".
- Its default character set is latin1, which every table a migration creates inherits. Such a
  table cannot store text outside latin1 (the app's own tables are utf8).
- Some of its id columns are int, from before Django's bigint ids, while the migrations record
  them as bigint. A migration sizes a new foreign key column from that record, so a bigint
  column referencing an int id fails with the same errno 150 (prod's apps_tag.id, #155).
- apps_orderedauthor began as the apps_app_authors table of App.authors, and kept that table's
  unique key on (app_id, author_id), which no migration records. Since an app's platforms each
  have their own authors (#155), that key refuses an author listed on two of an app's platforms,
  so saving one gave a 500 (#160).

prepare_schema() fixes these before every migrate (it is connected to pre_migrate). It changes
nothing on other databases, on a database that is already right, or for tables that do not
exist yet (migrations create those as InnoDB, with bigint ids).
"""
import logging

logger = logging.getLogger(__name__)

# Tables that InnoDB foreign keys of migrations reference, and so must be InnoDB:
# apps_appplatformcontent_tags.tag_id references apps_tag (#155).
INNODB_TABLES = ('apps_tag',)

# int columns that migrations record as bigint and that new foreign keys reference, widened to
# bigint, with the existing columns that reference them (prod has no constraints on these):
# apps_appplatformcontent_tags.tag_id references apps_tag.id, like apps_app_tags.tag_id (#155).
BIGINT_COLUMNS = (
    ('apps_tag', 'id', 'BIGINT NOT NULL AUTO_INCREMENT'),
    ('apps_app_tags', 'tag_id', 'BIGINT NOT NULL'),
)

# Unique keys that no migration records and that the models no longer allow, dropped: an app's
# author once per platform, not once in all (#160). MariaDB won't drop the only index a foreign key
# can use, so where no other index starts with the key's first column, one is added first.
OBSOLETE_UNIQUE_KEYS = (
    ('apps_orderedauthor', ('app_id', 'author_id')),
)

CHARSET = 'utf8'
COLLATION = 'utf8_general_ci'


def _value(cursor, sql, params=()):
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return row[0] if row else None


def _indexes(cursor, table):
    """'table's indexes but its primary key, by name: (whether it is unique, its columns in order)."""
    cursor.execute('SELECT INDEX_NAME, COLUMN_NAME, NON_UNIQUE FROM information_schema.STATISTICS '
                   "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND INDEX_NAME <> 'PRIMARY' "
                   'ORDER BY INDEX_NAME, SEQ_IN_INDEX', (table,))
    indexes = {}
    for name, column, non_unique in cursor.fetchall():
        indexes.setdefault(name, (not int(non_unique), []))[1].append(column)
    return {name: (unique, tuple(columns)) for name, (unique, columns) in indexes.items()}


def prepare_schema(connection):
    """
    Converts INNODB_TABLES that are MyISAM to InnoDB, widens BIGINT_COLUMNS that are int to
    bigint, drops OBSOLETE_UNIQUE_KEYS, and makes the database's default character set utf8 if
    it is latin1. Returns the statements it ran.
    """
    if connection.vendor != 'mysql':
        return []
    statements = []
    with connection.cursor() as cursor:
        charset = _value(cursor, 'SELECT DEFAULT_CHARACTER_SET_NAME FROM information_schema.SCHEMATA '
                                 'WHERE SCHEMA_NAME = DATABASE()')
        if charset and charset.lower().startswith('latin1'):
            statements.append('ALTER DATABASE CHARACTER SET %s COLLATE %s' % (CHARSET, COLLATION))
        for table in INNODB_TABLES:
            engine = _value(cursor, 'SELECT ENGINE FROM information_schema.TABLES '
                                    'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s', (table,))
            if engine and engine.lower() == 'myisam':
                statements.append('ALTER TABLE `%s` ENGINE=InnoDB' % table)
        for table, column, definition in BIGINT_COLUMNS:
            data_type = _value(cursor, 'SELECT DATA_TYPE FROM information_schema.COLUMNS '
                                       'WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s',
                               (table, column))
            if data_type and data_type.lower() == 'int':
                statements.append('ALTER TABLE `%s` MODIFY `%s` %s' % (table, column, definition))
        for table, columns in OBSOLETE_UNIQUE_KEYS:
            indexes = _indexes(cursor, table)
            obsolete = sorted(name for name, (unique, key_columns) in indexes.items()
                              if unique and key_columns == columns)
            if obsolete and not any(key_columns[0] == columns[0] for name, (_, key_columns) in indexes.items()
                                    if name not in obsolete):
                statements.append('ALTER TABLE `%s` ADD INDEX `%s_%s` (`%s`)' % (table, table, columns[0], columns[0]))
            for name in obsolete:
                statements.append('ALTER TABLE `%s` DROP INDEX `%s`' % (table, name))
        for statement in statements:
            logger.warning('Preparing the database for migrations: %s', statement)
            cursor.execute(statement)
    return statements


def prepare_schema_before_migrate(sender, using, **kwargs):
    """pre_migrate receiver; migrate sends pre_migrate once per app, so this runs for 'apps' only."""
    from django.db import connections
    for statement in prepare_schema(connections[using]):
        print('  Prepared the database: %s' % statement)
