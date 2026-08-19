# seances/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Count
from decimal import Decimal
import json
import re
import logging
import requests
from django.core.cache import cache
from etudiants.models import Etudiant
from django.conf import settings
from clients.models import Client
from enseignants.models import Enseignant
from affectations.models import Affectation
from forfaits.models import Forfait
from portefeuilles.models import Portefeuille, Transaction
from seances.models import Seance
from rh.models import Rh
from utilisateurs.models import Utilisateur

logger = logging.getLogger(__name__)


# ============================================================
# PAGE DE RÉSERVATION
# ============================================================

@login_required
def reserver_seance(request):
    """Page de réservation de séance pour un étudiant"""

    etudiant = Client.objects.filter(
        utilisateur=request.user,
        type_client='ETUDIANT'
    ).first()

    if not etudiant:
        messages.warning(request, "Vous devez être un étudiant pour réserver une séance.")
        return redirect('authentication:dashboard')

    affectations = Affectation.objects.filter(
        utilisateur=request.user,
        statut_affectation='active'
    ).select_related('rh', 'rh__utilisateur')

    utilisateur_ids = [aff.rh.utilisateur_id for aff in affectations if aff.rh]
    enseignants_map = {
        e.utilisateur_id: e
        for e in Enseignant.objects.filter(utilisateur_id__in=utilisateur_ids)
    }

    professeurs_affectes = []
    for aff in affectations:
        if aff.rh and aff.rh.utilisateur_id in enseignants_map:
            enseignant = enseignants_map[aff.rh.utilisateur_id]
            professeurs_affectes.append({
                'id': enseignant.id_enseignant,
                'nom': enseignant.utilisateur.get_full_name(),
                'matiere': aff.matiere,
                'heures_restantes': aff.heures_restantes,
            })

    matieres_disponibles = list(
        Enseignant.objects.exclude(matiere__isnull=True)
        .exclude(matiere__exact='')
        .values_list('matiere', flat=True)
        .distinct()
    )

    if not matieres_disponibles:
        matieres_disponibles = [
            'Mathématiques', 'Physique', 'Chimie', 'SVT',
            'Français', 'Anglais', 'Histoire', 'Géographie',
            'Philosophie', 'Informatique', 'Programmation',
            'Sciences Economiques', 'Comptabilité', 'Arabe',
            'Espagnol', 'Allemand'
        ]

    portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
    solde_portefeuille = portefeuille.solde if portefeuille else 0

    context = {
        'etudiant': etudiant,
        'matieres_disponibles': matieres_disponibles,
        'solde_portefeuille': solde_portefeuille,
        'professeurs_affectes': professeurs_affectes,
        'user': request.user,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'niveau_etude': etudiant.niveau_scolaire or 'Non spécifié',
        'nombre_affectations': affectations.count(),
    }

    return render(request, 'seances/reservation.html', context)


# ============================================================
# HELPERS "BULK" — tout en requêtes groupées, zéro boucle N+1
# ============================================================

def get_professeurs_affectes_ids(user_id):
    """
    Retourne l'ensemble des id_enseignant déjà affectés à cet étudiant.
    1 seule requête (jointure), à calculer UNE FOIS par requête HTTP,
    jamais recalculée pour chaque matière.
    """
    utilisateur_ids_rh = list(
        Affectation.objects.filter(
            utilisateur_id=user_id,
            statut_affectation='active',
            rh__isnull=False,
        ).values_list('rh__utilisateur_id', flat=True)
    )

    if not utilisateur_ids_rh:
        return set()

    return set(
        Enseignant.objects.filter(
            utilisateur_id__in=utilisateur_ids_rh
        ).values_list('id_enseignant', flat=True)
    )


def get_ratings_bulk(enseignant_utilisateur_ids):
    """
    Calcule rating + nb_seances pour une liste d'utilisateur_id d'enseignants,
    en UNE seule requête (au lieu d'une requête + boucle par enseignant).

    Retourne { utilisateur_id: {'rating': float, 'nb_seances': int} }
    """
    result = {uid: {'rating': 0, 'nb_seances': 0} for uid in enseignant_utilisateur_ids}
    if not enseignant_utilisateur_ids:
        return result

    rows = Seance.objects.filter(
        affectation__rh__utilisateur_id__in=enseignant_utilisateur_ids
    ).values('affectation__rh__utilisateur_id', 'qualite')

    buckets = {}
    for row in rows:
        uid = row['affectation__rh__utilisateur_id']
        buckets.setdefault(uid, []).append(row['qualite'])

    for uid, qualites in buckets.items():
        nb_seances = len(qualites)
        valeurs = []
        for q in qualites:
            if q:
                try:
                    valeurs.append(float(q))
                except (ValueError, TypeError):
                    pass
        rating = (sum(valeurs) / len(valeurs)) if valeurs else 0
        result[uid] = {'rating': rating, 'nb_seances': nb_seances}

    return result


