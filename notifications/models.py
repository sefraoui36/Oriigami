# notifications/models.py
from django.db import models
from authentication.models import Utilisateur

class Notification(models.Model):
    TYPES_NOTIFICATION = [
        ('seance', 'Séance'),
        ('paiement', 'Paiement'),
        ('message', 'Message'),
        ('commentaire', 'Commentaire'),
        ('rappel', 'Rappel'),
        ('systeme', 'Système'),
        ('cours', 'Cours'),
    ]
    
    id_notification = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications_recues')
    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications_envoyees', null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPES_NOTIFICATION, default='systeme')
    titre = models.CharField(max_length=200)
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lue = models.BooleanField(default=False)
    url_action = models.CharField(max_length=200, null=True, blank=True)
    texte_action = models.CharField(max_length=50, null=True, blank=True)
    icone = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['-date_envoi']
    
    def __str__(self):
        return f"{self.titre} - {self.utilisateur.email}"
    
    def marquer_comme_lue(self):
        self.lue = True
        self.save()