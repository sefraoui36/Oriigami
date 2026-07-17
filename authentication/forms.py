# authentication/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from clients.models import Client

Utilisateur = get_user_model()

class InscriptionForm(forms.ModelForm):
    prenom = forms.CharField(max_length=100, required=True, label="Prénom")
    nom = forms.CharField(max_length=100, required=True, label="Nom")
    telephone = forms.CharField(max_length=20, required=True, label="Téléphone")
    adresse = forms.CharField(widget=forms.Textarea, required=True, label="Adresse")
    type_client = forms.ChoiceField(
        choices=Client.TypeClient.choices,  # ✅ Utilise les choix du modèle
        required=True, 
        label="Type de compte",
        widget=forms.HiddenInput()
    )
    email = forms.EmailField(required=True, label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput, label="Mot de passe")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirmer le mot de passe")
    
    class Meta:
        model = Utilisateur
        fields = ['email', 'password1', 'password2']
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email
        
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2
        
    def save(self, commit=True):
        user = Utilisateur(
            email=self.cleaned_data['email'],
            username=self.cleaned_data['email'],
            first_name=self.cleaned_data['prenom'],
            last_name=self.cleaned_data['nom']
        )
        user.set_password(self.cleaned_data['password1'])
        
        if commit:
            user.save()
            
            # Créer le client
            client = Client.objects.create(
                utilisateur=user,
                prenom=self.cleaned_data['prenom'],
                nom=self.cleaned_data['nom'],
                telephone=self.cleaned_data['telephone'],
                adresse=self.cleaned_data['adresse'],
                type_client=self.cleaned_data['type_client']  # ✅ 'parent' ou 'etudiant'
            )
            
            # Si c'est un parent, créer les enfants
            if self.cleaned_data['type_client'] == 'parent':
                from enfants.models import Enfant
                
                noms = self.data.getlist('nom_enfant[]')
                prenoms = self.data.getlist('prenom_enfant[]')
                ages = self.data.getlist('age_enfant[]')
                niveaux = self.data.getlist('niveau_enfant[]')
                etablissements = self.data.getlist('etablissement_enfant[]')
                
                for i in range(len(noms)):
                    if noms[i] and prenoms[i]:
                        Enfant.objects.create(
                            client=client,
                            nom=noms[i],
                            prenom=prenoms[i],
                            age=int(ages[i]) if ages[i] else 0,
                            niveau=niveaux[i] if i < len(niveaux) else '',
                            etablissement=etablissements[i] if i < len(etablissements) else '',
                            matricule=''
                        )
            
            # Si c'est un étudiant
            elif self.cleaned_data['type_client'] == 'etudiant':
                from etudiants.models import Etudiant
                Etudiant.objects.create(
                    client=client,
                    age=0,
                    niveau=self.cleaned_data.get('niveau_etude', ''),
                    specialite=self.cleaned_data.get('specialite', ''),
                    nom_parent=self.cleaned_data['nom'],
                    telephone=self.cleaned_data['telephone'],
                    etablissement=self.cleaned_data.get('etablissement', ''),
                    matricule=self.cleaned_data.get('matricule', '')
                )
        return user


class ConnexionForm(AuthenticationForm):
    username = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={
        'class': 'w-full bg-surface-container-lowest border border-outline-variant rounded-xl px-4 py-3.5 focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all',
        'placeholder': 'votre@email.com'
    }))
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={
        'class': 'w-full bg-surface-container-lowest border border-outline-variant rounded-xl px-4 py-3.5 focus:ring-4 focus:ring-primary/10 focus:border-primary outline-none transition-all',
        'placeholder': '••••••••'
    }))