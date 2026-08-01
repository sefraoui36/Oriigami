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

# clients/views.py (AJOUTER cette fonction)

@login_required
def liste_seances(request):
    """Vue pour afficher les séances des enfants du parent"""
    from seances.models import Seance
    from affectations.models import Affectation
    from enseignants.models import Enseignant
    from django.utils import timezone
    from datetime import datetime, timedelta
    import calendar
    
    # Récupérer le client parent connecté
    parent = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not parent:
        messages.warning(request, "Vous n'avez pas encore de profil parent.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer tous les enfants du parent
    enfants = Client.objects.filter(parent=parent, type_client='ETUDIANT')
    
    # Récupérer toutes les séances des enfants
    affectations = Affectation.objects.filter(
        client__in=enfants,
        statut_affectation='active'
    )
    
    seances = Seance.objects.filter(
        affectation__in=affectations
    ).order_by('date', 'heure')
    
    # Séances à venir (à partir d'aujourd'hui)
    aujourdhui = timezone.now().date()
    seances_a_venir = seances.filter(date__gte=aujourdhui, statut__in=['prevue', 'en_cours'])
    
    # Séances passées
    seances_passees = seances.filter(date__lt=aujourdhui, statut='termine')
    
    # Statistiques
    total_seances = seances.count()
    seances_semaine = seances.filter(
        date__gte=aujourdhui,
        date__lte=aujourdhui + timedelta(days=7)
    ).count()
    
    # Données pour le calendrier
    mois_courant = timezone.now().month
    annee_courante = timezone.now().year
    jours_semaine = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
    
    # Générer les jours du mois
    calendrier_mois = []
    for jour in range(1, calendar.monthrange(annee_courante, mois_courant)[1] + 1):
        date_jour = datetime(annee_courante, mois_courant, jour).date()
        seances_jour = seances.filter(date=date_jour)
        calendrier_mois.append({
            'jour': jour,
            'date': date_jour,
            'est_aujourdhui': date_jour == aujourdhui,
            'a_seances': seances_jour.exists(),
            'seances': seances_jour
        })
    
    # Préparer les données des séances pour le template
    seances_data = []
    for seance in seances_a_venir[:10]:  # Limiter aux 10 prochaines
        enfant = seance.affectation.client if seance.affectation else None
        enseignant = None
        if seance.affectation and seance.affectation.rh:
            enseignant = Enseignant.objects.filter(utilisateur=seance.affectation.rh.utilisateur).first()
        
        # Déterminer le statut de la séance
        statut_display = seance.get_statut_display() if hasattr(seance, 'get_statut_display') else seance.statut
        couleur_statut = 'green' if seance.statut == 'termine' else 'orange' if seance.statut == 'prevue' else 'blue'
        
        # Vérifier si c'est une recommandation IA
        est_ia = seance.est_ia if hasattr(seance, 'est_ia') else False
        
        # Matière
        matiere = seance.affectation.matiere if seance.affectation else 'Cours'
        
        # Durée
        duree = seance.duree or '1h00'
        
        # Enseignant
        nom_enseignant = "Enseignant"
        if enseignant and enseignant.utilisateur:
            nom_enseignant = f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}".strip() or "Enseignant"
        
        seances_data.append({
            'id': seance.id,
            'enfant': enfant.prenom if enfant else 'Inconnu',
            'enfant_initial': enfant.prenom[0].upper() if enfant else '?',
            'matiere': matiere,
            'matiere_icone': get_matiere_icone(matiere),
            'couleur_matiere': get_matiere_couleur(matiere),
            'enseignant': nom_enseignant,
            'enseignant_photo': enseignant.utilisateur.photo if enseignant and hasattr(enseignant.utilisateur, 'photo') else None,
            'date': seance.date.strftime('%d/%m/%Y'),
            'date_affichage': get_date_affichage(seance.date),
            'heure': seance.heure.strftime('%H:%M') if seance.heure else '--:--',
            'heure_fin': (seance.heure + timedelta(hours=1)).strftime('%H:%M') if seance.heure else '--:--',
            'duree': duree,
            'statut': statut_display,
            'couleur_statut': couleur_statut,
            'est_ia': est_ia,
            'mode': 'En visio' if seance.en_visio else 'Domicile',
            'mode_icone': 'videocam' if seance.en_visio else 'location_on',
            'lieu': seance.lieu or ('Lien visio' if seance.en_visio else 'À définir'),
            'est_termine': seance.statut == 'termine',
            'peut_rejoindre': seance.statut in ['prevue', 'en_cours'],
            'peut_modifier': seance.statut in ['prevue', 'en_attente'],
            'peut_annuler': seance.statut in ['prevue', 'en_attente'],
            'seance_id': seance.id,
        })
    
    # Séances passées pour l'historique
    historique_data = []
    for seance in seances_passees[:5]:
        enfant = seance.affectation.client if seance.affectation else None
        enseignant = None
        if seance.affectation and seance.affectation.rh:
            enseignant = Enseignant.objects.filter(utilisateur=seance.affectation.rh.utilisateur).first()
        
        matiere = seance.affectation.matiere if seance.affectation else 'Cours'
        nom_enseignant = "Enseignant"
        if enseignant and enseignant.utilisateur:
            nom_enseignant = f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}".strip() or "Enseignant"
        
        historique_data.append({
            'matiere': matiere,
            'matiere_icone': get_matiere_icone(matiere),
            'couleur_matiere': get_matiere_couleur(matiere),
            'enfant': enfant.prenom if enfant else 'Inconnu',
            'enseignant': nom_enseignant,
            'date': seance.date.strftime('%d %b.'),
            'heure': seance.heure.strftime('%H:%M') if seance.heure else '--:--',
            'duree': seance.duree or '1h00',
            'statut': 'Complétée',
            'peut_voir_rapport': True,
        })
    
    # Timeline de la journée
    timeline_data = []
    today_seances = seances.filter(date=aujourdhui).order_by('heure')
    for seance in today_seances:
        enfant = seance.affectation.client if seance.affectation else None
        matiere = seance.affectation.matiere if seance.affectation else 'Cours'
        enseignant = None
        if seance.affectation and seance.affectation.rh:
            enseignant = Enseignant.objects.filter(utilisateur=seance.affectation.rh.utilisateur).first()
        
        nom_enseignant = "Enseignant"
        if enseignant and enseignant.utilisateur:
            nom_enseignant = f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}".strip() or "Enseignant"
        
        timeline_data.append({
            'heure': seance.heure.strftime('%H:%M') if seance.heure else '--:--',
            'duree': seance.duree or '1h00',
            'matiere': matiere,
            'enfant': enfant.prenom if enfant else 'Inconnu',
            'enseignant': nom_enseignant,
            'couleur': get_matiere_couleur(matiere),
            'est_termine': seance.statut == 'termine',
        })
    
    # Optimisation IA (simulée)
    optimisation = {
        'score': 92,
        'message': 'Votre planning actuel est optimisé. Cependant, 2 créneaux pourraient être regroupés pour économiser du temps de transport.'
    }
    
    context = {
        'parent': parent,
        'enfants': enfants,
        'seances': seances_data,
        'seances_semaine': seances_semaine,
        'total_seances': total_seances,
        'calendrier_mois': calendrier_mois,
        'jour_semaine': jours_semaine,
        'mois_courant': mois_courant,
        'annee_courante': annee_courante,
        'aujourdhui': aujourdhui,
        'timeline_data': timeline_data,
        'historique_data': historique_data,
        'optimisation': optimisation,
        'user': request.user,
    }
    
    return render(request, 'parent/seances.html', context)

