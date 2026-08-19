# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg
from .forms import InscriptionForm, ConnexionForm
from clients.models import Client
from enfants.models import Enfant
from etudiants.models import Etudiant
from seances.models import Seance
from affectations.models import Affectation
from notifications.models import Notification
from forfaits.models import Forfait
from enseignants.models import Enseignant
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse


def inscription(request):
    """
    Page d'inscription - Gère Parent ET Étudiant
    - Parent : crée son compte + ses enfants (sans compte)
    - Étudiant : crée son compte (sans choix de parent)
    """
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            type_client = request.POST.get('type_client', 'parent').lower()
            print(f"🔍 [DEBUG] type_client reçu: {type_client}")
            
            # Créer le client
            client = Client.objects.create(
                utilisateur=user,
                nom=form.cleaned_data['nom'],
                prenom=form.cleaned_data['prenom'],
                telephone=form.cleaned_data.get('telephone', ''),
                adresse=form.cleaned_data.get('adresse', ''),
                type_client=type_client
            )
            print(f"✅ [DEBUG] Client créé: {client.id_client} - Type: {client.type_client}")
            
            # ============================================
            # 🔥 CAS PARENT : Créer les enfants
            # ============================================
            if type_client == 'parent':
                noms_enfants = request.POST.getlist('nom_enfant[]')
                prenoms_enfants = request.POST.getlist('prenom_enfant[]')
                niveaux_enfants = request.POST.getlist('niveau_enfant[]')
                etablissements_enfants = request.POST.getlist('etablissement_enfant[]')
                
                for i in range(len(noms_enfants)):
                    if noms_enfants[i] and prenoms_enfants[i]:
                        Client.objects.create(
                            utilisateur=user,
                            type_client='etudiant',
                            nom=noms_enfants[i],
                            prenom=prenoms_enfants[i],
                            telephone='',
                            adresse='',
                            parent=client,
                            niveau_scolaire=niveaux_enfants[i] if i < len(niveaux_enfants) else '',
                            etablissement=etablissements_enfants[i] if i < len(etablissements_enfants) else ''
                        )
                        print(f"✅ [DEBUG] Enfant créé: {prenoms_enfants[i]} {noms_enfants[i]}")
                
                messages.success(request, "✅ Compte parent créé avec succès !")
                print("🔄 [DEBUG] Redirection vers connexion")
                return redirect('authentication:connexion')
            
            # ============================================
            # 🔥 CAS ÉTUDIANT (sans choix de parent)
            # ============================================
            elif type_client == 'etudiant':
                # Récupérer les informations supplémentaires de l'étudiant
                niveau_etude = request.POST.get('niveau_etude', '')
                etablissement = request.POST.get('etablissement', '')
                
                # Mettre à jour les informations de l'étudiant
                client.niveau_scolaire = niveau_etude
                client.etablissement = etablissement
                client.save()
                
                messages.success(request, "✅ Compte étudiant créé avec succès !")
                print("🔄 [DEBUG] Redirection vers connexion")
                return redirect('authentication:connexion')
            
            # Cas par défaut (normalement jamais atteint)
            messages.success(request, "Inscription réussie ! Veuillez vous connecter.")
            print("🔄 [DEBUG] Redirection vers connexion (défaut)")
            return redirect('authentication:connexion')
            
        else:
            print("❌ [DEBUG] Formulaire invalide")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = InscriptionForm()
    
    return render(request, 'clients/inscription.html', {
        'form': form,
    })


def connexion(request):
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bonjour {user.first_name} ! Content de vous revoir.")
            
            # Récupérer le client
            client = Client.objects.filter(utilisateur=user).first()
            print(f"🔍 [DEBUG] Client trouvé: {client}")
            if client:
                print(f"🔍 [DEBUG] Type client: {client.type_client}")
            
            # 🔥 REDIRECTION CORRECTE selon le type de client
            if client:
                if client.type_client == 'parent':
                    print("👉 [DEBUG] Redirection vers dashboard_parent")
                    return redirect('clients:dashboard_parent')
                elif client.type_client == 'etudiant':
                    print("👉 [DEBUG] Redirection vers authentication:dashboard")
                    return redirect('authentication:dashboard')
                elif client.type_client == 'enseignant':
                    print("👉 [DEBUG] Redirection vers dashboard_enseignant")
                    return redirect('enseignants:dashboard')
            
            # Par défaut, rediriger vers le dashboard étudiant
            print("👉 [DEBUG] Redirection par défaut vers authentication:dashboard")
            return redirect('authentication:dashboard')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
    else:
        form = ConnexionForm()
    
    return render(request, 'clients/connexion.html', {'form': form})