def get_affectations_similaires_bulk(matiere, enseignant_utilisateur_ids):
    """
    Compte, en UNE seule requête groupée, le nombre d'affectations actives
    pour une matière donnée, par utilisateur_id d'enseignant (via rh).

    Retourne { utilisateur_id: count }
    """
    if not enseignant_utilisateur_ids:
        return {}

    rows = (
        Affectation.objects.filter(
            matiere__icontains=matiere,
            rh__utilisateur_id__in=enseignant_utilisateur_ids,
            statut_affectation='active',
        )
        .values('rh__utilisateur_id')
        .annotate(cnt=Count('id'))
    )
    return {row['rh__utilisateur_id']: row['cnt'] for row in rows}


def calculer_score_enseignant(enseignant, matiere, professeurs_affectes_ids,
                               ratings_bulk, affectations_bulk):
    """
    Fonction PURE : aucune requête SQL ici. Toutes les données nécessaires
    ont déjà été récupérées en amont via les fonctions *_bulk.
    """
    score = 50
    deja_affecte = enseignant.id_enseignant in professeurs_affectes_ids
    if deja_affecte:
        score += 30

    if enseignant.experience:
        years = re.findall(r'\d+', enseignant.experience)
        if years:
            score += min(20, int(years[0]) * 2)

    if enseignant.diplome:
        if 'Doctorat' in enseignant.diplome or 'PhD' in enseignant.diplome:
            score += 15
        elif 'Master' in enseignant.diplome:
            score += 10
        elif 'Licence' in enseignant.diplome:
            score += 5

    if getattr(enseignant, 'disponible', True):
        score += 10

    tarif = float(enseignant.tarif_heure) if enseignant.tarif_heure else 120
    if tarif <= 130:
        score += 5

    rating_info = ratings_bulk.get(enseignant.utilisateur_id, {'rating': 0, 'nb_seances': 0})
    rating_moyen = rating_info['rating']
    nb_seances = rating_info['nb_seances']

    if rating_moyen > 0:
        score += int(rating_moyen * 2)
    elif nb_seances > 0:
        score += min(10, nb_seances // 2)

    nb_affectations_similaires = affectations_bulk.get(enseignant.utilisateur_id, 0)
    score += min(10, nb_affectations_similaires * 2)

    return {
        'id': enseignant.id_enseignant,
        'nom': enseignant.utilisateur.get_full_name() or enseignant.utilisateur.username,
        'matiere': enseignant.matiere or matiere,
        'experience': enseignant.experience or 'Non spécifié',
        'diplome': enseignant.diplome or 'Non spécifié',
        'disponible': getattr(enseignant, 'disponible', True),
        'tarif_heure': tarif,
        'score': score,
        'deja_affecte': deja_affecte,
        'rating': round(rating_moyen, 1) if rating_moyen else 0,
        'nb_seances': nb_seances,
        'est_exemple': False,
    }


PROFS_DEFAUT = [
    # IDs négatifs volontairement : on ne doit JAMAIS entrer en collision
    # avec un id_enseignant réel de la base (qui commence à 1).
    # 'est_exemple': True => ce ne sont PAS de vrais enseignants réservables,
    # uniquement des profils de démonstration utilisés pour compléter
    # l'affichage quand trop peu de vrais professeurs correspondent.
    {'id': -1, 'nom': 'Dr. Ahmed Benali', 'experience': '8 ans',
     'diplome': 'Doctorat en Mathématiques', 'disponible': True, 'tarif_heure': 140,
     'score': 85, 'deja_affecte': False, 'rating': 4.8, 'nb_seances': 45, 'est_exemple': True},
    {'id': -2, 'nom': 'Mme. Sarah El Fassi', 'experience': '5 ans',
     'diplome': 'Master en Physique', 'disponible': True, 'tarif_heure': 120,
     'score': 75, 'deja_affecte': False, 'rating': 4.5, 'nb_seances': 32, 'est_exemple': True},
    {'id': -3, 'nom': 'M. Karim Idrissi', 'experience': '3 ans',
     'diplome': 'Ingénieur en Informatique', 'disponible': False, 'tarif_heure': 100,
     'score': 60, 'deja_affecte': False, 'rating': 4.2, 'nb_seances': 28, 'est_exemple': True},
]


def _completer_avec_defauts(professeurs_data, matiere, minimum=3):
    """
    Complète une liste de professeurs avec les profs par défaut jusqu'à
    atteindre `minimum` entrées, sans dupliquer un id déjà présent.

    IMPORTANT : ces profs par défaut sont marqués 'est_exemple': True et ne
    doivent JAMAIS être sélectionnables/réservables côté frontend, car ils
    ne correspondent à aucun Enseignant réel en base (voir confirmer_reservation
    qui rejette tout id négatif).
    """
    if len(professeurs_data) >= minimum:
        return professeurs_data

    ids_existants = {p['id'] for p in professeurs_data}
    completes = list(professeurs_data)
    for defaut in PROFS_DEFAUT:
        if len(completes) >= minimum:
            break
        if defaut['id'] in ids_existants:
            continue
        completes.append(dict(defaut, matiere=matiere))
    return completes


def get_pool_professeurs(matiere, user_id, professeurs_affectes_ids=None, limit=10):
    """
    Retourne le POOL COMPLET de candidats pour une matière (jusqu'à `limit`
    profs réels, complété par des profs par défaut si nécessaire pour
    garantir au moins 3 candidats au total).

    Contrairement à l'ancienne version, on NE cache PAS que le top 3 :
    on cache tout le pool, ce qui permet au rafraîchissement de proposer
    de VRAIES alternatives au lieu de retomber toujours sur les 3 mêmes.
    """
    cache_key = f"pool_professeurs_{matiere}_{user_id}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    etudiant = Client.objects.filter(
        utilisateur_id=user_id,
        type_client='ETUDIANT'
    ).first()
    if not etudiant:
        return []

    if professeurs_affectes_ids is None:
        professeurs_affectes_ids = get_professeurs_affectes_ids(user_id)

    enseignants = list(
        Enseignant.objects.filter(
            matiere__icontains=matiere
        ).select_related('utilisateur')[:limit]
    )

    if not enseignants:
        pool = [dict(p, matiere=matiere) for p in PROFS_DEFAUT]
        cache.set(cache_key, pool, 300)
        return pool

    utilisateur_ids = [e.utilisateur_id for e in enseignants]

    ratings_bulk = get_ratings_bulk(utilisateur_ids)
    affectations_bulk = get_affectations_similaires_bulk(matiere, utilisateur_ids)

    pool = [
        calculer_score_enseignant(
            e, matiere, professeurs_affectes_ids, ratings_bulk, affectations_bulk
        )
        for e in enseignants
    ]

    # Garantit toujours au moins 3 candidats DANS LE POOL, même si la BDD
    # n'a que 1 ou 2 profs pour cette matière.
    pool = _completer_avec_defauts(pool, matiere, minimum=3)

    cache.set(cache_key, pool, 300)
    return pool


