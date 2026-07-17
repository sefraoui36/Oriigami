# etudiants/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def profil(request):
    return render(request, 'etudiants/profil.html')

@login_required
def enseignants(request):
    return render(request, 'etudiants/enseignants.html')

@login_required
def seances(request):
    return render(request, 'etudiants/seances.html')

@login_required
def forfait(request):
    return render(request, 'etudiants/forfait.html')

@login_required
def portefeuille(request):
    return render(request, 'etudiants/portefeuille.html')

@login_required
def progression(request):
    return render(request, 'etudiants/progression.html')

@login_required
def avis(request):
    return render(request, 'etudiants/avis.html')

@login_required
def notifications(request):
    return render(request, 'etudiants/notifications.html')

@login_required
def parametres(request):
    return render(request, 'etudiants/parametres.html')