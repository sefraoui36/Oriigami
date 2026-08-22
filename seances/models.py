# seances/models.py
from django.db import models
from affectations.models import Affectation

class Seance(models.Model):
    STATUT_SEANCE = [
        ('prevue', 'Prévue'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
        ('reportee', 'Reportée'),
    ]
    
    affectation = models.ForeignKey(Affectation, on_delete=models.CASCADE, related_name='seances')
    date = models.DateField()
    heure = models.TimeField()
    duree = models.CharField(max_length=50)
    qualite = models.CharField(max_length=100, null=True, blank=True)
    type_seance = models.CharField(max_length=100)
    statut = models.CharField(max_length=20, choices=STATUT_SEANCE, default='prevue')

    def __str__(self):
        return f"Séance du {self.date} - {self.affectation.matiere} ({self.statut})"


class RappelSeance(models.Model):
    CANAL_CHOICES = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
    ]
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('envoye', 'Envoyé'),
        ('echec', 'Échec'),
        ('annule', 'Annulé'),
    ]

    seance = models.OneToOneField(Seance, on_delete=models.CASCADE, related_name='rappel')
    canal = models.CharField(max_length=10, choices=CANAL_CHOICES)
    telephone = models.CharField(max_length=20)
    date_envoi_prevue = models.DateTimeField()
    statut = models.CharField(max_length=15, choices=STATUT_CHOICES, default='en_attente')
    date_envoi_reelle = models.DateTimeField(null=True, blank=True)
    erreur = models.TextField(blank=True, default='')

    class Meta:
        indexes = [
            models.Index(fields=['statut', 'date_envoi_prevue']),
        ]

    def __str__(self):
        return f"Rappel {self.canal} - {self.seance} ({self.statut})"