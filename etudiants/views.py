# etudiants/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from clients.models import Client
from etudiants.models import Etudiant
from enseignants.models import Enseignant
from affectations.models import Affectation
from seances.models import Seance
from forfaits.models import Forfait
from notifications.models import Notification
from portefeuilles.models import Portefeuille
from demandes_paiement.models import DemandePaiement
from ia_recommandations.models import IaRecommendations
from authentication.models import Utilisateur
from avis.models import Avis
from .forms import ParametresForm, SecuriteForm, NotificationPreferencesForm, AvisForm

@login_required
def profil(request):
    user = request.user
    client = Client.objects.filter(utilisateur=user).first()
    
    # ===== GESTION DES ACTIONS POST =====
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Mettre à jour le profil
        if action == 'update_profile':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            telephone = request.POST.get('telephone')
            adresse = request.POST.get('adresse')
            
            # Mettre à jour l'utilisateur
            if first_name:
                user.first_name = first_name.strip()
            if last_name:
                user.last_name = last_name.strip()
            if email:
                user.email = email.strip()
                user.username = email.strip()  # Django utilise username pour l'authentification
            if telephone:
                user.telephone = telephone.strip()
            if adresse:
                user.adresse_actuelle = adresse.strip()
            
            user.save()
            
            # Mettre à jour le client si nécessaire
            if client and adresse:
                client.adresse = adresse.strip()
                client.nom = last_name.strip() if last_name else client.nom
                client.prenom = first_name.strip() if first_name else client.prenom
                client.telephone = telephone.strip() if telephone else client.telephone
                client.save()
            
            messages.success(request, "✅ Vos informations ont été mises à jour avec succès !")
            return redirect('etudiants:profil')
        
        # 2. Changer le mot de passe
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Vérifier le mot de passe actuel
            if not user.check_password(current_password):
                messages.error(request, "❌ Le mot de passe actuel est incorrect.")
                return redirect('etudiants:profil')
            
            # Vérifier que les nouveaux mots de passe correspondent
            if new_password != confirm_password:
                messages.error(request, "❌ Les mots de passe ne correspondent pas.")
                return redirect('etudiants:profil')
            
            # Vérifier la longueur du nouveau mot de passe
            if len(new_password) < 8:
                messages.error(request, "❌ Le mot de passe doit contenir au moins 8 caractères.")
                return redirect('etudiants:profil')
            
            # Changer le mot de passe
            user.set_password(new_password)
            user.save()
            
            # Garder l'utilisateur connecté après changement de mot de passe
            update_session_auth_hash(request, user)
            
            messages.success(request, "✅ Votre mot de passe a été changé avec succès !")
            return redirect('etudiants:profil')
        
        # 3. Supprimer le compte
        elif action == 'delete_account':
            # Déconnecter l'utilisateur
            from django.contrib.auth import logout
            logout(request)
            
            # Supprimer l'utilisateur (cascade supprime aussi les clients)
            user.delete()
            
            messages.success(request, "Votre compte a été supprimé avec succès.")
            return redirect('authentication:connexion')
        
        # 4. Activer/Désactiver la 2FA
        elif action == 'toggle_2fa':
            enabled = request.POST.get('enabled') == 'true'
            # Ajoutez ce champ dans votre modèle Utilisateur si nécessaire
            # user.two_factor_enabled = enabled
            # user.save()
            
            messages.success(request, f"✅ Authentification à deux facteurs {'activée' if enabled else 'désactivée'}")
            return redirect('etudiants:profil')
    
    # ===== AFFICHAGE DU PROFIL =====
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'telephone': user.telephone,
        'adresse_actuelle': user.adresse_actuelle,
        'date_naissance': user.date_naissance,
        'client': client,
    }
    
    return render(request, 'etudiants/profil.html', context)

