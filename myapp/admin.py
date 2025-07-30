from django.contrib import admin
from .models import CountingSession, PalmOilCount

# Register your models here.
admin.site.register(CountingSession)

@admin.register(PalmOilCount)
class PalmOilCountAdmin(admin.ModelAdmin):
    list_display = ('date', 'suitable_count', 'unsuitable_count', 'status')
    list_filter = ('status', 'date')
    search_fields = ('date', 'status')
