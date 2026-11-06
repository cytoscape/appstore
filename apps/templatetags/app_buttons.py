from django import template
from apps.models import App

register = template.Library()

@register.inclusion_tag('app_button.html')
def app_button(app, order_index):
    try:
        app.star_percentage = 100 * app.object.stars / 5 / app.object.votes if app.object.votes else 0
        c = {}
        c['app'] = app.object
        c['order_index'] = order_index
        return c
    except:
        app.star_percentage = 100 * app.stars / 5 / app.votes if app.votes else 0 
        c = {}
        c['app'] = app
        c['order_index'] = order_index
        return c

@register.inclusion_tag('app_button.html')
def app_button_by_name(app_name):
    try:
        app = App.objects.get(name=app_name)
        c = dict()
        c['app'] = app
        return c
    except:
        return {}

@register.inclusion_tag('app_buttons.html')
def app_buttons(apps):
    return {'apps': list(apps)}


@register.inclusion_tag('list_of_apps_search.html')
def list_of_apps_search(apps, include_relevancy = False):
    apps = filter(lambda a: hasattr(a.object, 'has_releases'), apps)
    apps_with_releases = filter(lambda a: a.object.has_releases, apps)
    apps_without_releases = filter(lambda a: not a.object.has_releases, apps)
#    # a list of sort buttons to display
#                    # button name       div attr name          attr type
#    sort_criteria = (('name',           'object.fullname',            'str'),
#                    ('downloads',      'object.downloads',           'int'),
#                    ('votes',          'object.votes',               'int'),
#                    ('newest release', 'object.latest_release_date', 'date'))
#    if (include_relevancy):
#        sort_criteria = (('relevancy',  'order_index',  'int'), ) + sort_criteria
    return {'apps_with_releases': apps_with_releases,
            'apps_without_releases': apps_without_releases}


@register.inclusion_tag('list_of_apps.html')
def list_of_apps(apps, include_relevancy = False):
    apps_with_releases = filter(lambda a: a.has_releases, apps)
    apps_without_releases = filter(lambda a: not a.has_releases, apps)
    # a list of sort buttons to display
                    # button name       div attr name          attr type
    sort_criteria = (('name',           'fullname',            'str'),
                     ('downloads',      'downloads',           'int'),
                     ('votes',          'votes',               'int'),
                     ('newest release', 'latest_release_date', 'date'))
    if (include_relevancy):
        sort_criteria = (('relevancy',  'order_index',  'int'), ) + sort_criteria
    return {'apps_with_releases': apps_with_releases,
            'apps_without_releases': apps_without_releases,
            'sort_criteria': sort_criteria}
