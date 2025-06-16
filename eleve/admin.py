from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'user_display', 
        'notification_type', 
        'message_preview', 
        'is_read_display', 
        'created_at_display',
        'is_recent_display'
    ]
    list_filter = [
        'notification_type', 
        'is_read', 
        'created_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = [
        'user__username', 
        'user__first_name', 
        'user__last_name', 
        'message'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'read_at']
    
    # Filtres personnalisés
    list_per_page = 25
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def user_display(self, obj):
        """Affichage amélioré de l'utilisateur"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name} ({obj.user.username})"
        return obj.user.username
    user_display.short_description = "Utilisateur"
    user_display.admin_order_field = 'user__username'
    
    def message_preview(self, obj):
        """Aperçu du message (truncated)"""
        if len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message
    message_preview.short_description = "Message"
    
    def is_read_display(self, obj):
        """Affichage coloré du statut de lecture"""
        if obj.is_read:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Lu</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Non lu</span>'
        )
    is_read_display.short_description = "Statut"
    is_read_display.admin_order_field = 'is_read'
    
    def created_at_display(self, obj):
        """Affichage formaté de la date de création"""
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_display.short_description = "Créé le"
    created_at_display.admin_order_field = 'created_at'
    
    def is_recent_display(self, obj):
        """Indicateur de notification récente"""
        if obj.is_recent:
            return format_html(
                '<span style="color: orange; font-weight: bold;">🔥 Récent</span>'
            )
        return "-"
    is_recent_display.short_description = "Récent"
    
    def get_queryset(self, request):
        """Optimiser les requêtes avec select_related"""
        return super().get_queryset(request).select_related('user')
    
    # Actions personnalisées
    def mark_as_read(self, request, queryset):
        """Marquer les notifications sélectionnées comme lues"""
        updated = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            updated += 1
        
        self.message_user(
            request,
            f"{updated} notification(s) marquée(s) comme lue(s)."
        )
    mark_as_read.short_description = "Marquer comme lues"
    
    def mark_as_unread(self, request, queryset):
        """Marquer les notifications sélectionnées comme non lues"""
        updated = queryset.filter(is_read=True).update(
            is_read=False,
            read_at=None
        )
        
        self.message_user(
            request,
            f"{updated} notification(s) marquée(s) comme non lue(s)."
        )
    mark_as_unread.short_description = "Marquer comme non lues"
    
    # Fieldsets pour l'édition
    fieldsets = (
        ('Informations principales', {
            'fields': ('user', 'notification_type', 'message')
        }),
        ('Référence', {
            'fields': ('related_id',),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('is_read', 'created_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Permettre l'ajout de notifications depuis l'admin"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Permettre la suppression seulement aux superusers"""
        return request.user.is_superuser