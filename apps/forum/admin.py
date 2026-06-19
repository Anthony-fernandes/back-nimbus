from django.contrib import admin
from .models import ForumCategory, ForumTopic, ForumReply

admin.site.register(ForumCategory)
admin.site.register(ForumTopic)
admin.site.register(ForumReply)