def get_date_affichage(date):
    """Retourne une date formatée pour l'affichage"""
    aujourdhui = timezone.now().date()
    if date == aujourdhui:
        return "Aujourd'hui"
    elif date == aujourdhui + timedelta(days=1):
        return "Demain"
    elif date < aujourdhui:
        return "Passé"
    else:
        jours_semaine = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        return jours_semaine[date.weekday()]

def get_matiere_icone(matiere):
    """Retourne l'icône correspondante à la matière"""
    icones = {
        'math': 'calculate',
        'mathématiques': 'calculate',
        'français': 'menu_book',
        'anglais': 'translate',
        'physique': 'biotech',
        'chimie': 'science',
        'histoire': 'history',
        'géo': 'public',
        'web': 'code',
        'informatique': 'code',
        'programmation': 'code',
        'art': 'palette',
        'musique': 'music_note',
        'sport': 'sports',
    }
    if matiere:
        for key, icon in icones.items():
            if key in matiere.lower():
                return icon
    return 'school'

def get_matiere_couleur(matiere):
    """Retourne la couleur correspondante à la matière"""
    couleurs = {
        'math': 'primary',
        'mathématiques': 'primary',
        'français': 'tertiary',
        'anglais': 'secondary',
        'physique': 'blue',
        'chimie': 'purple',
        'histoire': 'orange',
        'géo': 'green',
        'web': 'indigo',
        'informatique': 'indigo',
        'programmation': 'indigo',
        'art': 'pink',
        'musique': 'teal',
        'sport': 'emerald',
    }
    if matiere:
        for key, color in couleurs.items():
            if key in matiere.lower():
                return color
    return 'primary'

# clients/views.py (AJOUTER cette fonction)