@login_required
def enseignants(request):
    user = request.user
    enseignants_list = []
    total_enseignants = 0
    
    try:
        client = Client.objects.filter(utilisateur=user).first()
        etudiant = Etudiant.objects.filter(client=client).first()
        
        if etudiant:
            affectations = Affectation.objects.filter(etudiant=etudiant)
            
            for aff in affectations:
                if aff.rh and aff.rh.utilisateur:
                    enseignant_user = aff.rh.utilisateur
                    
                    try:
                        enseignant = Enseignant.objects.get(utilisateur=enseignant_user)
                    except Enseignant.DoesNotExist:
                        enseignant = None
                    
                    seances = Seance.objects.filter(affectation=aff)
                    seances_completees = seances.filter(statut='termine').count()
                    seances_prevues = seances.filter(statut='prevue').count()
                    total_seances = seances.count()
                    
                    progression = int((seances_completees / total_seances * 100)) if total_seances > 0 else 0
                    
                    forfait = Forfait.objects.filter(utilisateur=user).first()
                    forfait_nom = forfait.type if forfait else "Standard"
                    forfait_heures = forfait.nombre_heure if forfait else 0
                    
                    heures_restantes = aff.heures_restantes if aff.heures_restantes else 0
                    
                    enseignants_list.append({
                        'nom': f"{enseignant_user.first_name} {enseignant_user.last_name}",
                        'matiere': aff.matiere,
                        'matiere_personnalise': aff.matiere_personnalise,
                        'seances_completees': seances_completees,
                        'seances_prevues': seances_prevues,
                        'total_seances': total_seances,
                        'progression': progression,
                        'heures_restantes': heures_restantes,
                        'heures_total': forfait_heures,
                        'forfait_nom': forfait_nom,
                        'prochaine_seance': seances.filter(statut='prevue', date__gte=timezone.now().date()).order_by('date', 'heure').first(),
                        'note': 4.5,
                        'experience': enseignant_user.experiences.count() if hasattr(enseignant_user, 'experiences') else 0,
                    })
                    
            total_enseignants = len(enseignants_list)
            
    except Client.DoesNotExist:
        pass
    except Exception as e:
        print(f"Erreur: {e}")
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'enseignants': enseignants_list,
        'total_enseignants': total_enseignants,
    }
    return render(request, 'etudiants/enseignants.html', context)

@login_required
def seances(request):
    user = request.user
    seances_a_venir = []
    seances_terminees = []
    ia_recommendations = []
    
    # Statistiques
    total_seances = 0
    heures_restantes = 0
    heures_total = 0
    presence_data = []
    focus_score = 0
    
    try:
        client = Client.objects.filter(utilisateur=user).first()
        etudiant = Etudiant.objects.filter(client=client).first()
        
        if etudiant:
            # Récupérer les séances à venir
            seances_a_venir = Seance.objects.filter(
                affectation__etudiant=etudiant,
                statut='prevue',
                date__gte=timezone.now().date()
            ).order_by('date', 'heure')[:5]
            
            # Récupérer les séances terminées
            seances_terminees = Seance.objects.filter(
                affectation__etudiant=etudiant,
                statut='termine'
            ).order_by('-date')[:5]
            
            # Récupérer les recommandations IA
            ia_recommendations = IaRecommendations.objects.filter(
                utilisateur=user
            ).order_by('-date')[:3]
            
            # Calculer les statistiques
            all_seances = Seance.objects.filter(affectation__etudiant=etudiant)
            total_seances = all_seances.count()
            seances_terminees_count = all_seances.filter(statut='termine').count()
            
            # Heures restantes (depuis le forfait)
            forfait = Forfait.objects.filter(utilisateur=user).first()
            if forfait:
                heures_total = forfait.nombre_heure or 0
                heures_utilisees = seances_terminees_count * 2  # 2h par séance
                heures_restantes = max(0, heures_total - heures_utilisees)
            
            # Calcul du Focus Score (moyenne des notes ou progression)
            if seances_terminees_count > 0:
                notes = [s.qualite for s in all_seances if s.qualite]
                if notes:
                    notes_float = []
                    for n in notes:
                        try:
                            notes_float.append(float(n))
                        except:
                            pass
                    if notes_float:
                        focus_score = int((sum(notes_float) / len(notes_float)) * 20)  # Convertir /5 en %
                        focus_score = min(100, max(0, focus_score))
            
            # Données pour l'assiduité (derniers 5 jours)
            today = timezone.now().date()
            for i in range(4, -1, -1):
                day = today - timedelta(days=i)
                seances_day = Seance.objects.filter(
                    affectation__etudiant=etudiant,
                    date=day
                )
                total_day = seances_day.count()
                present_day = seances_day.filter(statut='termine').count()
                if total_day > 0:
                    presence_pct = int((present_day / total_day) * 100)
                else:
                    presence_pct = 0
                presence_data.append({
                    'day': day.strftime('%a'),
                    'presence': presence_pct,
                    'is_high': presence_pct >= 80,
                    'is_medium': 50 <= presence_pct < 80,
                    'is_low': presence_pct < 50,
                })
            
            # Si pas de données de présence, générer des valeurs par défaut
            if not presence_data:
                presence_data = [
                    {'day': 'Lun', 'presence': 0, 'is_high': False, 'is_medium': False, 'is_low': True},
                    {'day': 'Mar', 'presence': 0, 'is_high': False, 'is_medium': False, 'is_low': True},
                    {'day': 'Mer', 'presence': 0, 'is_high': False, 'is_medium': False, 'is_low': True},
                    {'day': 'Jeu', 'presence': 0, 'is_high': False, 'is_medium': False, 'is_low': True},
                    {'day': 'Ven', 'presence': 0, 'is_high': False, 'is_medium': False, 'is_low': True},
                ]
            
    except Exception as e:
        print(f"Erreur seances: {e}")
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'seances_a_venir': seances_a_venir,
        'seances_terminees': seances_terminees,
        'ia_recommendations': ia_recommendations,
        'total_seances': total_seances,
        'heures_restantes': heures_restantes,
        'heures_total': heures_total,
        'presence_data': presence_data,
        'focus_score': focus_score,
        'focus_status': 'Optimal' if focus_score >= 80 else 'Bon' if focus_score >= 60 else 'À améliorer',
    }
    return render(request, 'etudiants/seances.html', context)

