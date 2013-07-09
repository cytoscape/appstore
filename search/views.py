import os.path
import inspect
from django.http import HttpResponseBadRequest
from apps import models
from apps.views import _nav_panel_context
from util.view_util import html_response, get_object_or_none
from types import IntType
import xapian
from conf.xapian import XAPIAN_INDICES_DIR

Xapian_Enquires = None

def _init_xapian_search():
    global Xapian_Enquires
    Xapian_Enquires = {}
    for model_name, model in inspect.getmembers(models, inspect.isclass):
        db_dir = os.path.join(XAPIAN_INDICES_DIR, model_name)
        if not os.path.exists(db_dir): continue
        db = xapian.Database(db_dir)
        enquire = xapian.Enquire(db)
        qp = xapian.QueryParser()
        qp.set_stemmer(xapian.Stem('english'))
        qp.set_database(db)
        qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)
        Xapian_Enquires[model] = (db, enquire, qp)

def _xapian_search(query_str, limit = None, only_matching_ids = False):
    global Xapian_Enquires
    if not Xapian_Enquires:
        _init_xapian_search()
    
    if limit and (not type(limit) == IntType or limit <= 0):
        raise ValueError('limit parameter must be a positive integer')

    all_results = {}
    for model, (db, enquire, qp) in Xapian_Enquires.iteritems():
        q = qp.parse_query(query_str, qp.FLAG_PARTIAL | qp.FLAG_PHRASE)
        enquire.set_query(q)
        matches = enquire.get_mset(0, limit if limit else db.get_doccount())
        if not len(matches): continue
        
        matched_obj_ids = (match.document.get_data() for match in matches)
        if only_matching_ids:
            all_results[model.__name__] = list(matched_obj_ids)
        else:
	    matched_objs = list()
	    for matched_obj_id in matched_obj_ids:
	    	matched_obj = get_object_or_none(model, **{model.search_key: matched_obj_id})
		if not matched_obj: continue
		matched_objs.append(matched_obj)
	    if matched_objs:
	    	all_results[model.__name__] = matched_objs

    return all_results

def search(request):
    query = request.GET.get('q', None)
    if not query:
        return HttpResponseBadRequest('"q" parameter not specified')

    c = {
        'results': _xapian_search(query),
        'search_query': query,
    	'go_back_to': '&ldquo;%s&rdquo; search results' % query,
    }
    return html_response('search.html', c, request, processors = (_nav_panel_context, ))
