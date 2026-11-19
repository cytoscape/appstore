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

mkdir -p integration/.auth
for browser in $BROWSERS; do
    cleanup
    echo "=== $browser: starting the App Store on a fresh MariaDB"
    if ! $COMPOSE up -d --build --wait app; then
        echo "The App Store container did not become healthy" >&2
        $COMPOSE logs app >&2 || true
        exit 1
    fi
    $COMPOSE cp app:/srv/appstore/build/it_sessions.json integration/.auth/sessions.json
    $COMPOSE run --rm e2e --project="$browser"
done