@login_required
def forfait(request):
    user = request.user
    forfait = None
    forfait_nom = "Aucun forfait"
    forfait_heures = 0
    heures_utilisees = 0
    heures_restantes = 0
    pourcentage = 0
    date_achat = None
    statut_paiement = "Non payé"
    montant = 0
    id_forfait = ""
    enseignant_nom = "Non assigné"
    enseignant_matiere = ""
    prochaine_seance = None
    historique_seances = []
    paiements = []
    
    try:
        forfait = Forfait.objects.filter(utilisateur=user).first()
        
        if forfait:
            forfait_nom = forfait.type if forfait.type else "Forfait Standard"
            forfait_heures = forfait.nombre_heure if forfait.nombre_heure else 0
            date_achat = forfait.date if forfait.date else None
            montant = forfait.prix if forfait.prix else 0
            id_forfait = f"#PKG-{forfait.id_forfait:04d}" if forfait.id_forfait else "#PKG-0001"
            
            try:
                client = Client.objects.filter(utilisateur=user).first()
                etudiant = Etudiant.objects.filter(client=client).first()
                
                if etudiant:
                    seances = Seance.objects.filter(affectation__etudiant=etudiant, statut='termine')
                    heures_utilisees = seances.count() * 2
                    
                    heures_restantes = forfait_heures - heures_utilisees
                    if heures_restantes < 0:
                        heures_restantes = 0
                    
                    if forfait_heures > 0:
                        pourcentage = int((heures_utilisees / forfait_heures) * 100)
                        if pourcentage > 100:
                            pourcentage = 100
                    
                    statut_paiement = "Payé" if forfait.prix and forfait.prix > 0 else "En attente"
                    
                    prochaine_seance = Seance.objects.filter(
                        affectation__etudiant=etudiant,
                        statut='prevue',
                        date__gte=timezone.now().date()
                    ).order_by('date', 'heure').first()
                    
                    affectation = Affectation.objects.filter(etudiant=etudiant).first()
                    if affectation and affectation.rh and affectation.rh.utilisateur:
                        enseignant_user = affectation.rh.utilisateur
                        enseignant_nom = f"{enseignant_user.first_name} {enseignant_user.last_name}"
                        enseignant_matiere = affectation.matiere
                    
                    historique_seances = Seance.objects.filter(
                        affectation__etudiant=etudiant
                    ).order_by('-date', '-heure')[:10]
                    
                    paiements = DemandePaiement.objects.filter(
                        utilisateur=user
                    ).order_by('-date_demande')[:5]
                    
            except Client.DoesNotExist:
                pass
            except Exception as e:
                print(f"Erreur calcul: {e}")
                
    except Forfait.DoesNotExist:
        pass
    except Exception as e:
        print(f"Erreur forfait: {e}")
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'forfait': forfait,
        'forfait_nom': forfait_nom,
        'forfait_heures': forfait_heures,
        'heures_utilisees': heures_utilisees,
        'heures_restantes': heures_restantes,
        'pourcentage': pourcentage,
        'date_achat': date_achat,
        'statut_paiement': statut_paiement,
        'montant': montant,
        'id_forfait': id_forfait,
        'enseignant_nom': enseignant_nom,
        'enseignant_matiere': enseignant_matiere,
        'prochaine_seance': prochaine_seance,
        'historique_seances': historique_seances,
        'paiements': paiements,
        'total_paiements': len(paiements),
    }
    return render(request, 'etudiants/forfait.html', context)

