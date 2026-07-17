# clients/admin.py
from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'telephone', 'type_client', 'utilisateur')
    search_fields = ('nom', 'prenom', 'telephone')
    list_filter = ('type_client',)