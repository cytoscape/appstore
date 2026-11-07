=======
History
=======

2.1.0 (2026-11-05)
---------------------

* Cytoscape Web apps can be submitted to, reviewed in and installed from the App Store.

  * **Submitting:** a developer uploads a built bundle (a zip of the build's ``dist``). The Store
    checks it (zip integrity, safe paths, a ``remoteEntry.js`` and the ``cy-manifest.json`` app id)
    and keeps it under ``pending/`` until an admin accepts it. Submitting from a GitHub URL is
    stored but can't be approved yet.

  * **Hosting:** an accepted bundle is served under ``/web/<app>/<version>/`` with a generated
    ``manifest.json``, which publishes the bundle's own app id rather than the URL slug.
    `Issue #144 <https://github.com/cytoscape/appstore/issues/144>`_

  * **Installing:** the app page's **Install in Cytoscape Web** button opens Cytoscape Web with
    ``?installApp=<manifest URL>``, and counts the install. Each release shows its Manifest URL with
    a copy button. Web apps are marked beta, and older versions are listed in Release History.

* Service apps, backed by a hosted endpoint, can be submitted to and installed from the App Store.

  * **Submitting:** the Store checks the endpoint is reachable, answers its status check and isn't
    on a private network, then queues it for review.

  * **Installing:** **Open in Cytoscape Web** opens the service in Cytoscape Web, and installs are
    counted per release.

* Service apps can be installed into Cytoscape Desktop from their App Store page, using the
  Desktop Service App's ``serviceapps`` commands, as part of
  `cytoscape/cytoscape#28 <https://github.com/cytoscape/cytoscape/issues/28>`_.

  * **Install button:** the page's **Install in Cytoscape Desktop** button checks the user's running
    Desktop and shows Install, Installed or Upgrade. It installs through ``serviceapps install`` with a
    10 s timeout. If Desktop isn't running, or lacks the Desktop Service App, the button is greyed out
    and its info icon's tooltip says what Desktop needs: to be running, and to have the Desktop
    Service App installed. The page links to the Desktop Service App's store page.
    `Issue #151 <https://github.com/cytoscape/appstore/issues/151>`_,
    `Issue #154 <https://github.com/cytoscape/appstore/issues/154>`_

  * **Install count:** ``/download/install/<app>/<version>?client=desktop`` counts a Desktop install
    in the service app's install count and replies 204, without the redirect to Cytoscape Web. The
    per-app stats timeline, which returned 500 for every platform, now reports each platform's own
    counts.
    `Issue #150 <https://github.com/cytoscape/appstore/issues/150>`_

  * **Release integrity:** a service app's latest release is chosen by version number, so 1.10
    comes after 1.9, rather than by upload date. A test guards ``/backend/all_apps``, which Desktop
    reads, so that it never lists service or web releases.
    `Issue #152 <https://github.com/cytoscape/appstore/issues/152>`_

  * **Tests and CI:** ``make test`` now builds a ``uv`` virtualenv (Python 3.12), runs
    headless-Chromium browser tests of the install button against a fake CyREST, and runs in GitHub
    Actions on pull requests. ``uv`` is a new host prerequisite, and ``social-auth-core`` is pinned
    to 4.5.4. ``make integration-test`` runs a Playwright suite, in Chromium and Firefox, against the
    App Store in a Docker container; it also runs in GitHub Actions on pull requests.

* One app, many platforms: an app's name is its identity, and its page covers every platform it is
  released on. `Issue #155 <https://github.com/cytoscape/appstore/issues/155>`_

  * **Identity:** a Desktop, Cytoscape Web or Service version submitted under an existing app's name
    by one of its editors joins that app, after admin review, instead of being refused as a name
    collision. Someone who isn't an editor can't submit under the name. The review queue labels each
    submission **New app** or **New platform**.

  * **Platform selector:** the app page's **Available Platforms** buttons choose a platform. Details and
    Release History show the selected platform's, and switching keeps the open tab. A page opens
    on the first platform and Details, and the Details / Release History tabs look like the
    platform buttons (solid blue when selected).

  * **Per-platform content:** each platform keeps its own description, details, categories,
    screenshots, authors, links and licence, and never shows another platform's. The name, icon,
    editors, ratings and the downloads total are shared. An app's existing content stays with the
    platform it was on, so existing pages look the same; a platform added later starts empty. When
    Desktop joins an app that was on Web or Service, that content moves to its original platform,
    so Desktop's starts empty. ``manage.py set_original_platform`` separates the content of an app
    that gained a platform before this rule.

  * **Editing:** the edit page edits one platform at a time, and asks whether to save or discard
    unsaved changes before switching platform. If a save fails, the saving dialog closes, the page
    says what failed and keeps the unsaved changes, and it does not switch platform.

  * **Listings and search:** a platform's listing describes each app as that platform's page does,
    category pages and counts include categories on any platform, and search covers every
    platform's content. Apps that are only Cytoscape 2.x plugins have their own page.

  * **Unchanged for Cytoscape Desktop:** ``/backend/all_apps``, which Desktop's App Manager reads,
    returns the same apps and content as before.

  * **Deploying:** this release adds database migrations, so run ``makemigrations`` and ``migrate``
    without ``--dry-run``. They drop the ``App.platform`` column, which 2.0.x releases need, so back
    up the database before deploying: rolling back to 2.0.x means restoring that backup.
    On MySQL/MariaDB, ``migrate`` first converts a MyISAM ``apps_tag`` to InnoDB and widens an
    ``int`` ``apps_tag.id`` (and ``apps_app_tags.tag_id``) to ``bigint``, since a new foreign key
    references it, and changes a latin1 database default character set to utf8 (so new tables can
    store any text), printing each change; it changes nothing on a database that is already right.

* **Version in the footer:** every page shows the running version after **Contact Us**: the git tag
  the checkout is at, else its short commit hash, else ``develop`` when git can't tell.

* Fixes and platform updates since 2.0.3.

  * **Submitting:** the **Submit an API** page no longer hangs on ``pom.xml`` upload
    (`Issue #149 <https://github.com/cytoscape/appstore/issues/149>`_), and accepting new apps works
    again.

  * **Installing from Cytoscape:** the Desktop install button works inside Cytoscape's CyBrowser,
    offers the jar as a download link, and accepting an app's licence installs only once
    (CYTOSCAPE-13032).

  * **Download statistics:** a unique constraint stops concurrent downloads from creating duplicate
    statistics rows.

  * **Platform:** Django 4.2.15, MariaDB and Rocky Linux 9.


2.0.3 (2021-01-23)
---------------------

* Fixed bug where comparison of minimum version of supported Cytoscape fails
  since versions are compared as strings.
  `Issue #88 <https://github.com/cytoscape/appstore/issues/88>`_

* Fixed bug where uploading pom.xml and javadoc jar file failed.
  `Issue #91 <https://github.com/cytoscape/appstore/issues/91>`_


2.0.2 (2020-08-07)
---------------------

* Fixed bug where incorrect server URL was being sent in App submission and approval emails.
  `Issue #87 <https://github.com/cytoscape/appstore/issues/87>`_

* Fixed bug where editors could not be added to an existing app. 
  `Issue #86 <https://github.com/cytoscape/appstore/issues/86>`_

* Fixed bug where server would log an error when someone visited the no longer existing help/competitions
  URL. `Issue #84 <https://github.com/cytoscape/appstore/issues/84>`_

2.0.1 (2020-06-19)
---------------------

* Fixed bug where uploading an App with jar file smaller then 2.5 megabytes would fail

2.0.0 (2020-06-16)
---------------------

* Upgraded AppStore to Django 2.2.13
