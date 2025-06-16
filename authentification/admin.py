from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'classe', 'is_active')
    list_filter = ('user_type', 'classe', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'numero_etudiant')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Spécifiques', {
            'fields': ('user_type', 'classe', 'numero_etudiant', 'telephone', 'date_naissance', 'adresse')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations Spécifiques', {
            'fields': ('user_type', 'classe', 'numero_etudiant', 'email', 'first_name', 'last_name')
        }),
    )
