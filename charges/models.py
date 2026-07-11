from django.db import models

class Charges(models.Model):
    id_charge = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=150)
    date = models.DateField()
    montant = models.FloatField()