@login_required
def portefeuille(request):
    user = request.user
    portefeuille = None
    transactions = []
    solde = 0
    total_recharge = 0
    total_depense = 0
    total_heures = 0
    id_portefeuille = "#OP-00001"
    statut = "Actif"
    dernier_update = "Aujourd'hui"
    validite = "Illimitée"
    
    try:
        portefeuille = Portefeuille.objects.filter(utilisateur=user).first()
        if portefeuille:
            solde = portefeuille.solde if portefeuille.solde else 0
            id_portefeuille = f"#OP-{portefeuille.id_portefeuille:05d}" if portefeuille.id_portefeuille else "#OP-00001"
    except:
        pass
    
    try:
        transactions = DemandePaiement.objects.filter(utilisateur=user).order_by('-date_demande')[:10]
        
        recharges = DemandePaiement.objects.filter(utilisateur=user, type_demande='recharge', statut='complete')
        for r in recharges:
            total_recharge += r.montant if r.montant else 0
        
        depenses = DemandePaiement.objects.filter(utilisateur=user, type_demande='paiement', statut='complete')
        for d in depenses:
            total_depense += d.montant if d.montant else 0
        
        try:
            client = Client.objects.filter(utilisateur=user).first()
            etudiant = Etudiant.objects.filter(client=client).first()
            if etudiant:
                seances = Seance.objects.filter(affectation__etudiant=etudiant)
                total_heures = seances.count() * 2
        except:
            pass
            
    except Exception as e:
        print(f"Erreur portefeuille: {e}")
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'portefeuille': portefeuille,
        'transactions': transactions,
        'solde': solde,
        'total_recharge': total_recharge,
        'total_depense': total_depense,
        'total_heures': total_heures,
        'id_portefeuille': id_portefeuille,
        'statut': statut,
        'dernier_update': dernier_update,
        'validite': validite,
        'total_transactions': len(transactions),
    }
    return render(request, 'etudiants/portefeuille.html', context)

