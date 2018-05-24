from django.contrib import auth
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from social_auth.decorators import dsa_view
from social_auth.views import associate_complete, complete_process
from util.view_util import html_response
import logging

def login(request):
    next_url = request.GET.get('next', reverse('default-page'))
    if request.user.is_authenticated():
        return HttpResponseRedirect(next_url)
    return html_response('login.html', {'navbar_selected': 'signin', 'next_url': next_url}, request)

logger = logging.getLogger(__name__)

# If a user logs in through Google and clicks "Deny", it'll throw an exception.
# However, social_auth.views.complete() does not handle exceptions at all. This
# method replaces complete() to handle exceptions.
@csrf_exempt
@dsa_view()
def login_done(request, backend, *args, **kwargs):
    if request.user.is_authenticated():
        return associate_complete(request, backend, *args, **kwargs)
    else:
        try:
            return complete_process(request, backend, *args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return html_response('login.html', {'at_login': True, 'error': str(e)}, request)

def logout(request):
    auth_logout(request)
    next_url = request.GET.get('next', reverse('default-page'))
    return HttpResponseRedirect(next_url)
