from django.db import models

class MonthlyCount(models.Model):
    id_monthlycount = models.AutoField(primary_key=True)
    group_name = models.CharField(max_length=100)
    count = models.IntegerField()
    month = models.DateField()