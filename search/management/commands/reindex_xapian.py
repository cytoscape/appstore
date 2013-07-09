import xapian
from django.core.management.base import BaseCommand
import os
import os.path
import sys
from apps import models
import inspect
import re
from conf.xapian import XAPIAN_INDICES_DIR

def index_model(dbs_root, model_name, model):
    db_path = os.path.join(dbs_root, model_name)
    db = xapian.WritableDatabase(db_path, xapian.DB_CREATE_OR_OPEN)
    indexer = xapian.TermGenerator()
    indexer.set_stemmer(xapian.Stem('english'))
    (schema, keyname) = (model.search_schema, model.search_key)
    for obj in model.objects.all():
        key = str(getattr(obj, keyname))
        doc = xapian.Document()
        doc.set_data(key)
        indexer.set_document(doc)
        for field in schema:
            do_camel_case = False
            if field[0] == '^':
                do_camel_case = True
                field = field[1:]
            value = getattr(obj, field)
            if not value: continue
            if do_camel_case:
                index_camel_case(value, indexer)
            else:
                indexer.index_text(value)
        db.add_document(doc)

camel_case_re = re.compile(r'([A-Z]+[a-z]*)')
def index_camel_case(name, indexer):
    indexer.index_text(name)
    for substring in camel_case_re.findall(name):
        indexer.index_text(substring)

class Command(BaseCommand):
    help = 'Reindexes all apps using the Xapian text search library'

    def handle(self, *args, **options):
        if not os.path.exists(XAPIAN_INDICES_DIR):
            os.mkdir(XAPIAN_INDICES_DIR)
        
        print 'Indexing...',
        sys.stdout.flush()
        for model_name, model in inspect.getmembers(models, inspect.isclass):
            if not 'search_schema' in dir(model): continue
            print model_name,
            sys.stdout.flush()
            index_model(XAPIAN_INDICES_DIR, model_name, model)
        print 'done.'
