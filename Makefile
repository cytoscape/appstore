index:
	rm -rf xapian_indices
	python manage.py reindex_xapian

nopyc:
	find . -name "*.pyc" -exec rm -vf {} \;
