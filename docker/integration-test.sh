#!/bin/sh
# For each browser: start a fresh App Store container on a fresh MariaDB (docker/compose.yml),
# wait for it, copy out the seeded sessions, and run the Playwright suite in integration/ in the
# e2e container against it. Called by make integration-test; the host needs only Docker.
set -eu

BROWSERS=${INTEGRATION_BROWSERS:-chromium firefox}
COMPOSE="docker compose -f docker/compose.yml -p appstore-it"

cleanup() {
    $COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

fail_deploy() {
    echo "Deploy check failed: $1" >&2
    $COMPOSE logs app >&2 || true
    exit 1
}

# runs the SQL in $1 on the db container's AppStore database, printing one tab-separated row per line
query() {
    $COMPOSE exec -T db mariadb -uroot -pappstore-test -N -B AppStore -e "$1"
}

# apps_orderedauthor's unique keys, but its primary key, one per line: name<TAB>columns in order
unique_author_keys() {
    query "SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) FROM information_schema.STATISTICS
           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'apps_orderedauthor' AND NON_UNIQUE = 0
           AND INDEX_NAME <> 'PRIMARY' GROUP BY INDEX_NAME"
}

# The app container put its database in prod's state, then ran the deploy's migrate (entrypoint.sh):
# that migrate must have dropped the old unique key on (app_id, author_id) (#160).
check_deploy() {
    $COMPOSE logs app | grep -qF 'Prepared the database: ALTER TABLE `apps_orderedauthor` DROP INDEX `app_id`' \
        || fail_deploy "migrate didn't print that it dropped the old key app_id"
    keys=$(unique_author_keys)
    if printf '%s\n' "$keys" | grep -q "$(printf '\tapp_id,author_id$')"; then
        fail_deploy "apps_orderedauthor still has a unique key on (app_id, author_id): $keys"
    fi
    # and the model's rule in its place: an author once per platform of an app
    printf '%s\n' "$keys" | grep -qx "$(printf 'unique_app_author_platform\tapp_id,author_id,platform')" \
        || fail_deploy "apps_orderedauthor has no unique key unique_app_author_platform on (app_id, author_id, platform): $keys"
}

mkdir -p integration/.auth
for browser in $BROWSERS; do
    cleanup
    echo "=== $browser: starting the App Store on a fresh MariaDB"
    if ! $COMPOSE up -d --build --wait app; then
        echo "The App Store container did not become healthy" >&2
        $COMPOSE logs app >&2 || true
        exit 1
    fi
    check_deploy
    $COMPOSE cp app:/srv/appstore/build/it_sessions.json integration/.auth/sessions.json
    $COMPOSE run --rm e2e --project="$browser"
done
