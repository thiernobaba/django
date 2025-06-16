from django.contrib import admin
from .models import Classe, Eleve, Matiere, Note, CahierTexte, Absence, Projet

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('niveau', 'description')
    search_fields = ('niveau',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(id=request.user.classe.id)
        return qs

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'classe', 'email', 'date_inscription')
    list_filter = ('classe', 'sexe')
    search_fields = ('nom', 'prenom', 'email')
    date_hierarchy = 'date_inscription'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classe=request.user.classe)
        return qs

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'coefficient', 'description')
    list_filter = ('classes',)
    search_fields = ('nom', 'code')
    filter_horizontal = ('classes',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classes=request.user.classe)
        return qs

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'matiere', 'valeur', 'type_evaluation', 'date')
    list_filter = ('matiere', 'type_evaluation', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'matiere__nom')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(eleve__classe=request.user.classe)
        return qs

@admin.register(CahierTexte)
class CahierTexteAdmin(admin.ModelAdmin):
    list_display = ('classe', 'matiere', 'date')
    list_filter = ('classe', 'matiere', 'date')
    date_hierarchy = 'date'
    search_fields = ('contenu',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classe=request.user.classe)
        return qs

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'justifiee')
    list_filter = ('justifiee', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'motif')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(eleve__classe=request.user.classe)
        return qs

@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'classe', 'matiere', 'date_attribution', 'date_limite')
    list_filter = ('classe', 'matiere', 'date_limite')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date_limite'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_responsable_classe:
            return qs.filter(classe=request.user.classe)
        return qs