=======
History
=======

Unreleased
---------------------

* Service apps can be installed into Cytoscape Desktop from their App Store page, using the
  Desktop Service App's ``serviceapps`` commands, as part of
  `cytoscape/cytoscape#28 <https://github.com/cytoscape/cytoscape/issues/28>`_.

  * **Install button:** the page's **Install in Cytoscape Desktop** button checks the user's running
    Desktop and shows Install, Installed or Upgrade. It installs through ``serviceapps install`` with a
    10 s timeout. If Desktop isn't running, or lacks the Desktop Service App, the button is greyed out
    with a tooltip, and the page links to the Desktop Service App's store page.
    `Issue #151 <https://github.com/cytoscape/appstore/issues/151>`_

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
    to 4.5.4.

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
