from django.contrib import admin
from .models import CahierTexte, Absence, Projet, RenduProjet, Retard, Observation

@admin.register(CahierTexte)
class CahierTexteAdmin(admin.ModelAdmin):
    list_display = ('classe', 'matiere', 'date', 'titre')
    list_filter = ('classe', 'matiere', 'date')
    search_fields = ('titre', 'contenu')
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classe=request.user.classe)
        return qs

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'matiere', 'heure_debut', 'heure_fin', 'justifiee')
    list_filter = ('justifiee', 'matiere', 'date', 'type_absence')
    search_fields = ('eleve__nom', 'eleve__prenom', 'motif')
    date_hierarchy = 'date'
    ordering = ['-date', '-heure_debut']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(eleve__classe=request.user.classe)
        elif request.user.is_eleve:
            return qs.filter(eleve__numero_etudiant=request.user.numero_etudiant)
        return qs

@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'classe', 'matiere', 'type_projet', 'date_limite', 'statut')
    list_filter = ('classe', 'matiere', 'type_projet', 'statut', 'date_limite')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date_limite'
    ordering = ['date_limite']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classe=request.user.classe)
        return qs

@admin.register(RenduProjet)
class RenduProjetAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'projet', 'date_rendu', 'note', 'est_en_retard')
    list_filter = ('projet__matiere', 'date_rendu', 'note')
    search_fields = ('eleve__nom', 'eleve__prenom', 'projet__titre')
    date_hierarchy = 'date_rendu'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(projet__classe=request.user.classe)
        elif request.user.is_eleve:
            return qs.filter(eleve__numero_etudiant=request.user.numero_etudiant)
        return qs

@admin.register(Retard)
class RetardAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'matiere', 'heure_arrivee', 'duree_retard', 'justifie')
    list_filter = ('justifie', 'matiere', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'motif')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(eleve__classe=request.user.classe)
        return qs

@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'type_observation', 'titre', 'suivi_necessaire')
    list_filter = ('type_observation', 'suivi_necessaire', 'matiere', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'titre', 'contenu')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(eleve__classe=request.user.classe)
        elif request.user.is_eleve:
            return qs.filter(eleve__numero_etudiant=request.user.numero_etudiant)
        return qs