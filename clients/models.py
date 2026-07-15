from django.db import models
from utilisateurs.models import Utilisateur

class Client(models.Model):
    # Énumération pour distinguer le type de client
    class TypeClient(models.TextChoices):
        PARENT = 'parent', 'Parent'
        ETUDIANT = 'etudiant', 'Étudiant'

    id_client = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='clients')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    adresse = models.TextField()
    
    # Nouvel attribut pour la distinction
    type_client = models.CharField(
        max_length=10,
        choices=TypeClient.choices,
        default=TypeClient.PARENT,
        help_text="Permet de distinguer si le client est un parent ou un étudiant indépendant"
    )

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_type_client_display()})"