def selectionner_suggestions(pool, exclude_ids=None, top_n=3):
    """
    À partir d'un pool complet, retourne un tuple :
    (professeurs_suggeres, statut)

    statut in {'ok', 'partiel', 'meme_resultat'}
    - 'ok'           : top_n candidats disponibles (nouveaux si exclude_ids fourni)
    - 'partiel'      : entre 1 et top_n-1 nouveaux candidats disponibles
    - 'meme_resultat': aucun nouveau candidat -> on retombe sur le pool entier
    """
    exclude_ids = exclude_ids or set()

    if not exclude_ids:
        suggestions = sorted(pool, key=lambda x: x['score'], reverse=True)[:top_n]
        return suggestions, 'ok'

    disponibles = [p for p in pool if p['id'] not in exclude_ids]
    disponibles = sorted(disponibles, key=lambda x: x['score'], reverse=True)

    if len(disponibles) == 0:
        # Aucun nouveau prof : on retombe sur le classement complet du pool
        fallback = sorted(pool, key=lambda x: x['score'], reverse=True)[:top_n]
        return fallback, 'meme_resultat'

    if len(disponibles) < top_n:
        # On affiche uniquement les VRAIS nouveaux, pas de remplissage
        # avec un prof déjà vu (ça recréerait le doublon qu'on veut éviter)
        return disponibles, 'partiel'

    return disponibles[:top_n], 'ok'


# ============================================================
# APPEL GROK (optionnel, dégradé proprement si indisponible)
# ============================================================

