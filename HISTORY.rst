=======
History
=======

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
