# portefeuilles/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from .models import Portefeuille, Transaction
from decimal import Decimal

@login_required
def mon_portefeuille(request):
    """Vue principale du portefeuille"""
    
    # ✅ Utiliser request.user directement car le modèle utilise settings.AUTH_USER_MODEL
    try:
        portefeuille = Portefeuille.objects.get(utilisateur=request.user)
    except Portefeuille.DoesNotExist:
        portefeuille = Portefeuille.objects.create(
            utilisateur=request.user,
            solde=0.00,
            est_actif=True
        )
    
    # Statistiques
    transactions = portefeuille.transactions.filter(statut='COMPLETE')
    total_recharge = transactions.filter(type='RECHARGE').aggregate(
        total=Sum('montant')
    )['total'] or Decimal('0.00')
    
    total_depense = transactions.filter(type='PAIEMENT').aggregate(
        total=Sum('montant')
    )['total'] or Decimal('0.00')
    
    # Dernières transactions
    dernieres_transactions = portefeuille.transactions.all().order_by('-date_creation')[:10]
    
    # Total heures (simulé - à adapter selon votre logique)
    total_heures = 120
    
    # Hauteurs pour le graphique (exemple)
    hauteurs_graphique = [40, 60, 50, 85, 55, 80]
    
    context = {
        'portefeuille': portefeuille,
        'total_recharge': total_recharge,
        'total_depense': total_depense,
        'dernieres_transactions': dernieres_transactions,
        'total_heures': total_heures,
        'hauteurs_graphique': hauteurs_graphique,
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
    }
    
    return render(request, 'parent/portefeuille.html', context)


@login_required
def recharger_portefeuille(request):
    """Recharge le portefeuille"""
    
    if request.method == 'POST':
        montant = request.POST.get('montant')
        methode = request.POST.get('methode_paiement', 'Carte Bancaire')
        
        try:
            montant = Decimal(montant)
            if montant <= 0:
                messages.error(request, "Le montant doit être supérieur à 0")
                return redirect('portefeuilles:mon_portefeuille')
            
            portefeuille = Portefeuille.objects.get(utilisateur=request.user)
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                portefeuille=portefeuille,
                type='RECHARGE',
                montant=montant,
                description=f"Rechargement de {montant} MAD",
                methode_paiement=methode,
                statut='COMPLETE',
                date_completion=timezone.now()
            )
            
            # Recharger le portefeuille (utilise la méthode du modèle)
            portefeuille.recharger(montant)
            
            messages.success(request, f"Votre portefeuille a été rechargé de {montant} MAD")
            return redirect('portefeuilles:mon_portefeuille')
            
        except Portefeuille.DoesNotExist:
            messages.error(request, "Portefeuille non trouvé")
            return redirect('portefeuilles:mon_portefeuille')
        except Exception as e:
            messages.error(request, f"Erreur lors du rechargement: {str(e)}")
            return redirect('portefeuilles:mon_portefeuille')
    
    return redirect('portefeuilles:mon_portefeuille')


@login_required
def transactions_api(request):
    """API pour récupérer les transactions en JSON"""
    
    portefeuille = get_object_or_404(Portefeuille, utilisateur=request.user)
    transactions = portefeuille.transactions.all().order_by('-date_creation')
    
    data = []
    for t in transactions:
        data.append({
            'date': t.date_creation.strftime('%d %b, %Y'),
            'heure': t.date_creation.strftime('%H:%M'),
            'type': t.get_type_display(),
            'description': t.description,
            'montant': str(t.montant),
            'methode': t.methode_paiement or 'N/A',
            'statut': t.get_statut_display(),
            'statut_class': t.statut.lower(),
        })
    
    return JsonResponse({'transactions': data})