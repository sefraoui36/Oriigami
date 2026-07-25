# avis/admin.py
from django.contrib import admin
from .models import Avis

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ('id_avis', 'etudiant', 'enseignant', 'note', 'date_creation')
    list_filter = ('note', 'date_creation')
    search_fields = ('etudiant__nom', 'etudiant__prenom', 'enseignant__first_name', 'enseignant__last_name', 'commentaire')
    readonly_fields = ('date_creation', 'date_modification')
    ordering = ('-date_creation',)