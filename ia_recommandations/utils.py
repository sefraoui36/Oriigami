# ia_recommandations/utils.py
from django.utils import timezone
from datetime import timedelta
from seances.models import Seance
from affectations.models import Affectation

def generer_seances_ia(etudiant):
    """
    Génère des séances recommandées par l'IA pour un étudiant
    """
    # Récupérer les affectations de l'étudiant
    affectations = Affectation.objects.filter(etudiant=etudiant)
    
    for aff in affectations:
        # Analyser les performances (simulation)
        seances_existantes = Seance.objects.filter(affectation=aff)
        dernier_score = 0
        
        # Récupérer le dernier score IA
        try:
            ia_reco = IaRecommendations.objects.filter(
                utilisateur=etudiant.client.utilisateur
            ).order_by('-date').first()
            if ia_reco:
                dernier_score = ia_reco.score
        except:
            pass
        
        # Si le score est faible, recommander plus de séances
        if dernier_score < 70:
            # Créer une séance recommandée par l'IA
            nouvelle_seance = Seance.objects.create(
                affectation=aff,
                date=timezone.now().date() + timedelta(days=2),
                heure=timezone.now().time().replace(hour=14, minute=0),
                duree="1h30",
                type_seance="revision_ia",
                statut="prevue"
            )
            return nouvelle_seance
    
    return None