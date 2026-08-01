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
        heures_restantes = 20
        
        # Déterminer la couleur de la carte en fonction des heures
        statut_carte = ''
        if heures_restantes <= 10:
            statut_carte = 'border-error/20'
        elif heures_restantes <= 20:
            statut_carte = 'border-amber-500/20'
        else:
            statut_carte = 'border-primary/20'
        
        # Matières de l'enfant (exemple)
        matieres = ['Maths', 'Français']
        
        # Calculer la moyenne (exemple)
        moyenne = 15.5
        
        enfants_data.append({
            'id_client': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'age': calculate_age(enfant.date_naissance) if enfant.date_naissance else '--',
            'etablissement': enfant.etablissement or 'Établissement',
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'photo': enfant.photo,
            'heures_restantes': heures_restantes,
            'heures_total': 40,
            'matieres': matieres,
            'moyenne': moyenne,
            'nombre_enseignants': 2,
            'statut_carte': statut_carte,
            'taux_progression': 75,
            'prochaine_seance': {
                'matiere': 'Mathématiques',
                'date_heure': "Demain, 16:30"
            }
        })
    
    # Séances à venir (tous enfants confondus)
    prochaines_seances = get_prochaines_seances_parent(parent, enfants)
    
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

def get_prochaines_seances_parent(parent, enfants):
    """Récupère les prochaines séances pour tous les enfants du parent"""
    prochaines_seances = []
    
    # Générer des séances dynamiquement pour chaque enfant
    matieres_exemples = ['Mathématiques', 'Français', 'Anglais', 'Physique-Chimie']
    enseignants_exemples = ['Dr. Robert M.', 'Sarah Jones', 'Mme. Leclerc', 'M. Martin']
    statuts_exemples = ['Confirmé', 'En attente', 'Confirmé', 'Confirmé']
    couleurs_exemples = ['emerald', 'amber', 'emerald', 'emerald']
    
    for i, enfant in enumerate(enfants):
        idx = i % len(matieres_exemples)
        prochaines_seances.append({
            'enfant': enfant.prenom,
            'initiales': f"{enfant.prenom[0]}{enfant.nom[0]}".upper(),
            'matiere': matieres_exemples[idx],
            'enseignant': enseignants_exemples[idx],
            'date_heure': f"{i+2} oct, {14 + i*2}:00",
            'statut': statuts_exemples[idx],
            'couleur_statut': couleurs_exemples[idx]
        })
    
    # Si pas d'enfants, retourner des exemples
    if not prochaines_seances:
        prochaines_seances = [
            {
                'enfant': 'Ahmed',
                'initiales': 'AD',
                'matiere': 'Mathématiques',
                'enseignant': 'Dr. Robert M.',
                'date_heure': 'Demain, 16:30',
                'statut': 'Confirmé',
                'couleur_statut': 'emerald'
            }
        ]
    
    return prochaines_seances

def get_stats_consommation(enfants):
    """Récupère les statistiques de consommation par enfant"""
    stats = []
    couleurs = ['primary', 'secondary', 'amber-500']
    heures = [12, 30, 8]
    
    for i, enfant in enumerate(enfants):
        stats.append({
            'prenom': enfant.prenom,
            'heures': heures[i % len(heures)],
            'couleur': couleurs[i % len(couleurs)]
        })
    
    if not stats:
        stats = [{'prenom': 'Aucun', 'heures': 0, 'couleur': 'primary'}]
    
    return stats

