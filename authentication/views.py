from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
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

def inscription(request):
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')
        
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie ! Bienvenue sur Origami Privé.")
            return redirect('authentication:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = InscriptionForm()
    
    return render(request, 'clients/inscription.html', {'form': form})

def connexion(request):
    if request.user.is_authenticated:
        return redirect('authentication:dashboard')
        
    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Bonjour {user.first_name} ! Content de vous revoir.")
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
    user = request.user
    
    try:
        client = Client.objects.get(utilisateur=user)
    except Client.DoesNotExist:
        client = None
    
    etudiant = None
    if client:
        try:
            etudiant = Etudiant.objects.filter(client=client).first()
        except:
            pass
    
    cours_actifs = 0
    cours_termines = 0
    if etudiant:
        try:
            seances_etudiant = Seance.objects.filter(affectation__etudiant=etudiant)
            cours_actifs = seances_etudiant.filter(statut__in=['prevue', 'en_cours']).count()
            cours_termines = seances_etudiant.filter(statut='termine').count()
        except:
            pass
    
    heures_restantes = 0
    try:
        forfait = Forfait.objects.filter(utilisateur=user).first()
        if forfait:
            heures_restantes = forfait.nombre_heure
    except:
        pass
    
    moyenne_generale = 0
    if etudiant:
        try:
            seances = Seance.objects.filter(affectation__etudiant=etudiant)
            notes = [s.qualite for s in seances if s.qualite]
            if notes:
                moyenne_generale = sum(notes) / len(notes)
        except:
            pass
    
    cours_list = []
    try:
        affectations = Affectation.objects.filter(utilisateur=user, statut_affectation='active')[:3]
        for aff in affectations:
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
    except:
        pass
    
    if not cours_list:
        cours_list = []

    prochaines_seances = []
    try:
        if etudiant:
            seances = Seance.objects.filter(
                affectation__etudiant=etudiant,
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

    notifications_list = []
    try:
        notifications = Notification.objects.filter(
            utilisateur=user,
            lecture=False
        ).order_by('-date_envoi')[:3]
        
        for notif in notifications:
            delta = timezone.now().date() - notif.date_envoi
            if delta.days == 0:
                temps = "Aujourd'hui"
            elif delta.days == 1:
                temps = "Hier"
            elif delta.days < 7:
                temps = f"Il y a {delta.days} jours"
            else:
                temps = notif.date_envoi.strftime('%d/%m/%Y')
            
            notifications_list.append({
                'message': notif.message[:100],
                'temps': temps,
                'icone': 'notifications',
                'couleur': 'primary'
            })
    except:
        pass
    
    progression = {
        'pourcentage': 0,
        'cours_completes': 0,
        'total_cours': 0,
        'quiz_reussis': 0,
        'total_quiz': 0,
        'heures_effectuees': 0,
        'heures_total': 0
    }
    
    if etudiant:
        try:
            seances = Seance.objects.filter(affectation__etudiant=etudiant)
            total = seances.count()
            terminees = seances.filter(statut='termine').count()
            
            progression['cours_completes'] = terminees
            progression['total_cours'] = total
            progression['pourcentage'] = int((terminees / total * 100)) if total > 0 else 0
            
            heures = 0
            for s in seances.filter(statut='termine'):
                if s.duree:
                    try:
                        heures += float(s.duree.replace('h', '').strip())
                    except:
                        pass
            progression['heures_effectuees'] = int(heures)
            
            if forfait:
                progression['heures_total'] = forfait.nombre_heure
        except:
            pass

    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'client': client,
        'etudiant': etudiant,
        'cours_actifs': cours_actifs,
        'cours_termines': cours_termines,
        'heures_restantes': heures_restantes,
        'moyenne_generale': round(moyenne_generale, 1) if moyenne_generale else 0,
        'cours': cours_list,
        'prochaines_seances': prochaines_seances,
        'notifications': notifications_list,
        'progression': progression
    }
    
    return render(request, 'etudiants/dashboard.html', context)

def get_matiere_icone(matiere):
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
    for key, icon in icones.items():
        if key in matiere.lower():
            return icon
    return 'school'

def get_matiere_couleur(matiere):
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
    for key, color in couleurs.items():
        if key in matiere.lower():
            return color
    return 'primary'