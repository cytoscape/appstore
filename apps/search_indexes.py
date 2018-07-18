from haystack import indexes
from apps.models import App

class AppIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document = True, use_template = True)
    name = indexes.CharField(model_attr = 'name')
    fullname = indexes.CharField(model_attr='fullname',null=True)
    description = indexes.CharField(model_attr = 'description',null=True)
    details = indexes.CharField(model_attr = 'details',null=True)
    has_releases = indexes.BooleanField(model_attr='has_releases',null = True)
    tags = indexes.MultiValueField(model_attr = 'tags',null=True)
    authors = indexes.MultiValueField(model_attr = 'authors',null=True)
    downloads = indexes.IntegerField(model_attr = 'downloads',null = True)
    votes = indexes.IntegerField(model_attr = 'votes',null = True)
    stars =indexes.IntegerField(model_attr = 'stars',null = True) 
    latest_release_date = indexes.DateField(model_attr = 'latest_release_date',null= True)

    

    def get_model(self):
        return App
    def prepare_authors(self, obj):
        return [author.id for author in obj.authors.all()]
    def prepare_tags(self, obj):
        return [tag.id for tag in obj.tags.all()]

