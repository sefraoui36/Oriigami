# clients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Client

@login_required
def dashboard_parent(request):
    """Dashboard pour les parents"""
    # Récupérer le client parent connecté - utilisation de .first() pour éviter MultipleObjectsReturned
    client = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not client:
        # Si le parent n'existe pas, rediriger vers la création de profil
        messages.warning(request, "Vous n'avez pas encore de profil parent. Veuillez en créer un.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer tous les enfants du parent
    enfants = Client.objects.filter(parent=client, type_client='ETUDIANT')
    nombre_enfants = enfants.count()
    
    # Statistiques (à adapter selon vos modèles réels)
    forfaits_actifs = 3
    heures_restantes = 42
    seances_semaine = 4
    total_paye = 12450
    
    # Solde du portefeuille
    solde_portefeuille = 0
    try:
        from portefeuilles.models import Portefeuille
        portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
        if portefeuille:
            solde_portefeuille = portefeuille.solde
    except:
        pass
    
    # Prochaines séances (à adapter selon vos modèles)
    prochaines_seances = []
    
    # Données pour les enfants (à adapter selon vos modèles)
    enfants_data = []
    for enfant in enfants:
        # Essayer de récupérer les vraies données si disponibles
        heures_restantes_enfant = 12
        nombre_enseignants = 2
        prochaine_matiere = "Mathématiques"
        prochaine_date = "Aujourd'hui, 17:00"
        taux_progression = 75
        
        enfants_data.append({
            'id': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'etablissement': enfant.etablissement or 'Établissement',
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'photo': enfant.photo,
            'heures_restantes': heures_restantes_enfant,
            'nombre_enseignants': nombre_enseignants,
            'prochaine_seance': {
                'matiere': prochaine_matiere,
                'date_heure': prochaine_date
            },
            'taux_progression': taux_progression
        })
    
    context = {
        'client': client,
        'enfants': enfants_data,
        'nombre_enfants': nombre_enfants,
        'forfaits_actifs': forfaits_actifs,
        'heures_restantes': heures_restantes,
        'seances_semaine': seances_semaine,
        'total_paye': total_paye,
        'solde_portefeuille': solde_portefeuille,
        'prochaines_seances': prochaines_seances,
        'user': request.user,
    }
    
    return render(request, 'parent/dashboard.html', context)

@login_required
def creer_profil_parent(request):
    """Création du profil parent"""
    # Vérifier si l'utilisateur a déjà un profil parent
    client_existant = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    if client_existant:
        messages.info(request, "Vous avez déjà un profil parent.")
        return redirect('clients:dashboard_parent')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        
        # Créer le client parent
        client = Client.objects.create(
            utilisateur=request.user,
            nom=nom,
            prenom=prenom,
            telephone=telephone or '',
            adresse=adresse or '',
            type_client='PARENT'
        )
        
        messages.success(request, f"Profil parent créé avec succès ! Bienvenue {prenom} {nom}.")
        return redirect('clients:dashboard_parent')
    
    return render(request, 'clients/creer_profil_parent.html')