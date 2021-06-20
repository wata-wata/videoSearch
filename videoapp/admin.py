from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(VideoCategory)
admin.site.register(Video)
admin.site.register(SearchResult)
admin.site.register(SiteUser)