@login_required
def deconnexion(request):
    logout(request)
    messages.info(request, "Vous êtes déconnecté. À bientôt !")
    return redirect('authentication:connexion')


@login_required
def dashboard(request):
    """
    Dashboard étudiant
    Affiche les informations de l'étudiant, ses cours, ses séances, etc.
    """
    user = request.user
    
    # Récupérer le client
    client = Client.objects.filter(utilisateur=user).first()
    
    # 🔥 Si c'est un parent, rediriger vers le dashboard parent
    if client and client.type_client == 'parent':
        print("👉 [DEBUG] Parent détecté dans dashboard, redirection vers clients:dashboard_parent")
        return redirect('clients:dashboard_parent')
    
    # 🔥 Si c'est un enseignant, rediriger vers le dashboard enseignant
    if client and client.type_client == 'enseignant':
        print("👉 [DEBUG] Enseignant détecté dans dashboard")
        return render(request, 'enseignants/dashboard.html', {'user': user, 'client': client})
    
    # ============================================
    # 🔥 DASHBOARD ÉTUDIANT
    # ============================================
    
    # 🔥 Récupérer le parent de l'étudiant (peut être None)
    parent = client.parent if client else None
    
    # Récupérer les affectations de l'étudiant
    affectations = Affectation.objects.filter(
        utilisateur=user,  # 🔥 L'utilisateur de l'étudiant
        statut_affectation='active'
    )
    
    # Statistiques des cours
    cours_actifs = affectations.count()
    
    # Récupérer les séances de l'étudiant
    seances_etudiant = Seance.objects.filter(
        affectation__in=affectations
    )
    cours_termines = seances_etudiant.filter(statut='termine').count()
    
    # Heures restantes (à partir du forfait)
    heures_restantes = 0
    try:
        forfait = Forfait.objects.filter(utilisateur=user).first()
        if forfait:
            heures_restantes = forfait.nombre_heure
    except:
        pass
    
    # Moyenne générale
    moyenne_generale = 0
    try:
        notes = [s.qualite for s in seances_etudiant if s.qualite]
        if notes:
            moyenne_generale = sum(notes) / len(notes)
    except:
        pass
    
    # Liste des cours
    cours_list = []
    for aff in affectations[:3]:
        total_seances = Seance.objects.filter(affectation=aff).count()
        seances_terminees = Seance.objects.filter(affectation=aff, statut='termine').count()
        progression = int((seances_terminees / total_seances * 100)) if total_seances > 0 else 0
        
        professeur = "Enseignant"
        if aff.rh:
            try:
                enseignant = Enseignant.objects.filter(utilisateur=aff.rh.utilisateur).first()
                if enseignant and enseignant.utilisateur:
                    professeur = f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}"
            except:
                pass
        
        cours_list.append({
            'nom': aff.matiere or 'Cours',
            'professeur': professeur,
            'seances_restantes': int(aff.heures_restantes) if aff.heures_restantes else 0,
            'progression': progression,
            'icone': get_matiere_icone(aff.matiere),
            'couleur': get_matiere_couleur(aff.matiere)
        })
    
    if not cours_list:
        cours_list = []
    
    # Prochaines séances
    prochaines_seances = []
    try:
        seances = Seance.objects.filter(
            affectation__in=affectations,
            statut='prevue',
            date__gte=timezone.now().date()
        ).order_by('date', 'heure')[:3]
        
        for seance in seances:
            jour = seance.date.strftime('%a')
            jours_fr = {
                'Mon': 'Lun', 'Tue': 'Mar', 'Wed': 'Mer', 
                'Thu': 'Jeu', 'Fri': 'Ven', 'Sat': 'Sam', 'Sun': 'Dim'
            }
            jour_fr = jours_fr.get(jour, jour)
            
            matiere = seance.affectation.matiere if seance.affectation else 'Cours'
            heure = seance.heure.strftime('%H:%M') if seance.heure else '--:--'
            duree = seance.duree if seance.duree else '1h'
            
            professeur = "Enseignant"
            if seance.affectation and seance.affectation.rh:
                try:
                    enseignant = Enseignant.objects.filter(utilisateur=seance.affectation.rh.utilisateur).first()
                    if enseignant and enseignant.utilisateur:
                        professeur = f"{enseignant.utilisateur.first_name} {enseignant.utilisateur.last_name}"
                except:
                    pass
            
            prochaines_seances.append({
                'jour': jour_fr,
                'date': seance.date.strftime('%d'),
                'matiere': matiere,
                'heure': f"{heure} - {duree}",
                'professeur': professeur,
                'couleur': get_matiere_couleur(matiere)
            })
    except:
        pass
    
    # Notifications
    notifications_list = []
    try:
        notifications = Notification.objects.filter(
            utilisateur=user,
            lue=False
        ).order_by('-date_envoi')[:3]
        
        for notif in notifications:
            delta = timezone.now().date() - notif.date_envoi.date() if hasattr(notif.date_envoi, 'date') else timezone.now().date() - notif.date_envoi
            if delta.days == 0:
                temps = "Aujourd'hui"
            elif delta.days == 1:
                temps = "Hier"
            elif delta.days < 7:
                temps = f"Il y a {delta.days} jours"
            else:
                temps = notif.date_envoi.strftime('%d/%m/%Y')
            
            notifications_list.append({
                'message': notif.message[:100] if hasattr(notif, 'message') else str(notif),
                'temps': temps,
                'icone': 'notifications',
                'couleur': 'primary'
            })
    except:
        pass
    
    # Progression globale
    progression = {
        'pourcentage': 0,
        'cours_completes': 0,
        'total_cours': 0,
        'quiz_reussis': 0,
        'total_quiz': 0,
        'heures_effectuees': 0,
        'heures_total': 0
    }
    
    try:
        seances = Seance.objects.filter(affectation__in=affectations)
        total = seances.count()
        terminees = seances.filter(statut='termine').count()
        
        progression['cours_completes'] = terminees
        progression['total_cours'] = total
        progression['pourcentage'] = int((terminees / total * 100)) if total > 0 else 0
        
        heures = 0
        for s in seances.filter(statut='termine'):
            if s.duree:
                try:
                    duree_str = s.duree.replace('h', '').strip()
                    if 'min' in duree_str:
                        parts = duree_str.split('h')
                        if len(parts) == 2:
                            heures += float(parts[0]) + float(parts[1].replace('min', '')) / 60
                    else:
                        heures += float(duree_str)
                except:
                    pass
        progression['heures_effectuees'] = int(heures)
        
        if forfait:
            progression['heures_total'] = forfait.nombre_heure
    except:
        pass
    
    # ============================================
    # 🔥 CONTEXTE POUR LE TEMPLATE
    # ============================================
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'client': client,
        'parent': parent,  # 🔥 Le parent de l'étudiant (peut être None)
        'affectations': affectations,
        'cours_actifs': cours_actifs,
        'cours_termines': cours_termines,
        'heures_restantes': heures_restantes,
        'moyenne_generale': round(moyenne_generale, 1) if moyenne_generale else 0,
        'cours': cours_list,
        'prochaines_seances': prochaines_seances,
        'notifications': notifications_list,
        'progression': progression,
        'nombre_affectations': affectations.count(),
        'est_etudiant': True,
    }
    
    return render(request, 'etudiants/dashboard.html', context)


def get_matiere_icone(matiere):
    """Retourne l'icône correspondante à la matière"""
    icones = {
        'math': 'calculate',
        'mathématiques': 'calculate',
        'français': 'menu_book',
        'anglais': 'translate',
        'physique': 'science',
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