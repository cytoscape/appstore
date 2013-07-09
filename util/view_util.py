import json
import re
from cStringIO import StringIO
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.serializers.json import DjangoJSONEncoder, Serializer
from django.db import models

def html_response(template_name, context, request, processors = []):
    return render_to_response(template_name, context, context_instance=RequestContext(request, processors=processors))

def json_response(obj):
    response = HttpResponse(mimetype='application/json; charset=utf-8')
    json.dump(obj, response, separators=(',', ':'), ensure_ascii=False, sort_keys=False, cls=DjangoJSONEncoder)
    #json.dump(obj, response, indent=2, cls=DjangoJSONEncoder)
    return response

def obj_to_dict(obj, fields):
    return dict((field, getattr(obj, field)) for field in fields)

def iter_to_dict(iterable, fields):
    return [obj_to_dict(obj, fields) for obj in iterable]

def get_object_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None
    
IPAddrRE = re.compile(r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$')
def ipaddr_str_to_long(ipaddr_str):
    m = IPAddrRE.match(ipaddr_str)
    if not m: return 0
    oct1, oct2, oct3, oct4 = m.groups()
    oct1, oct2, oct3, oct4 = (long(oct1), long(oct2), long(oct3), long(oct4))
    return oct4 + (oct3 << 8) + (oct2 << 16) + (oct1 << 24)

def ipaddr_long_to_str(ipaddr_long):
    oct4 = ipaddr_long & 255
    ipaddr_long >>= 8
    oct3 = ipaddr_long & 255
    ipaddr_long >>= 8
    oct2 = ipaddr_long & 255
    ipaddr_long >>= 8
    oct1 = ipaddr_long & 255
    return '%d.%d.%d.%d' % (oct1, oct2, oct3, oct4)
    
