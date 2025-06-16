from django import forms
from .models import CahierTexte, Absence, Projet, RenduProjet, Retard, Observation
from responsable_filiere.models import Classe, Eleve, Matiere

class CahierTexteForm(forms.ModelForm):
    """Formulaire pour le cahier de texte"""
    class Meta:
        model = CahierTexte
        fields = ['classe', 'matiere', 'date', 'titre', 'contenu', 'travail_a_faire']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'contenu': forms.Textarea(attrs={'rows': 4}),
            'travail_a_faire': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['classe'].initial = user.classe
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)

class AbsenceForm(forms.ModelForm):
    """Formulaire pour enregistrer une absence"""
    class Meta:
        model = Absence
        fields = ['eleve', 'date', 'matiere', 'type_absence', 'heure_debut', 'heure_fin', 
                  'justifiee', 'motif', 'date_justification', 'document_justificatif']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'date_justification': forms.DateInput(attrs={'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'type': 'time'}),
            'motif': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['eleve'].queryset = Eleve.objects.filter(classe=user.classe)
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)

class AbsenceMultipleForm(forms.Form):
    """Formulaire pour marquer plusieurs élèves absents en une fois"""
    classe = forms.ModelChoiceField(queryset=Classe.objects.all())
    matiere = forms.ModelChoiceField(queryset=Matiere.objects.all())
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    type_absence = forms.ChoiceField(choices=Absence.TYPE_ABSENCE_CHOICES)
    heure_debut = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    heure_fin = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    eleves = forms.ModelMultipleChoiceField(
        queryset=Eleve.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['classe'].initial = user.classe
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)
            self.fields['eleves'].queryset = Eleve.objects.filter(classe=user.classe)
        elif 'classe' in self.data:
            try:
                classe_id = int(self.data.get('classe'))
                self.fields['eleves'].queryset = Eleve.objects.filter(classe_id=classe_id)
            except (ValueError, TypeError):
                pass

class ProjetForm(forms.ModelForm):
    """Formulaire pour créer/modifier un projet"""
    class Meta:
        model = Projet
        fields = ['titre', 'description', 'matiere', 'classe', 'type_projet', 'date_attribution',
                  'date_limite', 'coefficient', 'consignes', 'fichier_sujet']
        widgets = {
            'date_attribution': forms.DateInput(attrs={'type': 'date'}),
            'date_limite': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'consignes': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['classe'].initial = user.classe
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)

class RenduProjetForm(forms.ModelForm):
    """Formulaire pour la correction d'un rendu de projet"""
    class Meta:
        model = RenduProjet
        fields = ['note', 'commentaire_professeur']
        widgets = {
            'commentaire_professeur': forms.Textarea(attrs={'rows': 4}),
        }

class RetardForm(forms.ModelForm):
    """Formulaire pour enregistrer un retard"""
    class Meta:
        model = Retard
        fields = ['eleve', 'date', 'matiere', 'heure_arrivee', 'heure_prevue', 
                  'motif', 'justifie', 'sanction']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'type': 'time'}),
            'heure_prevue': forms.TimeInput(attrs={'type': 'time'}),
            'motif': forms.Textarea(attrs={'rows': 3}),
            'sanction': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['eleve'].queryset = Eleve.objects.filter(classe=user.classe)
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)

class ObservationForm(forms.ModelForm):
    """Formulaire pour créer une observation"""
    class Meta:
        model = Observation
        fields = ['eleve', 'date', 'matiere', 'type_observation', 'titre', 
                  'contenu', 'action_menee', 'suivi_necessaire']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'contenu': forms.Textarea(attrs={'rows': 4}),
            'action_menee': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['eleve'].queryset = Eleve.objects.filter(classe=user.classe)
            self.fields['matiere'].queryset = Matiere.objects.filter(classes=user.classe)

class ClasseSelectForm(forms.Form):
    """Formulaire pour sélectionner une classe"""
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        empty_label="Sélectionnez une classe",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['classe'].initial = user.classe

class FiltreDateForm(forms.Form):
    """Formulaire pour filtrer par date"""
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    classe = forms.ModelChoiceField(
        queryset=Classe.objects.all(),
        required=False,
        empty_label="Toutes les classes"
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_responsable_classe:
            self.fields['classe'].queryset = Classe.objects.filter(id=user.classe.id)
            self.fields['classe'].initial = user.classe