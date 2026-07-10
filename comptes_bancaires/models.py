# comptes_bancaires/models.py
from django.db import models
from utilisateurs.models import Utilisateur

class CompteBancaire(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='comptes_bancaires')
    code_banque = models.CharField(max_length=20)
    code_ville = models.CharField(max_length=20)
    numero_compte = models.CharField(max_length=50)
    cle_rib = models.CharField(max_length=10)
    nom_banque = models.CharField(max_length=100)
    date_creation = models.DateField(auto_now_add=True)
    statut = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nom_banque} - {self.numero_compte}"