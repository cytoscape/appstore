from haystack import indexes
from apps.models import App

class AppIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document = True, use_template = True)
    name = indexes.CharField(model_attr = 'name')
    has_releases = indexes.BooleanField(model_attr='has_releases')
    tags = indexes.MultiValueField(model_attr = 'tags',null=True)
    authors = indexes.MultiValueField(model_attr = 'authors',null=True)
    def get_model(self):
        return App
    def prepare_authors(self, obj):
        return [author.id for author in obj.authors.all()]
    def prepare_tags(self, obj):
        return [tag.id for tag in obj.tags.all()]

