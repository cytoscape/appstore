#!/bin/sh
# For each browser: start a fresh App Store container on the exported port, wait for it,
# copy out the seeded sessions, and run the Playwright suite in integration/ against it.
# Called by make integration-test, which builds the image and installs the suite first.
set -eu

IMAGE=${INTEGRATION_IMAGE:-appstore-it:local}
PORT=${INTEGRATION_PORT:-8080}
BROWSERS=${INTEGRATION_BROWSERS:-chromium firefox}
CONTAINER=appstore-it
URL=http://localhost:$PORT

cleanup() {
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_until_up() {
    tries=0
    until [ "$(curl -s -o /dev/null -w '%{http_code}' "$URL/apps/")" = "200" ]; do
        tries=$((tries + 1))
        if [ "$tries" -ge 120 ]; then
            echo "App Store container did not answer on $URL/apps/ within 120 s" >&2
            docker logs "$CONTAINER" >&2 || true
            exit 1
        fi
        sleep 1
    done
}

mkdir -p integration/.auth
for browser in $BROWSERS; do
    cleanup
    echo "=== $browser: starting $IMAGE on $URL"
    docker run -d --name "$CONTAINER" -p "$PORT:8000" -e "APPSTORE_PUBLIC_URL=$URL" "$IMAGE" >/dev/null
    wait_until_up
    docker cp "$CONTAINER:/srv/appstore/build/it_sessions.json" integration/.auth/sessions.json
    (cd integration && APPSTORE_URL=$URL npx playwright test --project="$browser")
done