def _appeler_grok(matiere, niveau, localisation, professeurs_data, affectations_info):
    """Retourne (grok_utilise: bool, profs_suggeres: list)."""
    XAI_API_KEY = getattr(settings, 'XAI_API_KEY', None)
    if not XAI_API_KEY:
        return False, []

    prompt = f"""
    Tu es un assistant spécialisé dans le matching entre étudiants et professeurs particuliers.

    CONTEXTE :
    - Affectations existantes : {affectations_info}
    - Matière recherchée : {matiere}
    - Niveau : {niveau}
    - Localisation : {localisation}

    CRITÈRES (par ordre d'importance) :
    1. Professeurs déjà affectés à l'étudiant (score +30)
    2. Expérience et diplômes
    3. Disponibilité
    4. Rating
    5. Tarif raisonnable

    LISTE DES PROFESSEURS :
    {json.dumps(professeurs_data, ensure_ascii=False)}

    Retourne UNIQUEMENT un tableau JSON des 3 meilleurs professeurs avec un champ "score" sur 100.
    """

    try:
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {XAI_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'grok-4.5',
                'messages': [
                    {'role': 'system', 'content': 'Tu es un assistant expert en matching éducatif. Réponds uniquement en JSON valide.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 800,
            },
            timeout=4,  # court : on ne veut jamais que Grok soit le goulot d'étranglement
        )
        if response.status_code != 200:
            return False, []

        content = response.json().get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        content = re.sub(r'^```json|^```|```$', '', content).strip()
        parsed = json.loads(content)
        if isinstance(parsed, list) and parsed:
            return True, parsed
        return False, []
    except Exception as e:
        logger.warning(f"Grok indisponible, fallback classement local: {e}")
        return False, []


def _valider_et_completer_reponse_grok(profs_bruts_grok, pool, exclude_ids=None):
    """
    Ne JAMAIS afficher directement ce que Grok renvoie : on ne lui fait
    confiance que pour l'ORDRE/le CHOIX (via l'id), et on repart des
    données réelles (pool) pour tous les champs affichés.

    `exclude_ids` : si fourni (cas d'un rafraîchissement), on ignore toute
    suggestion de Grok pointant vers un prof déjà exclu.

    Retourne None si la réponse de Grok n'est pas exploitable (le code
    appelant retombe alors sur `selectionner_suggestions`).
    """
    if not isinstance(profs_bruts_grok, list) or not profs_bruts_grok:
        return None

    exclude_ids = exclude_ids or set()
    profs_par_id = {p['id']: p for p in pool}
    valides = []
    ids_deja_pris = set()

    for item in profs_bruts_grok:
        if not isinstance(item, dict):
            continue
        pid = item.get('id')
        if pid not in profs_par_id or pid in ids_deja_pris or pid in exclude_ids:
            continue
        base = dict(profs_par_id[pid])
        if 'score' in item:
            try:
                base['score'] = int(item['score'])
            except (TypeError, ValueError):
                pass
        valides.append(base)
        ids_deja_pris.add(pid)

    if len(valides) < 3:
        reste_trie = sorted(
            (p for p in pool if p['id'] not in ids_deja_pris and p['id'] not in exclude_ids),
            key=lambda x: x['score'], reverse=True
        )
        for p in reste_trie:
            if len(valides) >= 3:
                break
            valides.append(p)

    return valides[:3] if len(valides) >= 3 else None


def _parse_exclude_ids(raw):
    """Parse une chaîne 'id1,id2,id3' en set d'entiers, tolérant."""
    exclude_ids = set()
    if not raw:
        return exclude_ids
    for x in raw.split(','):
        x = x.strip()
        if x:
            try:
                exclude_ids.add(int(x))
            except ValueError:
                pass
    return exclude_ids


# ============================================================
# API : 1 SÉANCE
# ============================================================

@login_required
def suggerer_professeurs(request):
    """API pour suggérer des professeurs pour UNE matière/séance."""

    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    matiere = request.POST.get('matiere')
    localisation = request.POST.get('localisation')
    niveau = request.POST.get('niveau')
    exclude_ids = _parse_exclude_ids(request.POST.get('exclude_ids', ''))

    if not matiere:
        return JsonResponse({'error': 'Veuillez sélectionner une matière'}, status=400)

    professeurs_affectes_ids = get_professeurs_affectes_ids(request.user.id)
    pool = get_pool_professeurs(matiere, request.user.id, professeurs_affectes_ids)

    affectations_info = (
        f"L'étudiant a déjà {len(professeurs_affectes_ids)} professeur(s) affecté(s)."
        if professeurs_affectes_ids else "Aucune affectation existante"
    )

    grok_utilise = False
    profs_suggeres = None
    statut = 'ok'

    # Grok uniquement au chargement initial : lors d'un rafraîchissement on
    # veut une garantie stricte de ne jamais réafficher un prof déjà exclu,
    # ce que le classement local garantit nativement.
    if not exclude_ids:
        grok_utilise, profs_bruts_grok = _appeler_grok(
            matiere, niveau, localisation, pool, affectations_info
        )
        if grok_utilise:
            profs_suggeres = _valider_et_completer_reponse_grok(profs_bruts_grok, pool)
            if profs_suggeres is None:
                grok_utilise = False

    if not profs_suggeres:
        profs_suggeres, statut = selectionner_suggestions(pool, exclude_ids)

    for prof in profs_suggeres:
        prof.setdefault('deja_affecte', False)
        prof.setdefault('rating', 0)
        prof.setdefault('nb_seances', 0)
        prof.setdefault('est_exemple', False)

    stats = {
        'total_affectations': Affectation.objects.filter(
            utilisateur=request.user, statut_affectation='active'
        ).count(),
        'professeurs_affectes': len(professeurs_affectes_ids),
        'matieres_affectees': list(
            Affectation.objects.filter(
                utilisateur=request.user, statut_affectation='active'
            ).values_list('matiere', flat=True).distinct()
        ),
    }

    return JsonResponse({
        'professeurs': profs_suggeres,
        'statistiques': stats,
        'grok_utilise': grok_utilise,
        'meme_resultat': statut == 'meme_resultat',
        'partiel': statut == 'partiel',
        'nb_nouveaux': len(profs_suggeres) if statut == 'partiel' else None,
    })


# ============================================================
# API : PLUSIEURS SÉANCES PERSONNALISÉES (1 carte par matière)
# ============================================================

@login_required
def suggerer_professeurs_multiples(request):
    """
    API pour suggérer des professeurs pour plusieurs séances personnalisées.
    Une "carte" est renvoyée par matière distincte, chacune avec ses profs.
    """

    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    matieres = [m for m in request.POST.getlist('matieres[]') if m]
    localisation = request.POST.get('localisation')
    niveau = request.POST.get('niveau')

    if not matieres:
        return JsonResponse({'error': 'Veuillez sélectionner au moins une matière'}, status=400)

    try:
        exclude_map_raw = json.loads(request.POST.get('exclude_ids_json', '{}'))
    except (json.JSONDecodeError, TypeError):
        exclude_map_raw = {}

    professeurs_affectes_ids = get_professeurs_affectes_ids(request.user.id)

    resultats = []
    for matiere in matieres:
        exclude_ids = set()
        for x in exclude_map_raw.get(matiere, []) or []:
            try:
                exclude_ids.add(int(x))
            except (TypeError, ValueError):
                pass

        pool = get_pool_professeurs(matiere, request.user.id, professeurs_affectes_ids)
        profs_suggeres, statut = selectionner_suggestions(pool, exclude_ids)

        for prof in profs_suggeres:
            prof.setdefault('est_exemple', False)

        resultats.append({
            'matiere': matiere,
            'professeurs': profs_suggeres,
            'meme_resultat': statut == 'meme_resultat',
            'partiel': statut == 'partiel',
            'nb_nouveaux': len(profs_suggeres) if statut == 'partiel' else None,
        })

    return JsonResponse({'resultats': resultats})


# ============================================================
# API : CONFIRMATION DE LA RÉSERVATION (paiement + création réelle)
# ============================================================

@login_required
def confirmer_reservation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Données invalides'}, status=400)

    mode_paiement = data.get('mode_paiement')
    seances_data = data.get('seances', [])
    # 👇 Diagnostic pédagogique rempli juste avant le paiement (step 4 du wizard).
    # Purement informatif pour le moment : on le journalise pour que l'équipe
    # pédagogique puisse le consulter et, à terme, le rattacher à un modèle
    # dédié (ex: PreferenceApprentissage) si on veut le persister en base.
    preferences = data.get('preferences', {})

    if mode_paiement not in ('portefeuille', 'carte', 'virement'):
        return JsonResponse({'error': 'Mode de paiement invalide'}, status=400)

    if not seances_data:
        return JsonResponse({'error': 'Aucune séance à réserver'}, status=400)

    for s in seances_data:
        try:
            prof_id = int(s.get('professeur_id', -1))
        except (TypeError, ValueError):
            prof_id = -1

        if prof_id < 0:
            return JsonResponse({
                'error': f"Le professeur choisi pour « {s.get('matiere')} » n'est pas "
                         f"disponible pour le moment. Merci de recharger les suggestions."
            }, status=400)

        enseignant = Enseignant.objects.filter(
            id_enseignant=prof_id,
            disponible=True
        ).first()

        if not enseignant:
            return JsonResponse({
                'error': f"Le professeur choisi pour « {s.get('matiere')} » n'est plus disponible. "
                         f"Veuillez rafraîchir les suggestions."
            }, status=400)

    client = Client.objects.filter(utilisateur=request.user, type_client='ETUDIANT').first()
    if not client:
        return JsonResponse({'error': 'Profil étudiant introuvable'}, status=400)

    try:
        total = sum(Decimal(str(s['tarif'])) for s in seances_data)
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'error': 'Tarifs invalides'}, status=400)

    portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()

    if mode_paiement == 'portefeuille':
        solde_actuel = portefeuille.solde if portefeuille else Decimal('0')
        if not portefeuille or solde_actuel < total:
            return JsonResponse({
                'error': 'Solde insuffisant dans le portefeuille',
                'solde': float(solde_actuel),
                'total': float(total),
            }, status=400)

    statut_affectation = 'active' if mode_paiement == 'portefeuille' else 'en_attente'
    statut_paiement = {
        'portefeuille': 'paye',
        'carte': 'en_attente_carte',
        'virement': 'en_attente_virement',
    }[mode_paiement]
    statut_seance = 'prevue' if mode_paiement == 'portefeuille' else 'reportee'

    seances_creees_ids = []

    try:
        with transaction.atomic():
            if mode_paiement == 'portefeuille':
                portefeuille.solde -= total
                portefeuille.save()
                Transaction.objects.create(
                    utilisateur=request.user,
                    montant=-total,
                    type_transaction='paiement_seance',
                    description=f"Paiement de {len(seances_data)} séance(s)",
                )

            for s in seances_data:
                enseignant = Enseignant.objects.filter(
                    id_enseignant=s['professeur_id'],
                    disponible=True
                ).select_related('utilisateur').first()

                if not enseignant:
                    raise ValueError(f"Professeur introuvable ou indisponible (id={s.get('professeur_id')})")

                forfait = Forfait.objects.first()
                if not forfait:
                    raise ValueError("Aucun forfait disponible en base")

                affectation = Affectation.objects.create(
                    utilisateur=request.user,
                    enseignant=enseignant,
                    forfait=forfait,
                    matiere=s['matiere'],
                    prix_renumeration=float(s['tarif']),
                    statut_paiement=statut_paiement,
                    statut_affectation=statut_affectation,
                    heures_restantes=1,
                )

                seance = Seance.objects.create(
                    affectation=affectation,
                    date=s['date'],
                    heure=s['heure'],
                    duree=s.get('duree', '1h'),
                    type_seance=s['matiere'],
                    statut=statut_seance,
                )
                seances_creees_ids.append(seance.id)

    except ValueError as e:
        logger.error(f"Erreur confirmation réservation: {e}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Erreur inattendue lors de la confirmation de réservation")
        return JsonResponse({'error': "Une erreur est survenue, veuillez réessayer."}, status=500)

    if preferences:
        logger.info(
            "Préférences pédagogiques renseignées par l'utilisateur %s pour les séances %s : %s",
            request.user.id, seances_creees_ids, preferences,
        )

    payload = {
        'success': True,
        'statut_paiement': statut_paiement,
        'seances_ids': seances_creees_ids,
        'total': float(total),
    }

    if mode_paiement == 'carte':
        payload['redirect_url'] = None
        payload['message'] = "Redirection vers le paiement par carte à implémenter (CMI/Stripe)."

    return JsonResponse(payload)


