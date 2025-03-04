from django.contrib import admin
from .models import UserProfile, Tip, Like, Follow, Share

admin.site.register(UserProfile)
admin.site.register(Tip)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Share)