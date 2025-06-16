# responsable_filiere/admin.py

from django.contrib import admin
from .models import Classe, Eleve, Matiere, Note, CahierTexte, Absence, Projet

@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    list_display = ('niveau', 'description')
    search_fields = ('niveau',)

@admin.register(Eleve)
class EleveAdmin(admin.ModelAdmin):
    list_display = ('numero_etudiant','nom', 'prenom', 'classe', 'email', 'date_inscription')
    list_filter = ('classe', 'sexe')
    search_fields = ('nom', 'prenom', 'email')
    date_hierarchy = 'date_inscription'

@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'coefficient', 'description')
    list_filter = ('classes',)
    search_fields = ('nom', 'code')
    filter_horizontal = ('classes',)

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'matiere', 'valeur', 'type_evaluation', 'date')
    list_filter = ('matiere', 'type_evaluation', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'matiere__nom')
    date_hierarchy = 'date'

@admin.register(CahierTexte)
class CahierTexteAdmin(admin.ModelAdmin):
    list_display = ('classe', 'matiere', 'date')
    list_filter = ('classe', 'matiere', 'date')
    date_hierarchy = 'date'
    search_fields = ('contenu',)

@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ('eleve', 'date', 'justifiee')
    list_filter = ('justifiee', 'date')
    search_fields = ('eleve__nom', 'eleve__prenom', 'motif')
    date_hierarchy = 'date'

@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    list_display = ('titre', 'classe', 'matiere', 'date_attribution', 'date_limite')
    list_filter = ('classe', 'matiere', 'date_limite')
    search_fields = ('titre', 'description')
    date_hierarchy = 'date_limite'