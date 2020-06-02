import json
import re
try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
from django.core.serializers.json import DjangoJSONEncoder, Serializer


def html_response(template_name, context, request, processors = []):
    rc = RequestContext(request, processors=processors)
    rc.update(context)
    return render(request, template_name, context=rc.flatten())


def json_response(obj):
    """
    Converts 'obj' passed into a HttpResponse
    :param obj: object to convert to json
    :return:
    :rtype: :py:class:`~django.http.HttpResponse`
    """
    response = HttpResponse(content_type='application/json; charset=utf-8')
    json.dump(obj, response, separators=(',', ':'), ensure_ascii=False, sort_keys=False, cls=DjangoJSONEncoder)
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
    oct1, oct2, oct3, oct4 = (int(oct1), int(oct2),int(oct3), int(oct4))
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
