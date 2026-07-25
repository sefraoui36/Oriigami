# etudiants/forms.py
from django import forms
from django.contrib.auth import get_user_model
from clients.models import Client
from avis.models import Avis

Utilisateur = get_user_model()

class ParametresForm(forms.ModelForm):
    nom = forms.CharField(max_length=100, required=True, label="Nom", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    prenom = forms.CharField(max_length=100, required=True, label="Prénom", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    email = forms.EmailField(required=True, label="Email", widget=forms.EmailInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    telephone = forms.CharField(max_length=20, required=True, label="Téléphone", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    telephone2 = forms.CharField(max_length=20, required=False, label="Téléphone secondaire", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    adresse = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 3,
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }), required=True, label="Adresse")
    date_naissance = forms.DateField(required=False, label="Date de naissance", widget=forms.DateInput(attrs={
        'type': 'date',
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    sexe = forms.ChoiceField(choices=[('', 'Non précisé'), ('M', 'Masculin'), ('F', 'Féminin')], required=False, label="Sexe", widget=forms.Select(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    cin = forms.CharField(max_length=20, required=False, label="CIN", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    activite_actuelle = forms.CharField(max_length=100, required=False, label="Activité actuelle", widget=forms.TextInput(attrs={
        'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all'
    }))
    
    class Meta:
        model = Utilisateur
        fields = ['email', 'first_name', 'last_name', 'date_naissance', 'sexe', 'cin', 'activite_actuelle']
    
    def __init__(self, *args, **kwargs):
        self.client_instance = kwargs.pop('client_instance', None)
        super().__init__(*args, **kwargs)
        
        if self.client_instance:
            self.fields['nom'].initial = self.client_instance.nom
            self.fields['prenom'].initial = self.client_instance.prenom
            self.fields['telephone'].initial = self.client_instance.telephone
            self.fields['telephone2'].initial = self.client_instance.telephone2
            self.fields['adresse'].initial = self.client_instance.adresse
        else:
            if self.instance:
                self.fields['nom'].initial = self.instance.last_name
                self.fields['prenom'].initial = self.instance.first_name
                self.fields['telephone'].initial = self.instance.telephone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user


class SecuriteForm(forms.Form):
    ancien_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all',
            'placeholder': 'Votre mot de passe actuel'
        }),
        label="Ancien mot de passe"
    )
    nouveau_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all',
            'placeholder': 'Nouveau mot de passe (8 caractères minimum)'
        }),
        label="Nouveau mot de passe"
    )
    confirmer_mot_de_passe = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full p-3 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all',
            'placeholder': 'Confirmez le nouveau mot de passe'
        }),
        label="Confirmer le nouveau mot de passe"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        ancien = cleaned_data.get('ancien_mot_de_passe')
        nouveau = cleaned_data.get('nouveau_mot_de_passe')
        confirmer = cleaned_data.get('confirmer_mot_de_passe')
        
        if self.user and ancien:
            if not self.user.check_password(ancien):
                self.add_error('ancien_mot_de_passe', "Le mot de passe actuel est incorrect.")
        
        if nouveau and confirmer and nouveau != confirmer:
            self.add_error('confirmer_mot_de_passe', "Les mots de passe ne correspondent pas.")
        
        if nouveau and len(nouveau) < 8:
            self.add_error('nouveau_mot_de_passe', "Le mot de passe doit contenir au moins 8 caractères.")
        
        return cleaned_data


class NotificationPreferencesForm(forms.Form):
    rappels_seance = forms.BooleanField(required=False, initial=True, label="Rappels de séance")
    rappels_sms = forms.BooleanField(required=False, initial=True, label="SMS")
    rappels_email = forms.BooleanField(required=False, initial=True, label="Email")
    messages_enseignants = forms.BooleanField(required=False, initial=True, label="Messages enseignants")
    newsletter = forms.BooleanField(required=False, initial=False, label="Newsletter")
    promotions = forms.BooleanField(required=False, initial=False, label="Promotions")


class AvisForm(forms.Form):
    enseignant_id = forms.IntegerField(widget=forms.HiddenInput())
    affectation_id = forms.IntegerField(widget=forms.HiddenInput())
    note = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'hidden',
            'id': 'note_input'
        })
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-4 bg-surface-container-lowest border border-outline-variant/30 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none',
            'rows': 4,
            'placeholder': 'Partagez votre expérience avec cet enseignant...'
        }),
        required=True,
        label="Commentaire"
    )