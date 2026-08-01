# clients/models.py
from django.db import models
from django.conf import settings  

class Client(models.Model):
   
    class TypeClient(models.TextChoices):
        PARENT = 'parent', 'Parent'       
        ETUDIANT = 'etudiant', 'Étudiant'

    id_client = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='clients'
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    adresse = models.TextField()
    
    type_client = models.CharField(
        max_length=10,
        choices=TypeClient.choices,
        default=TypeClient.PARENT,
        help_text="Permet de distinguer si le client est un parent ou un étudiant indépendant"
    )
    
    # Relation parent-enfant
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='clients_enfants',
        limit_choices_to={'type_client': TypeClient.PARENT}
    )
    
    # Champs supplémentaires pour les enfants
    niveau_scolaire = models.CharField(max_length=50, null=True, blank=True)
    etablissement = models.CharField(max_length=100, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    
    # Photo de profil
    photo = models.ImageField(upload_to='clients/photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_type_client_display()})"
    
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}"
    
    @property
    def is_parent(self):
        return self.type_client == self.TypeClient.PARENT
    
    @property
    def is_etudiant(self):
        return self.type_client == self.TypeClient.ETUDIANT
    
    @property
    def enfants(self):
        """Retourne les enfants du parent"""
        if self.is_parent:
            return self.clients_enfants.all()
        return Client.objects.none()