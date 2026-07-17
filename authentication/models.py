# authentication/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Utilisateur(AbstractUser):
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    reference = models.CharField(max_length=50, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profils/', null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=10, null=True, blank=True, choices=[
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ])
    telephone = models.CharField(max_length=20, null=True, blank=True)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    adresse_actuelle = models.TextField(null=True, blank=True)
    activite_actuelle = models.CharField(max_length=100, null=True, blank=True)
    rating = models.FloatField(default=0.0)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"