def get_recommandation(enfants):
    """Génère une recommandation basée sur les données des enfants"""
    for enfant in enfants:
        # Si un enfant a un nom qui commence par L (exemple)
        if enfant.prenom and enfant.prenom.startswith('L'):
            return {
                'message': f"Le forfait de {enfant.prenom} arrive à expiration. Activez le renouvellement automatique pour éviter toute interruption.",
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

# clients/views.py (AJOUTER cette fonction)

@login_required
def liste_enseignants(request):
    """Vue pour afficher la liste des enseignants des enfants du parent"""
    # Récupérer le client parent connecté
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not parent:
        messages.warning(request, "Vous n'avez pas encore de profil parent.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer tous les enfants du parent
    enfants = Client.objects.filter(parent=parent, type_client='ETUDIANT')
    nombre_enfants = enfants.count()
    
    # Récupérer les enseignants via les affectations
    from enseignants.models import Enseignant
    from affectations.models import Affectation
    from seances.models import Seance
    
    # Statistiques globales
    enseignants_actifs = Enseignant.objects.filter(
        utilisateur__in=Affectation.objects.filter(
            client__in=enfants,
            statut_affectation='active'
        ).values('rh__utilisateur')
    ).distinct().count()
    
    matieres_distinctes = Affectation.objects.filter(
        client__in=enfants,
        statut_affectation='active'
    ).values_list('matiere', flat=True).distinct().count()
    
    seances_semaine = Seance.objects.filter(
        affectation__client__in=enfants,
        date__gte=timezone.now().date(),
        date__lte=timezone.now().date() + timedelta(days=7),
        statut='prevue'
    ).count()
    
    # Structure de données pour les enfants et leurs enseignants
    enfants_enseignants = []
    
    for enfant in enfants:
        # Récupérer les affectations actives de l'enfant
        affectations = Affectation.objects.filter(
            client=enfant,
            statut_affectation='active'
        ).select_related('rh', 'rh__utilisateur')
        
        enseignants_list = []
        for aff in affectations:
            if aff.rh and aff.rh.utilisateur:
                enseignant = Enseignant.objects.filter(utilisateur=aff.rh.utilisateur).first()
                if enseignant:
                    # Récupérer la prochaine séance
                    prochaine_seance = Seance.objects.filter(
                        affectation=aff,
                        statut='prevue',
                        date__gte=timezone.now().date()
                    ).order_by('date', 'heure').first()
                    
                    # Compter les séances totales et terminées
                    total_seances = Seance.objects.filter(affectation=aff).count()
                    seances_terminees = Seance.objects.filter(affectation=aff, statut='termine').count()
                    
                    # Heures restantes (à adapter selon votre logique)
                    heures_restantes = aff.heures_restantes if aff.heures_restantes else 0
                    
                    enseignants_list.append({
                        'id': enseignant.id,
                        'nom': enseignant.utilisateur.last_name or 'Enseignant',
                        'prenom': enseignant.utilisateur.first_name or '',
                        'nom_complet': f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}".strip(),
                        'matiere': aff.matiere or 'Cours',
                        'photo': enseignant.utilisateur.photo if hasattr(enseignant.utilisateur, 'photo') else None,
                        'statut': 'Actif' if aff.statut_affectation == 'active' else 'Inactif',
                        'heures_restantes': heures_restantes,
                        'total_seances': total_seances,
                        'seances_terminees': seances_terminees,
                        'prochaine_seance': prochaine_seance,
                        'prochaine_date': prochaine_seance.date.strftime('%d/%m') if prochaine_seance else 'Aucune',
                        'prochaine_heure': prochaine_seance.heure.strftime('%H:%M') if prochaine_seance and prochaine_seance.heure else '--:--',
                        'progression': int((seances_terminees / total_seances * 100)) if total_seances > 0 else 0,
                        'experience': enseignant.experience if hasattr(enseignant, 'experience') else 'Non spécifié',
                        'diplome': enseignant.diplome if hasattr(enseignant, 'diplome') else 'Non spécifié',
                        'disponibilites': get_disponibilites_enseignant(enseignant),
                        'enfants_suivis': [enfant.prenom],
                    })
        
        enfants_enseignants.append({
            'id': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'photo': enfant.photo,
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'nombre_enseignants': len(enseignants_list),
            'enseignants': enseignants_list
        })
    
    # Tous les enseignants pour la vue détaillée
    tous_enseignants = []
    for item in enfants_enseignants:
        for enseignant in item['enseignants']:
            enseignant['enfant'] = item['prenom']
            tous_enseignants.append(enseignant)
    
    context = {
        'parent': parent,
        'enfants_enseignants': enfants_enseignants,
        'tous_enseignants': tous_enseignants,
        'enseignants_actifs': enseignants_actifs,
        'matieres_count': matieres_distinctes,
        'enfants_count': nombre_enfants,
        'seances_semaine': seances_semaine,
        'user': request.user,
    }
    
    return render(request, 'parent/enseignants.html', context)

def get_disponibilites_enseignant(enseignant):
    """Récupère les disponibilités d'un enseignant"""
    # À adapter selon votre modèle de disponibilités
    from disponibilites.models import Disponibilite
    try:
        disponibilites = Disponibilite.objects.filter(enseignant=enseignant)
        if disponibilites.exists():
            return disponibilites
    except:
        pass
    # Disponibilités par défaut
    return [
        {'jour': 'Lundi - Jeudi', 'heure': '17:00 - 20:00'},
        {'jour': 'Samedi', 'heure': '09:00 - 13:00'},
    ]

# clients/views.py (AJOUTER cette fonction)

@login_required
def liste_forfaits(request):
    """Vue pour afficher les forfaits du parent et de ses enfants"""
    from forfaits.models import Forfait
    from django.db.models import Sum
    
    # Récupérer le client parent connecté
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not parent:
        messages.warning(request, "Vous n'avez pas encore de profil parent.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer tous les enfants du parent
    enfants = Client.objects.filter(parent=parent, type_client='ETUDIANT')
    nombre_enfants = enfants.count()
    
    # Récupérer les forfaits du parent
    forfaits_parent = Forfait.objects.filter(utilisateur=request.user)
    
    # Récupérer les forfaits des enfants (via les affectations ou directement)
    forfaits_enfants = []
    heures_total_parent = 0
    heures_utilisees_parent = 0
    
    for enfant in enfants:
        # Récupérer les forfaits de l'enfant (à adapter selon votre modèle)
        # Exemple: forfaits_enfant = Forfait.objects.filter(enfant=enfant)
        # Pour l'exemple, on utilise des données simulées
        heures_total = 40
        heures_restantes = 20
        heures_utilisees = heures_total - heures_restantes
        
        forfaits_enfants.append({
            'enfant': enfant,
            'heures_total': heures_total,
            'heures_restantes': heures_restantes,
            'heures_utilisees': heures_utilisees,
            'pourcentage': int((heures_utilisees / heures_total * 100)) if heures_total > 0 else 0,
            'statut': 'Actif' if heures_restantes > 5 else 'Presque épuisé' if heures_restantes > 0 else 'Épuisé',
            'couleur_statut': 'green' if heures_restantes > 5 else 'amber' if heures_restantes > 0 else 'red'
        })
        
        heures_total_parent += heures_total
        heures_utilisees_parent += heures_utilisees
    
    # Statistiques globales
    pourcentage_global = int((heures_utilisees_parent / heures_total_parent * 100)) if heures_total_parent > 0 else 0
    
    # Forfaits disponibles (offres)
    offres_forfaits = get_offres_forfaits()
    
    # Recommandation
    recommandation = get_recommandation_forfait(forfaits_enfants)
    
    context = {
        'parent': parent,
        'enfants': enfants,
        'forfaits_enfants': forfaits_enfants,
        'nombre_enfants': nombre_enfants,
        'heures_total': heures_total_parent,
        'heures_utilisees': heures_utilisees_parent,
        'heures_restantes': heures_total_parent - heures_utilisees_parent,
        'pourcentage_global': pourcentage_global,
        'offres_forfaits': offres_forfaits,
        'recommandation': recommandation,
        'user': request.user,
    }
    
    return render(request, 'parent/forfaits.html', context)

def get_offres_forfaits():
    """Récupère les offres de forfaits disponibles"""
    return [
        {
            'id': 1,
            'nom': 'Pack Light',
            'description': 'Idéal pour un soutien ponctuel',
            'heures': 10,
            'prix': 1200,
            'prix_par_heure': 120,
            'couleur': 'primary',
            'icone': 'lightbulb',
            'popularite': 'standard',
            'features': ['10 Heures de cours', 'Tous niveaux']
        },
        {
            'id': 2,
            'nom': 'Pack Standard',
            'description': 'Le meilleur équilibre progrès/prix',
            'heures': 20,
            'prix': 2200,
            'prix_par_heure': 110,
            'couleur': 'primary',
            'icone': 'rocket_launch',
            'popularite': 'populaire',
            'features': ['20 Heures de cours', 'Rapport personnalisé']
        },
        {
            'id': 3,
            'nom': 'Pack Premium',
            'description': 'Accompagnement intensif complet',
            'heures': 40,
            'prix': 4000,
            'prix_par_heure': 100,
            'couleur': 'secondary',
            'icone': 'workspace_premium',
            'popularite': 'premium',
            'features': ['40 Heures de cours', 'Suivi personnalisé', 'Rapports détaillés']
        }
    ]

def get_recommandation_forfait(forfaits_enfants):
    """Génère une recommandation basée sur les forfaits des enfants"""
    for f in forfaits_enfants:
        if f['heures_restantes'] < 5 and f['heures_restantes'] > 0:
            return {
                'message': f"Le forfait de {f['enfant'].prenom} est presque épuisé ({f['heures_restantes']}h restantes). Pensez à le recharger.",
                'type': 'warning',
                'enfant': f['enfant'].prenom
            }
        elif f['heures_restantes'] <= 0:
            return {
                'message': f"Le forfait de {f['enfant'].prenom} est épuisé. Veuillez recharger pour continuer les cours.",
                'type': 'danger',
                'enfant': f['enfant'].prenom
            }
    return None

# clients/views.py (AJOUTER cette fonction)

@login_required
def acheter_forfait(request):
    """Acheter un forfait pour un enfant"""
    if request.method != 'POST':
        return redirect('clients:liste_forfaits')
    
    from forfaits.models import Forfait
    
    enfant_id = request.POST.get('enfant')
    forfait_id = request.POST.get('forfait')
    
    if not enfant_id or not forfait_id:
        messages.error(request, "Veuillez sélectionner un enfant et un forfait.")
        return redirect('clients:liste_forfaits')
    
    # Récupérer l'enfant
    enfant = Client.objects.filter(id_client=enfant_id, type_client='ETUDIANT').first()
    if not enfant:
        messages.error(request, "Enfant non trouvé.")
        return redirect('clients:liste_forfaits')
    
    # Vérifier que l'enfant appartient bien au parent
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    if enfant.parent != parent:
        messages.error(request, "Vous n'êtes pas autorisé à acheter un forfait pour cet enfant.")
        return redirect('clients:liste_forfaits')
    
    # Récupérer les détails du forfait
    offres = get_offres_forfaits()
    offre = None
    for o in offres:
        if o['id'] == int(forfait_id):
            offre = o
            break
    
    if not offre:
        messages.error(request, "Forfait non trouvé.")
        return redirect('clients:liste_forfaits')
    
    # Créer le forfait
    forfait = Forfait.objects.create(
        utilisateur=request.user,
        nombre_heure=offre['heures'],
        prix=offre['prix'],
        # Ajoutez d'autres champs selon votre modèle
    )
    
    messages.success(request, f"Forfait {offre['nom']} acheté avec succès pour {enfant.prenom} !")
    return redirect('clients:liste_forfaits')