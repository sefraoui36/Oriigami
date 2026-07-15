from django.db import models
from utilisateurs.models import Utilisateur

class Notification(models.Model):
    id_notification = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    titre = models.CharField(max_length=150)
    message = models.TextField()
    date_envoi = models.DateField(auto_now_add=True)
    lecture = models.BooleanField(default=False)