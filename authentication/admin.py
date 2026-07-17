# authentication/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur

class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'telephone', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'sexe')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations personnelles', {
            'fields': ('cin', 'reference', 'profile_photo', 'date_naissance', 'sexe', 
                      'telephone', 'telephone2', 'adresse_actuelle', 'activite_actuelle', 
                      'rating', 'must_change_password')
        }),
    )

admin.site.register(Utilisateur, UtilisateurAdmin)