@login_required
def profil_parent(request):
    """Vue pour afficher et modifier le profil du parent"""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm
    
    # Récupérer le client parent connecté
    client = Client.objects.filter(utilisateur=request.user, type_client='PARENT').first()
    
    if not client:
        messages.warning(request, "Vous n'avez pas encore de profil parent. Veuillez en créer un.")
        return redirect('clients:creer_profil_parent')
    
    # Récupérer les enfants du parent
    enfants = Client.objects.filter(parent=client, type_client='ETUDIANT')
    
    # Récupérer les forfaits actifs (à adapter)
    from forfaits.models import Forfait
    forfaits_actifs = Forfait.objects.filter(utilisateur=request.user).count()
    
    # Récupérer le solde du portefeuille
    solde_portefeuille = 0
    try:
        from portefeuilles.models import Portefeuille
        portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
        if portefeuille:
            solde_portefeuille = portefeuille.solde
    except:
        pass
    
    # Heures restantes (à adapter)
    heures_restantes = 42
    heures_total = 60
    
    # Dernières transactions (à adapter)
    dernieres_transactions = []
    try:
        from portefeuilles.models import Transaction
        transactions = Transaction.objects.filter(
            portefeuille__utilisateur=request.user
        ).order_by('-date_creation')[:3]
        for t in transactions:
            dernieres_transactions.append({
                'date': t.date_creation.strftime('%d %b %Y'),
                'description': t.description,
                'montant': f"{t.montant:.2f} €",
                'statut': 'Payé' if t.statut == 'COMPLETE' else 'En attente'
            })
    except:
        pass
    
    # Prochain cours
    prochain_cours = None
    try:
        from seances.models import Seance
        from affectations.models import Affectation
        from datetime import datetime, timedelta
        
        affectations = Affectation.objects.filter(
            client__in=enfants,
            statut_affectation='active'
        )
        prochaine_seance = Seance.objects.filter(
            affectation__in=affectations,
            date__gte=datetime.now().date(),
            statut='prevue'
        ).order_by('date', 'heure').first()
        
        if prochaine_seance:
            enseignant = None
            if prochaine_seance.affectation and prochaine_seance.affectation.rh:
                from enseignants.models import Enseignant
                enseignant = Enseignant.objects.filter(
                    utilisateur=prochaine_seance.affectation.rh.utilisateur
                ).first()
            
            prochain_cours = {
                'enseignant': f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}" if enseignant and enseignant.utilisateur else 'Enseignant',
                'matiere': prochaine_seance.affectation.matiere if prochaine_seance.affectation else 'Cours',
                'enfant': prochaine_seance.affectation.client.prenom if prochaine_seance.affectation and prochaine_seance.affectation.client else 'Enfant',
                'date': prochaine_seance.date.strftime('%d/%m/%Y'),
                'heure': prochaine_seance.heure.strftime('%H:%M') if prochaine_seance.heure else '--:--',
                'duree': prochaine_seance.duree or '1h00'
            }
    except:
        pass
    
    # Gestion du formulaire de modification du profil
    if request.method == 'POST':
        # Récupérer les données modifiées
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        date_naissance = request.POST.get('date_naissance')
        
        # Mettre à jour le client
        if nom:
            client.nom = nom
        if prenom:
            client.prenom = prenom
        if telephone:
            client.telephone = telephone
        if adresse:
            client.adresse = adresse
        if date_naissance:
            client.date_naissance = date_naissance
        
        client.save()
        
        # Mettre à jour l'utilisateur
        user = request.user
        if prenom:
            user.first_name = prenom
        if nom:
            user.last_name = nom
        user.save()
        
        messages.success(request, "Votre profil a été mis à jour avec succès !")
        return redirect('clients:profil_parent')
    
    # Données pour le template
    enfants_data = []
    for enfant in enfants:
        # Récupérer les matières de l'enfant (à adapter)
        matieres = []
        try:
            from affectations.models import Affectation
            affectations = Affectation.objects.filter(
                client=enfant,
                statut_affectation='active'
            )
            for aff in affectations:
                if aff.matiere:
                    matieres.append(aff.matiere)
        except:
            pass
        
        enfants_data.append({
            'id': enfant.id_client,
            'prenom': enfant.prenom,
            'nom': enfant.nom,
            'niveau': enfant.niveau_scolaire or 'Niveau',
            'matieres': matieres[:3] if matieres else ['Mathématiques', 'Français'],
            'statut': 'Actif'
        })
    
    # Préférences du système
    preferences = {
        'langue': 'Français',
        'fuseau_horaire': 'Europe/Paris (UTC+1)',
        'format_date': 'DD/MM/YYYY'
    }
    
    context = {
        'client': client,
        'user': request.user,
        'enfants': enfants_data,
        'forfaits_actifs': forfaits_actifs,
        'solde_portefeuille': solde_portefeuille,
        'heures_restantes': heures_restantes,
        'heures_total': heures_total,
        'dernieres_transactions': dernieres_transactions,
        'prochain_cours': prochain_cours,
        'preferences': preferences,
        'nombre_enfants': len(enfants_data),
    }
    
    return render(request, 'parent/profil.html', context)