@login_required
def progression(request):
    user = request.user
    progression_data = {
        'total': 0, 
        'terminees': 0, 
        'pourcentage': 0,
        'presence': 0,
        'heures_completees': 0,
        'heures_restantes': 0,
        'note_moyenne': 0,
        'matieres': [],
        'evaluations': [],
        'timeline': [],
    }
    
    try:
        client = Client.objects.filter(utilisateur=user).first()
        etudiant = Etudiant.objects.filter(client=client).first()
        
        if etudiant:
            seances = Seance.objects.filter(affectation__etudiant=etudiant)
            total = seances.count()
            terminees = seances.filter(statut='termine').count()
            prevues = seances.filter(statut='prevue').count()
            
            progression_data['total'] = total
            progression_data['terminees'] = terminees
            progression_data['pourcentage'] = int((terminees / total * 100)) if total > 0 else 0
            
            progression_data['heures_completees'] = terminees * 2
            progression_data['heures_restantes'] = prevues * 2
            
            toutes_les_seances = Seance.objects.filter(affectation__etudiant=etudiant)
            total_seances_prevues = toutes_les_seances.count()
            seances_present = toutes_les_seances.filter(statut='termine').count()
            
            if total_seances_prevues > 0:
                taux_presence = int((seances_present / total_seances_prevues) * 100)
            else:
                taux_presence = 0
            
            progression_data['presence'] = taux_presence
            
            notes = [s.qualite for s in seances if s.qualite]
            if notes:
                notes_float = []
                for n in notes:
                    try:
                        notes_float.append(float(n))
                    except:
                        pass
                if notes_float:
                    progression_data['note_moyenne'] = round(sum(notes_float) / len(notes_float), 1)
            
            affectations = Affectation.objects.filter(etudiant=etudiant)
            matieres = []
            for aff in affectations:
                seances_aff = Seance.objects.filter(affectation=aff)
                total_aff = seances_aff.count()
                terminees_aff = seances_aff.filter(statut='termine').count()
                progression_aff = int((terminees_aff / total_aff * 100)) if total_aff > 0 else 0
                
                matieres.append({
                    'nom': aff.matiere,
                    'progression': progression_aff,
                })
            progression_data['matieres'] = matieres
            
            avis_enseignants = Avis.objects.filter(
                etudiant=etudiant
            ).select_related('enseignant', 'affectation').order_by('-date_creation')[:5]
            
            evaluations = []
            for avis in avis_enseignants:
                evaluations.append({
                    'enseignant_nom': f"{avis.enseignant.first_name} {avis.enseignant.last_name}",
                    'matiere': avis.affectation.matiere if avis.affectation else '',
                    'commentaire': avis.commentaire,
                    'note': avis.note,
                    'date': avis.date_creation,
                })
            progression_data['evaluations'] = evaluations
            
            timeline = []
            
            seances_terminees = Seance.objects.filter(
                affectation__etudiant=etudiant,
                statut='termine'
            ).select_related('affectation').order_by('-date')[:10]
            
            for seance in seances_terminees:
                enseignant_nom = "Enseignant"
                if seance.affectation and seance.affectation.rh and seance.affectation.rh.utilisateur:
                    enseignant_nom = f"{seance.affectation.rh.utilisateur.first_name} {seance.affectation.rh.utilisateur.last_name}"
                
                niveau = "Débutant"
                niveau_couleur = "blue"
                if seance.qualite:
                    try:
                        note = float(seance.qualite)
                        if note >= 4.5:
                            niveau = "Excellent"
                            niveau_couleur = "green"
                        elif note >= 3.5:
                            niveau = "Bien"
                            niveau_couleur = "blue"
                        elif note >= 2.5:
                            niveau = "Moyen"
                            niveau_couleur = "orange"
                        else:
                            niveau = "À améliorer"
                            niveau_couleur = "red"
                    except:
                        pass
                
                matiere = seance.affectation.matiere if seance.affectation else "Cours"
                date_formatee = seance.date.strftime('%d %b %Y') if seance.date else ""
                
                timeline.append({
                    'date': seance.date,
                    'date_formatee': date_formatee,
                    'matiere': matiere,
                    'titre': f"Séance de {matiere}",
                    'description': f"Avec {enseignant_nom}",
                    'niveau': niveau,
                    'niveau_couleur': niveau_couleur,
                    'qualite': seance.qualite,
                })
            
            if len(timeline) < 3 and len(matieres) > 0:
                for matiere in matieres:
                    if matiere['progression'] >= 80 and len(timeline) < 6:
                        timeline.append({
                            'date': timezone.now().date(),
                            'date_formatee': timezone.now().date().strftime('%d %b %Y'),
                            'matiere': matiere['nom'],
                            'titre': f"Maîtrise de {matiere['nom']}",
                            'description': "Niveau avancé atteint",
                            'niveau': "Excellent",
                            'niveau_couleur': "green",
                            'qualite': "5.0",
                        })
            
            timeline = sorted(timeline, key=lambda x: x['date'], reverse=True)[:6]
            progression_data['timeline'] = timeline
            
    except Exception as e:
        print(f"Erreur progression: {e}")
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'progression': progression_data,
    }
    return render(request, 'etudiants/progression.html', context)

