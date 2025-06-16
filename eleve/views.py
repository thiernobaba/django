from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from responsable_filiere.models import Eleve, Note
from responsable_classe.models import Projet, Absence, CahierTexte
from eleve.models import Notification
from django.utils import timezone
import logging

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'eleve/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            context['eleve'] = eleve
            context['dernieres_notes'] = Note.objects.filter(eleve=eleve).select_related('matiere').order_by('-date')[:5]
            context['dernieres_absences'] = Absence.objects.filter(eleve=eleve).order_by('-date')[:5]
            context['projets_en_cours'] = Projet.objects.filter(classe=eleve.classe).order_by('date_limite')[:5]
            context['derniers_cahiers'] = CahierTexte.objects.filter(classe=eleve.classe).select_related('matiere').order_by('-date')[:5]
        except Eleve.DoesNotExist:
            context['error'] = "Profil élève non trouvé"
            context['eleve'] = None
            context['dernieres_notes'] = []
            context['dernieres_absences'] = []
            context['projets_en_cours'] = []
            context['derniers_cahiers'] = []

        if self.request.user.is_authenticated:
            context['unread_notifications'] = Notification.objects.filter(
                user=self.request.user,
                is_read=False
            ).count()
            context['recent_notifications'] = Notification.objects.filter(
                user=self.request.user
            ).order_by('-created_at')[:5]
        else:
            context['unread_notifications'] = 0
            context['recent_notifications'] = []
            
        return context

class EleveDetailView(LoginRequiredMixin, DetailView):
    model = Eleve
    template_name = 'eleve/eleve_detail.html'
    context_object_name = 'eleve'

    def get_object(self):
        try:
            return Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
        except Eleve.DoesNotExist:
            messages.error(self.request, "Profil élève non trouvé")
            return None

class NoteListView(LoginRequiredMixin, ListView):
    model = Note
    template_name = 'eleve/notes_list.html'
    context_object_name = 'notes'
    paginate_by = 20

    def get_queryset(self):
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            return Note.objects.filter(eleve=eleve).select_related('matiere').order_by('-date')
        except Eleve.DoesNotExist:
            return Note.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            moyenne = Note.objects.filter(eleve=eleve).aggregate(Avg('valeur'))['valeur__avg']
            context['moyenne_generale'] = round(moyenne, 2) if moyenne else None
            context['eleve'] = eleve
        except Eleve.DoesNotExist:
            context['moyenne_generale'] = None
            context['eleve'] = None
            messages.error(self.request, "Profil élève non trouvé")
        return context

class AbsenceListView(LoginRequiredMixin, ListView):
    model = Absence
    template_name = 'eleve/absences_list.html'
    context_object_name = 'absences'
    paginate_by = 20

    def get_queryset(self):
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            return Absence.objects.filter(eleve=eleve).order_by('-date')
        except Eleve.DoesNotExist:
            return Absence.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            context['eleve'] = eleve
            context['total_absences'] = self.get_queryset().count()
            context['absences_non_justifiees'] = self.get_queryset().filter(justifiee=False).count()
        except Eleve.DoesNotExist:
            context['eleve'] = None
            context['total_absences'] = 0
            context['absences_non_justifiees'] = 0
            messages.error(self.request, "Profil élève non trouvé")
        return context

class ProjetListView(LoginRequiredMixin, ListView):
    model = Projet
    template_name = 'eleve/projets_list.html'
    context_object_name = 'projets'
    paginate_by = 10

    def get_queryset(self):
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            return Projet.objects.filter(classe=eleve.classe).select_related('matiere').order_by('date_limite')
        except Eleve.DoesNotExist:
            return Projet.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            context['eleve'] = eleve
            
            # Calculer les statistiques des projets
            queryset = self.get_queryset()
            context['projets_en_retard'] = queryset.filter(date_limite__lt=context['today']).count()
            context['projets_a_temps'] = queryset.filter(date_limite__gte=context['today']).count()
            
        except Eleve.DoesNotExist:
            context['eleve'] = None
            context['projets_en_retard'] = 0
            context['projets_a_temps'] = 0
            messages.error(self.request, "Profil élève non trouvé")
        return context

class CahierTexteListView(LoginRequiredMixin, ListView):
    model = CahierTexte
    template_name = 'eleve/cahier_texte_list.html'
    context_object_name = 'cahiers'
    paginate_by = 10

    def get_queryset(self):
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            return CahierTexte.objects.filter(classe=eleve.classe).select_related('matiere').order_by('-date')
        except Eleve.DoesNotExist:
            return CahierTexte.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            context['eleve'] = eleve
        except Eleve.DoesNotExist:
            context['eleve'] = None
            messages.error(self.request, "Profil élève non trouvé")
        return context

class CahierTexteDetailView(LoginRequiredMixin, DetailView):
    model = CahierTexte
    template_name = 'eleve/cahier_texte_detail.html'
    context_object_name = 'cahier'

    def get_object(self):
        try:
            eleve = Eleve.objects.get(numero_etudiant=self.request.user.numero_etudiant)
            cahier = get_object_or_404(CahierTexte, pk=self.kwargs['pk'], classe=eleve.classe)
            return cahier
        except Eleve.DoesNotExist:
            messages.error(self.request, "Profil élève non trouvé")
            return None
