# clients/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Client

@login_required
def dashboard_parent(request):
    """Dashboard pour les parents"""
    # Récupérer le client parent connecté
    client = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not client:
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
    
    # Prochaines séances
    prochaines_seances = []
    
    # Données pour les enfants
    enfants_data = []
    for enfant in enfants:
        enfants_data.append({
            'id': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'etablissement': enfant.etablissement or 'Établissement',
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'photo': enfant.photo,
            'heures_restantes': 12,
            'nombre_enseignants': 2,
            'prochaine_seance': {
                'matiere': 'Mathématiques',
                'date_heure': "Aujourd'hui, 17:00"
            },
            'taux_progression': 75
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
def liste_enfants(request):
    """Vue pour afficher la liste des enfants du parent"""
    # Récupérer le client parent connecté
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not parent:
        messages.warning(request, "Vous n'avez pas encore de profil parent.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer tous les enfants du parent
    enfants = Client.objects.filter(parent=parent, type_client='ETUDIANT')
    nombre_enfants = enfants.count()
    
    # Données enrichies pour chaque enfant
    enfants_data = []
    for enfant in enfants:
        # Calculer les heures restantes (exemple)
        heures_restantes = 20  # À remplacer par votre logique métier
        
        # Déterminer la couleur de la carte en fonction des heures
        statut_carte = ''
        if heures_restantes <= 10:
            statut_carte = 'border-error/20'
        elif heures_restantes <= 20:
            statut_carte = 'border-amber-500/20'
        else:
            statut_carte = 'border-primary/20'
        
        # Matières de l'enfant (exemple)
        matieres = ['Maths', 'Français']  # À remplacer par vos données
        
        # Calculer la moyenne (exemple)
        moyenne = 15.5  # À remplacer par votre logique
        
        enfants_data.append({
            'id': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'age': calculate_age(enfant.date_naissance) if enfant.date_naissance else '--',
            'etablissement': enfant.etablissement or 'Établissement',
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'photo': enfant.photo,
            'heures_restantes': heures_restantes,
            'heures_total': 40,  # À remplacer
            'matieres': matieres,
            'moyenne': moyenne,
            'nombre_enseignants': 2,  # À remplacer
            'statut_carte': statut_carte,
            'taux_progression': 75,  # À remplacer
            'prochaine_seance': {
                'matiere': 'Mathématiques',
                'date_heure': "Demain, 16:30"
            }
        })
    
    # Séances à venir (tous enfants confondus)
    prochaines_seances = get_prochaines_seances_parent(parent)
    
    # Statistiques de consommation
    stats_consommation = get_stats_consommation(enfants)
    
    # Recommandation
    recommandation = get_recommandation(enfants)
    
    context = {
        'parent': parent,
        'enfants': enfants_data,
        'nombre_enfants': nombre_enfants,
        'prochaines_seances': prochaines_seances,
        'stats_consommation': stats_consommation,
        'recommandation': recommandation,
        'user': request.user,
    }
    
    return render(request, 'parent/enfants.html', context)

def calculate_age(date_naissance):
    """Calcule l'âge à partir de la date de naissance"""
    if not date_naissance:
        return None
    today = timezone.now().date()
    return today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))

def get_prochaines_seances_parent(parent):
    """Récupère les prochaines séances pour tous les enfants du parent"""
    # Exemple de données statiques - À remplacer par vos modèles
    return [
        {
            'enfant': 'Ahmed',
            'initiales': 'AD',
            'matiere': 'Mathématiques',
            'enseignant': 'Dr. Robert M.',
            'date_heure': 'Demain, 16:30',
            'statut': 'Confirmé',
            'couleur_statut': 'emerald'
        },
        {
            'enfant': 'Sara',
            'initiales': 'SD',
            'matiere': 'Anglais Intensif',
            'enseignant': 'Sarah Jones',
            'date_heure': '24 oct, 10:00',
            'statut': 'Confirmé',
            'couleur_statut': 'emerald'
        },
        {
            'enfant': 'Lucas',
            'initiales': 'LD',
            'matiere': 'Français',
            'enseignant': 'Mme. Leclerc',
            'date_heure': '25 oct, 14:00',
            'statut': 'En attente',
            'couleur_statut': 'amber'
        }
    ]

def get_stats_consommation(enfants):
    """Récupère les statistiques de consommation par enfant"""
    # Exemple de données - À remplacer par vos modèles
    stats = []
    couleurs = ['primary', 'secondary', 'amber-500']
    for i, enfant in enumerate(enfants):
        stats.append({
            'prenom': enfant.prenom,
            'heures': 12 if i == 0 else (30 if i == 1 else 8),
            'couleur': couleurs[i % len(couleurs)]
        })
    return stats

def get_recommandation(enfants):
    """Génère une recommandation basée sur les données des enfants"""
    for enfant in enfants:
        if enfant.prenom == 'Lucas':
            return {
                'message': 'Le forfait de Lucas arrive à expiration. Activez le renouvellement automatique pour éviter toute interruption.',
                'type': 'warning'
            }
    return None

@login_required
def creer_profil_parent(request):
    """Création du profil parent"""
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

# clients/views.py - Ajouter cette fonction
@login_required
def ajouter_enfant(request):
    """Ajoute un enfant au parent connecté"""
    if request.method != 'POST':
        return redirect('clients:liste_enfants')
    
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    if not parent:
        messages.error(request, "Vous devez avoir un profil parent pour ajouter un enfant.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer les données du formulaire
    prenom = request.POST.get('prenom')
    nom = request.POST.get('nom')
    date_naissance = request.POST.get('date_naissance')
    niveau_scolaire = request.POST.get('niveau_scolaire')
    etablissement = request.POST.get('etablissement')
    
    if not prenom or not nom:
        messages.error(request, "Le prénom et le nom sont obligatoires.")
        return redirect('clients:liste_enfants')
    
    # Créer l'enfant
    enfant = Client.objects.create(
        utilisateur=request.user,
        type_client='ETUDIANT',
        nom=nom,
        prenom=prenom,
        telephone='',
        adresse=parent.adresse or '',
        parent=parent,
        niveau_scolaire=niveau_scolaire or '',
        etablissement=etablissement or '',
        date_naissance=date_naissance if date_naissance else None
    )
    
    messages.success(request, f"{prenom} {nom} a été ajouté avec succès !")
    return redirect('clients:liste_enfants')