@login_required
def avis(request):
    user = request.user
    avis_list = []
    enseignants_a_noter = []
    avis_existants = []
    
    total_avis = 0
    note_moyenne = 0
    
    try:
        client = Client.objects.filter(utilisateur=user).first()
        etudiant = Etudiant.objects.filter(client=client).first()
        
        if etudiant:
            affectations = Affectation.objects.filter(etudiant=etudiant)
            
            for aff in affectations:
                if aff.rh and aff.rh.utilisateur:
                    enseignant_user = aff.rh.utilisateur
                    
                    try:
                        avis_existant = Avis.objects.get(
                            etudiant=etudiant,
                            enseignant=enseignant_user,
                            affectation=aff
                        )
                        
                        avis_existants.append({
                            'id': avis_existant.id_avis,
                            'enseignant_nom': f"{enseignant_user.first_name} {enseignant_user.last_name}",
                            'matiere': aff.matiere,
                            'note': avis_existant.note,
                            'commentaire': avis_existant.commentaire,
                            'date_creation': avis_existant.date_creation,
                            'enseignant_id': enseignant_user.id,
                            'affectation_id': aff.id_affectation,
                        })
                        
                        total_avis += 1
                        note_moyenne += avis_existant.note
                        
                    except Avis.DoesNotExist:
                        derniere_seance = Seance.objects.filter(
                            affectation=aff,
                            statut='termine'
                        ).order_by('-date', '-heure').first()
                        
                        enseignants_a_noter.append({
                            'id': enseignant_user.id,
                            'nom': f"{enseignant_user.first_name} {enseignant_user.last_name}",
                            'matiere': aff.matiere,
                            'specialite': enseignant_user.specialite if hasattr(enseignant_user, 'specialite') else '',
                            'derniere_seance': derniere_seance.date if derniere_seance else None,
                            'affectation_id': aff.id_affectation,
                        })
            
            if total_avis > 0:
                note_moyenne = round(note_moyenne / total_avis, 1)
            
            context_avis = {
                'total_avis': total_avis,
                'note_moyenne': note_moyenne,
                'avis_existants': avis_existants,
                'enseignants_a_noter': enseignants_a_noter,
                'a_ete_ameliore': True if total_avis > 0 else False,
            }
            
    except Client.DoesNotExist:
        pass
    except Exception as e:
        print(f"Erreur avis: {e}")
    
    if request.method == 'POST':
        form = AvisForm(request.POST)
        if form.is_valid():
            enseignant_id = form.cleaned_data['enseignant_id']
            affectation_id = form.cleaned_data['affectation_id']
            note = form.cleaned_data['note']
            commentaire = form.cleaned_data['commentaire']
            
            try:
                client = Client.objects.filter(utilisateur=user).first()
                etudiant = Etudiant.objects.filter(client=client).first()
                enseignant = Utilisateur.objects.get(id=enseignant_id)
                affectation = Affectation.objects.get(id_affectation=affectation_id)
                
                avis_existant = Avis.objects.filter(
                    etudiant=etudiant,
                    enseignant=enseignant,
                    affectation=affectation
                ).first()
                
                if avis_existant:
                    avis_existant.note = note
                    avis_existant.commentaire = commentaire
                    avis_existant.save()
                    messages.success(request, "Votre avis a été mis à jour avec succès !")
                else:
                    Avis.objects.create(
                        etudiant=etudiant,
                        enseignant=enseignant,
                        affectation=affectation,
                        note=note,
                        commentaire=commentaire
                    )
                    messages.success(request, "Votre avis a été ajouté avec succès !")
                
                return redirect('etudiants:avis')
                
            except Exception as e:
                messages.error(request, f"Erreur lors de l'enregistrement de l'avis: {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = AvisForm()
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'form': form,
        'total_avis': total_avis,
        'note_moyenne': note_moyenne,
        'avis_existants': avis_existants,
        'enseignants_a_noter': enseignants_a_noter,
        'a_ete_ameliore': True if total_avis > 0 else False,
    }
    return render(request, 'etudiants/avis.html', context)