# ============================================================
# API : SUPPRESSION D'UNE RÉSERVATION
# ============================================================

@login_required
def supprimer_reservation(request, affectation_id):
    """
    Supprime une réservation (Affectation) appartenant à l'utilisateur connecté.
    Si elle était payée via portefeuille, rembourse automatiquement le solde.
    La suppression de l'Affectation supprime en cascade ses Séances liées
    (Seance.affectation a on_delete=models.CASCADE).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    affectation = Affectation.objects.filter(
        id=affectation_id, utilisateur=request.user
    ).first()

    if not affectation:
        return JsonResponse({'error': 'Réservation introuvable.'}, status=404)

    try:
        with transaction.atomic():
            if affectation.statut_paiement == 'paye':
                portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
                if portefeuille:
                    montant_rembourse = Decimal(str(affectation.prix_renumeration or 0))
                    portefeuille.solde += montant_rembourse
                    portefeuille.save()
                    Transaction.objects.create(
                        utilisateur=request.user,
                        montant=montant_rembourse,
                        type_transaction='remboursement_annulation',
                        description=f"Remboursement annulation - {affectation.matiere}",
                    )

            affectation.delete()

    except Exception as e:
        logger.exception("Erreur lors de la suppression de la réservation")
        return JsonResponse({'error': "Une erreur est survenue lors de la suppression."}, status=500)

    return JsonResponse({'success': True})

# ============================================================
# PAGE DE RÉSERVATION POUR PARENT
# ============================================================

@login_required
def reserver_seance_parent(request):
    """Page de réservation de séance pour un parent (pour ses enfants)"""
    
    # Vérifier que l'utilisateur est un parent
    parent = Client.objects.filter(
        utilisateur=request.user,
        type_client='PARENT'
    ).first()
    
    if not parent:
        messages.warning(request, "Vous devez être un parent pour accéder à cette page.")
        return redirect('clients:dashboard_parent')
    
    # Récupérer les enfants du parent
    enfants = Client.objects.filter(
        parent=parent,
        type_client='ETUDIANT'
    ).select_related('utilisateur')
    
    if not enfants.exists():
        messages.warning(request, "Vous n'avez pas encore d'enfant inscrit. Ajoutez un enfant d'abord.")
        return redirect('clients:liste_enfants')
    
    # Récupérer les matières disponibles
    matieres_disponibles = list(
        Enseignant.objects.exclude(matiere__isnull=True)
        .exclude(matiere__exact='')
        .values_list('matiere', flat=True)
        .distinct()
    )
    
    if not matieres_disponibles:
        matieres_disponibles = [
            'Mathématiques', 'Physique', 'Chimie', 'SVT',
            'Français', 'Anglais', 'Histoire', 'Géographie',
            'Philosophie', 'Informatique', 'Programmation',
            'Sciences Economiques', 'Comptabilité', 'Arabe',
            'Espagnol', 'Allemand'
        ]
    
    # Solde du portefeuille du parent
    portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
    solde_portefeuille = portefeuille.solde if portefeuille else 0
    
    context = {
        'client': parent,
        'enfants': enfants,
        'matieres_disponibles': matieres_disponibles,
        'solde_portefeuille': solde_portefeuille,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'non_lues': 0,  # À implémenter selon ton système de notifications
    }
    
    return render(request, 'parent/reservation.html', context)


# ============================================================
# API : CONFIRMATION DE RÉSERVATION PAR PARENT
# ============================================================

@login_required
def confirmer_reservation_parent(request):
    """
    Version parent de confirmer_reservation.
    La seule différence est que l'enfant_id est passé dans chaque séance,
    et l'affectation est créée pour l'étudiant (enfant) plutôt que pour le parent.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Données invalides'}, status=400)
    
    mode_paiement = data.get('mode_paiement')
    seances_data = data.get('seances', [])
    preferences = data.get('preferences', {})
    
    if mode_paiement not in ('portefeuille', 'carte', 'virement'):
        return JsonResponse({'error': 'Mode de paiement invalide'}, status=400)
    
    if not seances_data:
        return JsonResponse({'error': 'Aucune séance à réserver'}, status=400)
    
    # Vérifier que le parent existe
    parent = Client.objects.filter(
        utilisateur=request.user,
        type_client='PARENT'
    ).first()
    
    if not parent:
        return JsonResponse({'error': 'Profil parent introuvable'}, status=400)
    
    # Vérifier chaque séance
    for s in seances_data:
        # Vérifier l'enfant
        enfant_id = s.get('enfant_id')
        if not enfant_id:
            return JsonResponse({'error': "Veuillez sélectionner un enfant pour chaque séance."}, status=400)
        
        enfant = Client.objects.filter(
            id=enfant_id,
            parent=parent,
            type_client='ETUDIANT'
        ).first()
        
        if not enfant:
            return JsonResponse({'error': f"L'enfant sélectionné n'existe pas ou ne vous est pas associé."}, status=400)
        
        # Vérifier le professeur
        try:
            prof_id = int(s.get('professeur_id', -1))
        except (TypeError, ValueError):
            prof_id = -1
        
        if prof_id < 0:
            return JsonResponse({
                'error': f"Le professeur choisi pour « {s.get('matiere')} » n'est pas disponible pour le moment. Merci de recharger les suggestions."
            }, status=400)
        
        enseignant = Enseignant.objects.filter(
            id_enseignant=prof_id,
            disponible=True
        ).first()
        
        if not enseignant:
            return JsonResponse({
                'error': f"Le professeur choisi pour « {s.get('matiere')} » n'est plus disponible. Veuillez rafraîchir les suggestions."
            }, status=400)
    
    try:
        total = sum(Decimal(str(s['tarif'])) for s in seances_data)
    except (KeyError, TypeError, ValueError):
        return JsonResponse({'error': 'Tarifs invalides'}, status=400)
    
    portefeuille = Portefeuille.objects.filter(utilisateur=request.user).first()
    
    if mode_paiement == 'portefeuille':
        solde_actuel = portefeuille.solde if portefeuille else Decimal('0')
        if not portefeuille or solde_actuel < total:
            return JsonResponse({
                'error': 'Solde insuffisant dans le portefeuille',
                'solde': float(solde_actuel),
                'total': float(total),
            }, status=400)
    
    statut_affectation = 'active' if mode_paiement == 'portefeuille' else 'en_attente'
    statut_paiement = {
        'portefeuille': 'paye',
        'carte': 'en_attente_carte',
        'virement': 'en_attente_virement',
    }[mode_paiement]
    statut_seance = 'prevue' if mode_paiement == 'portefeuille' else 'reportee'
    
    seances_creees_ids = []
    
    try:
        with transaction.atomic():
            if mode_paiement == 'portefeuille':
                portefeuille.solde -= total
                portefeuille.save()
                Transaction.objects.create(
                    utilisateur=request.user,
                    montant=-total,
                    type_transaction='paiement_seance_parent',
                    description=f"Paiement de {len(seances_data)} séance(s) pour enfant(s)",
                )
            
            for s in seances_data:
                # Récupérer l'enfant
                enfant = Client.objects.get(id=s['enfant_id'], parent=parent, type_client='ETUDIANT')
                
                enseignant = Enseignant.objects.filter(
                    id_enseignant=s['professeur_id'],
                    disponible=True
                ).select_related('utilisateur').first()
                
                if not enseignant:
                    raise ValueError(f"Professeur introuvable ou indisponible (id={s.get('professeur_id')})")
                
                forfait = Forfait.objects.first()
                if not forfait:
                    raise ValueError("Aucun forfait disponible en base")
                
                # Créer l'affectation pour l'ENFANT (utilisateur de l'enfant)
                affectation = Affectation.objects.create(
                    utilisateur=enfant.utilisateur,  # 👈 L'utilisateur de l'enfant
                    enseignant=enseignant,
                    forfait=forfait,
                    matiere=s['matiere'],
                    prix_renumeration=float(s['tarif']),
                    statut_paiement=statut_paiement,
                    statut_affectation=statut_affectation,
                    heures_restantes=1,
                    # Optionnel : ajouter un champ pour le parent qui a payé
                )
                
                seance = Seance.objects.create(
                    affectation=affectation,
                    date=s['date'],
                    heure=s['heure'],
                    duree=s.get('duree', '1h'),
                    type_seance=s['matiere'],
                    statut=statut_seance,
                )
                seances_creees_ids.append(seance.id)
    
    except Client.DoesNotExist:
        return JsonResponse({'error': "L'enfant sélectionné n'existe pas ou ne vous est pas associé."}, status=400)
    except ValueError as e:
        logger.error(f"Erreur confirmation réservation parent: {e}")
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Erreur inattendue lors de la confirmation de réservation parent")
        return JsonResponse({'error': "Une erreur est survenue, veuillez réessayer."}, status=500)
    
    if preferences:
        logger.info(
            "Préférences pédagogiques renseignées par le parent %s pour les séances %s : %s",
            request.user.id, seances_creees_ids, preferences,
        )
    
    payload = {
        'success': True,
        'statut_paiement': statut_paiement,
        'seances_ids': seances_creees_ids,
        'total': float(total),
    }
    
    if mode_paiement == 'carte':
        payload['redirect_url'] = None
        payload['message'] = "Redirection vers le paiement par carte à implémenter (CMI/Stripe)."
    
    return JsonResponse(payload)