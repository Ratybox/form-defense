from django.contrib import admin
from .models import FormEntry


@admin.register(FormEntry)
class FormEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email']
    readonly_fields = ['password_hash', 'created_at']
