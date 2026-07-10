# portefeuilles/admin.py
from django.contrib import admin
from .models import Portefeuille

@admin.register(Portefeuille)
class PortefeuilleAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'solde']
    search_fields = ['utilisateur__username']