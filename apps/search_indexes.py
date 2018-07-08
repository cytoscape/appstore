from haystack import indexes
from apps.models import App

class AppIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document = True, use_template = True)
    name = indexes.CharField(model_attr = 'name')
    tags = indexes.MultiValueField(model_attr = 'tags',null=True)
    authors = indexes.MultiValueField(model_attr = 'authors',null=True)
    def get_model(self):
        return App
    

