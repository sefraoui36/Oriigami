from django.db import models
from authentication.models import Utilisateur

class IaRecommendations(models.Model):
    id_IA_recommendation = models.AutoField(primary_key=True)
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='ia_recommendations')
    score = models.FloatField()
    date = models.DateField()