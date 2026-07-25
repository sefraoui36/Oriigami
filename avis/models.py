# avis/models.py
from django.db import models
from authentication.models import Utilisateur
from etudiants.models import Etudiant
from affectations.models import Affectation

class Avis(models.Model):
    id_avis = models.AutoField(primary_key=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='avis_donnes')
    enseignant = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='avis_recus')
    affectation = models.ForeignKey(Affectation, on_delete=models.CASCADE, related_name='avis')
    note = models.IntegerField(choices=[
        (1, '1 - Très mauvais'), 
        (2, '2 - Mauvais'), 
        (3, '3 - Moyen'), 
        (4, '4 - Bien'), 
        (5, '5 - Excellent')
    ])
    commentaire = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['etudiant', 'enseignant', 'affectation']
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Avis de {self.etudiant} pour {self.enseignant} - {self.note}/5"