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

CHARSET = 'utf8'
COLLATION = 'utf8_general_ci'


def _value(cursor, sql, params=()):
    cursor.execute(sql, params)
    row = cursor.fetchone()
    return row[0] if row else None


def prepare_schema(connection):
    """
    Converts INNODB_TABLES that are MyISAM to InnoDB, widens BIGINT_COLUMNS that are int to
    bigint, and makes the database's default character set utf8 if it is latin1. Returns the
    statements it ran.
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
        for statement in statements:
            logger.warning('Preparing the database for migrations: %s', statement)
            cursor.execute(statement)
    return statements


def prepare_schema_before_migrate(sender, using, **kwargs):
    """pre_migrate receiver; migrate sends pre_migrate once per app, so this runs for 'apps' only."""
    from django.db import connections
    for statement in prepare_schema(connections[using]):
        print('  Prepared the database: %s' % statement)
