# portefeuilles/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class Portefeuille(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portefeuilles')
    solde = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    devise = models.CharField(max_length=3, default='MAD')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    est_actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'
    
    def __str__(self):
        return f"Portefeuille de {self.utilisateur.get_full_name()} - {self.solde} {self.devise}"
    
    def recharger(self, montant):
        """Recharge le portefeuille"""
        self.solde += montant
        self.save()
        return self.solde
    
    def debiter(self, montant):
        """Débite le portefeuille si solde suffisant"""
        if self.solde >= montant:
            self.solde -= montant
            self.save()
            return True
        return False

class Transaction(models.Model):
    TYPE_CHOICES = [
        ('RECHARGE', 'Recharge'),
        ('PAIEMENT', 'Paiement'),
        ('REMBOURSEMENT', 'Remboursement'),
        ('ANNULATION', 'Annulation'),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('COMPLETE', 'Complété'),
        ('ECHEC', 'Échec'),
        ('ANNULE', 'Annulé'),
    ]
    
    portefeuille = models.ForeignKey(Portefeuille, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    methode_paiement = models.CharField(max_length=50, blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_completion = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=50, unique=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.montant} MAD - {self.get_statut_display()}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TRX-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)