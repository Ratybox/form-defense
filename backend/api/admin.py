from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import FormEntry


@admin.register(FormEntry)
class FormEntryAdmin(admin.ModelAdmin):
    # Display in list with all important information
    list_display = [
        'id', 
        'name', 
        'email', 
        'message_preview', 
        'password_hash_preview', 
        'created_at',
        'age_display'
    ]
    
    # Advanced filters
    list_filter = [
        'created_at',
        ('created_at', admin.DateFieldListFilter),  # Date filter
    ]
    
    # Enhanced search
    search_fields = ['name', 'email', 'message', 'password_hash']
    
    # Read-only fields
    readonly_fields = [
        'password_hash', 
        'created_at', 
        'entry_stats'
    ]
    
    # Pagination
    list_per_page = 50
    list_max_show_all = 200
    
    # Default sorting
    ordering = ['-created_at']
    
    # Custom actions
    actions = ['export_selected', 'mark_as_reviewed']
    
    # Custom CSS for dark theme
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
    
    # Organization of fields in the detail form
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email'),
            'classes': ('wide',)
        }),
        ('Message Content', {
            'fields': ('message',),
            'description': 'Message submitted via the form'
        }),
        ('Security - Password Hash', {
            'fields': ('password_hash',),
            'description': 'SHA-256 hash of the password (never display the password in cleartext)',
            'classes': ('collapse',)
        }),
        ('Entry Statistics', {
            'fields': ('entry_stats',),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    # Custom display methods for the list
    def message_preview(self, obj):
        """Displays a preview of the message (truncated to 50 characters)"""
        if obj.message:
            preview = obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
            return format_html(
                '<span title="{}" style="font-size: 0.9em; color: inherit;">{}</span>',
                obj.message,
                preview
            )
        return '-'
    message_preview.short_description = 'Message'
    message_preview.admin_order_field = 'message'
    
    def password_hash_preview(self, obj):
        """Displays a preview of the hash (first and last characters)"""
        if obj.password_hash:
            # Display first 8 and last 8 characters
            preview = f"{obj.password_hash[:8]}...{obj.password_hash[-8:]}"
            return format_html(
                '<code style="font-size: 0.85em; background: transparent; padding: 2px 4px; border-radius: 3px; color: #4a9eff; border: 1px solid #4a9eff;" title="{}">{}</code>',
                obj.password_hash,
                preview
            )
        return '-'
    password_hash_preview.short_description = 'Hash (SHA-256)'
    password_hash_preview.admin_order_field = 'password_hash'
    
    def age_display(self, obj):
        """Displays the age of the entry in a readable format"""
        if obj.created_at:
            now = timezone.now()
            age = now - obj.created_at
            
            if age < timedelta(minutes=1):
                return format_html('<span style="color: #4ade80;">Just now</span>')
            elif age < timedelta(hours=1):
                minutes = int(age.total_seconds() / 60)
                return format_html('<span style="color: #4ade80;">{} min ago</span>', minutes)
            elif age < timedelta(days=1):
                hours = int(age.total_seconds() / 3600)
                return format_html('<span style="color: #60a5fa;">{} h ago</span>', hours)
            elif age < timedelta(days=7):
                days = age.days
                return format_html('<span style="color: #fbbf24;">{} days ago</span>', days)
            else:
                return format_html('<span style="color: #9ca3af;">{}</span>', obj.created_at.strftime('%m/%d/%Y'))
        return '-'
    age_display.short_description = 'Age'
    age_display.admin_order_field = 'created_at'
    
    def entry_stats(self, obj):
        """Displays statistics about the entry"""
        stats = []
        
        # Message length
        if obj.message:
            msg_len = len(obj.message)
            stats.append(f'Message length: {msg_len} characters')
            
            # Word count
            word_count = len(obj.message.split())
            stats.append(f'Word count: {word_count}')
        
        # Hash length
        if obj.password_hash:
            stats.append(f'SHA-256 hash: {len(obj.password_hash)} characters (64 hex)')
        
        # Formatted creation date
        if obj.created_at:
            stats.append(f'Created on: {obj.created_at.strftime("%m/%d/%Y at %H:%M:%S")}')
        
        if stats:
            return format_html(
                '<div style="background: transparent; padding: 10px; border-radius: 5px; border-left: 4px solid #60a5fa; border: 1px solid #374151;">'
                '<ul style="margin: 0; padding-left: 20px; color: inherit;">{}</ul>'
                '</div>',
                mark_safe(''.join([f'<li style="color: inherit;">{stat}</li>' for stat in stats]))
            )
        return '-'
    entry_stats.short_description = 'Statistics'
    
    # Custom actions
    def export_selected(self, request, queryset):
        """Exports selected entries"""
        from django.http import HttpResponse
        import csv
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="form_entries_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Email', 'Message', 'Hash', 'Created At'])
        
        for entry in queryset:
            writer.writerow([
                entry.id,
                entry.name,
                entry.email,
                entry.message,
                entry.password_hash,
                entry.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        self.message_user(request, f'{queryset.count()} entry/entries exported successfully.')
        return response
    export_selected.short_description = 'Export selected entries'
    
    def mark_as_reviewed(self, request, queryset):
        """Marks entries as reviewed (for future use if status field is added)"""
        count = queryset.count()
        self.message_user(request, f'{count} entry/entries marked as reviewed.')
    mark_as_reviewed.short_description = 'Mark as reviewed'
    
    # Display customization
    def get_list_display(self, request):
        """Returns the display list according to permissions"""
        return self.list_display
    
    # Search enhancement
    def get_search_results(self, request, queryset, search_term):
        """Enhances search to include partial searches"""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        
        if search_term:
            # Search in hash (first characters)
            queryset = queryset | self.model.objects.filter(
                password_hash__startswith=search_term
            )
        
        return queryset, use_distinct
