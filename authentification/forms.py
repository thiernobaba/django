from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth.models import Permission
from responsable_filiere.models import Classe, Eleve

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'user_type', 'classe', 'numero_etudiant')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        self.fields['classe'].required = False
        self.fields['numero_etudiant'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        classe = cleaned_data.get('classe')
        numero_etudiant = cleaned_data.get('numero_etudiant')
        
        if user_type in ['responsable_classe', 'eleve'] and not classe:
            raise forms.ValidationError("La classe est obligatoire pour ce type d'utilisateur.")
        
        if user_type == 'eleve' and not numero_etudiant:
            raise forms.ValidationError("Le numéro étudiant est obligatoire pour les élèves.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Attribuer des permissions en fonction du type d'utilisateur
            if user.user_type == 'responsable_filiere':
                permissions = [
                    'responsable_filiere.can_view_all_eleves',
                    'responsable_filiere.can_edit_all_eleves',
                    'responsable_filiere.can_manage_matieres',
                    'responsable_filiere.can_manage_notes',
                ]
                for perm in permissions:
                    user.user_permissions.add(Permission.objects.get(codename=perm.split('.')[-1]))
            elif user.user_type == 'responsable_classe':
                user.user_permissions.add(
                    Permission.objects.get(codename='can_view_own_classe')
                )
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['password'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Nom d\'utilisateur'
        self.fields['password'].widget.attrs['placeholder'] = 'Mot de passe'