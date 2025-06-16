# responsable_filiere/forms.py

from django import forms
from .models import Eleve, Matiere, Note, Classe
from django.forms import inlineformset_factory

class EleveForm(forms.ModelForm):
    """Formulaire pour la création et modification d'un élève"""
    class Meta:
        model = Eleve
        fields = ['numero_etudiant', 'nom', 'prenom', 'date_naissance', 'sexe', 'email', 
                  'telephone', 'adresse', 'classe', 'photo']
        widgets = {
            'date_naissance': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }


class MatiereForm(forms.ModelForm):
    """Formulaire pour la création et modification d'une matière"""
    class Meta:
        model = Matiere
        fields = ['nom', 'code', 'coefficient', 'description', 'classes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'classes': forms.CheckboxSelectMultiple(),
        }


class NoteForm(forms.ModelForm):
    """Formulaire pour la saisie d'une note"""
    class Meta:
        model = Note
        fields = ['eleve', 'matiere', 'valeur', 'date', 'type_evaluation', 'commentaire']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'commentaire': forms.Textarea(attrs={'rows': 2}),
        }


class NoteMultipleForm(forms.Form):
    """Formulaire pour la saisie de notes pour plusieurs élèves d'une classe"""
    classe = forms.ModelChoiceField(queryset=Classe.objects.all())
    matiere = forms.ModelChoiceField(queryset=Matiere.objects.all())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    type_evaluation = forms.ChoiceField(choices=Note._meta.get_field('type_evaluation').choices)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Récupère l'utilisateur si fourni
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'is_responsable_classe') and self.user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=self.user.classe.id)
            self.fields['classe'].initial = self.user.classe
            self.fields['classe'].disabled = True
            
class NoteFilterForm(forms.Form):
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=False,
        empty_label="Toutes les classes",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    matiere = forms.ModelChoiceField(
        queryset=Matiere.objects.all(),
        required=False,
        empty_label="Toutes les matières",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Restreindre les choix selon le type d'utilisateur
        if user and hasattr(user, 'is_responsable_classe') and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
        elif user and hasattr(user, 'is_eleve') and user.is_eleve:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)
            
class EleveSelectForm(forms.Form):
    """Formulaire pour sélectionner une classe et voir les élèves"""
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        empty_label="Sélectionnez une classe",
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class MatiereSelectForm(forms.Form):
    """Formulaire pour filtrer les matières par classe"""
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        empty_label="Toutes les classes",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# Formulaire dynamique pour saisir les notes de plusieurs élèves à la fois
NoteFormSet = inlineformset_factory(
    Matiere, 
    Note, 
    fields=('eleve', 'valeur', 'commentaire'),
    extra=1,
    can_delete=False
)