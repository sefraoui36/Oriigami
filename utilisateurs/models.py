# utilisateurs/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Utilisateur(AbstractUser):
    cin = models.CharField(max_length=20, unique=True, null=True, blank=True)
    reference = models.CharField(max_length=50, null=True, blank=True)
    profile_photo = models.CharField(max_length=255, null=True, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=10, null=True, blank=True)
    telephone = models.CharField(max_length=20, null=True, blank=True)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    adresse_actuelle = models.TextField(null=True, blank=True)
    activite_actuelle = models.CharField(max_length=100, null=True, blank=True)
    rating = models.FloatField(default=0.0)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return self.username