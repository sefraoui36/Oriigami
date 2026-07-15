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

    # ===== AJOUTER CES LIGNES POUR ÉVITER LES CONFLITS =====
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='utilisateur_set',      # ← AJOUTER
        related_query_name='utilisateur',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='utilisateur_set',      # ← AJOUTER
        related_query_name='utilisateur',
    )

    def __str__(self):
        return self.username