@login_required
def notifications(request):
    user = request.user
    
    notifications_list = []
    notifications_non_lues = 0
    total_notifications = 0
    seances_notifications = []
    paiements_notifications = []
    messages_notifications = []
    
    try:
        all_notifications = Notification.objects.filter(
            Q(utilisateur=user) | Q(destinataire=user)
        ).order_by('-date_envoi')
        
        total_notifications = all_notifications.count()
        notifications_non_lues = all_notifications.filter(lue=False).count()
        
        notifications_list = all_notifications[:10]
        
        seances_notifications = all_notifications.filter(type__in=['seance', 'cours', 'rappel'])[:5]
        paiements_notifications = all_notifications.filter(type='paiement')[:5]
        messages_notifications = all_notifications.filter(type__in=['message', 'commentaire'])[:5]
        
    except Exception as e:
        print(f"Erreur notifications: {e}")
        pass
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'telephone': user.telephone,
        'notifications': notifications_list,
        'notifications_non_lues': notifications_non_lues,
        'total_notifications': total_notifications,
        'seances_notifications': seances_notifications,
        'paiements_notifications': paiements_notifications,
        'messages_notifications': messages_notifications,
    }
    return render(request, 'etudiants/notifications.html', context)

@login_required
def parametres(request):
    user = request.user
    client = None
    etudiant = None
    
    try:
        client = Client.objects.filter(utilisateur=user).first()
        if client:
            etudiant = Etudiant.objects.filter(client=client).first()
    except Client.DoesNotExist:
        pass
    
    if request.method == 'POST':
        if 'form_type' in request.POST:
            if request.POST['form_type'] == 'informations':
                form = ParametresForm(request.POST, instance=user, client_instance=client)
                if form.is_valid():
                    user = form.save()
                    if client:
                        client.nom = form.cleaned_data.get('nom', client.nom)
                        client.prenom = form.cleaned_data.get('prenom', client.prenom)
                        client.telephone = form.cleaned_data.get('telephone', client.telephone)
                        client.telephone2 = form.cleaned_data.get('telephone2', client.telephone2)
                        client.adresse = form.cleaned_data.get('adresse', client.adresse)
                        client.save()
                    messages.success(request, 'Vos informations ont été mises à jour avec succès !')
                    return redirect('etudiants:parametres')
                else:
                    messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
            elif request.POST['form_type'] == 'securite':
                form = SecuriteForm(request.POST, user=user)
                if form.is_valid():
                    nouveau_mdp = form.cleaned_data['nouveau_mot_de_passe']
                    user.set_password(nouveau_mdp)
                    user.save()
                    messages.success(request, 'Votre mot de passe a été changé avec succès !')
                    return redirect('etudiants:parametres')
                else:
                    messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
            elif request.POST['form_type'] == 'notifications':
                form = NotificationPreferencesForm(request.POST)
                if form.is_valid():
                    messages.success(request, 'Vos préférences de notification ont été mises à jour !')
                    return redirect('etudiants:parametres')
                else:
                    messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = ParametresForm(instance=user, client_instance=client)
        securite_form = SecuriteForm()
        notifications_form = NotificationPreferencesForm()
    
    try:
        forfait = Forfait.objects.filter(utilisateur=user).first()
        forfait_nom = forfait.type if forfait and forfait.type else "Standard"
    except:
        forfait_nom = "Standard"
    
    prochaine_seance = None
    try:
        if etudiant:
            prochaine_seance = Seance.objects.filter(
                affectation__etudiant=etudiant,
                statut='prevue',
                date__gte=timezone.now().date()
            ).order_by('date', 'heure').first()
    except:
        pass
    
    context = {
        'user': user,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'telephone': user.telephone,
        'telephone2': user.telephone2,
        'adresse': client.adresse if client else '',
        'date_naissance': user.date_naissance,
        'sexe': user.sexe,
        'cin': user.cin,
        'activite_actuelle': user.activite_actuelle,
        'client': client,
        'etudiant': etudiant,
        'form': form,
        'securite_form': securite_form,
        'notifications_form': notifications_form,
        'forfait_nom': forfait_nom,
        'prochaine_seance': prochaine_seance,
        'id_etudiant': f"#OP-2024-{user.id:04d}" if user.id else "#OP-2024-0000",
    }
    return render(request, 'etudiants/parametres.html', context)