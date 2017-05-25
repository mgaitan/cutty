from django.contrib import admin
from .models import (
    Brand, System, Profile, Cut, OpeningKind, Opening,
    Project
)

class OpeningKindModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

admin.site.register(OpeningKind, OpeningKindModelAdmin)


for cls in (Brand, System, Profile, Cut, Opening, Project):
    admin.site.register(cls)
