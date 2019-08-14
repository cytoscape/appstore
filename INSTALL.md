# Install overview
This project currently only works with `python 2` and very old django version `django < 1.9`.
This instructions show how to setup a local virtual environment.

## Checkout code base
```
git clone https://github.com/cytoscape/appstore.git CyAppStore
```
The root folder must be named `CyAppStore` so that the relative imports are working.

## Additional requirements
- mysql
- xapian (https://xapian.org/docs/install.html, https://github.com/notanumber/xapian-haystack/blob/master/install_xapian.sh)



## Setup Virtual Environment
``` 
mkvirtualenv appstore --python=python2
(appstore) ./install_xapian.sh 1.4.5
(appstore) pip install gevent
(appstore) pip install -r requirement.txt
```

## Perform the migrations
```
(appstore) python manage.py migrate
```

## Test the server
```
(appstore) python manage.py runserver
```

