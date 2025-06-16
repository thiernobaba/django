from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.db.models import Count, Q, Avg
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from authentification.mixins import ResponsableClasseRequiredMixin, EleveRequiredMixin
import pandas as pd
from io import BytesIO
import xlsxwriter

from .models import CahierTexte, Absence, Projet, RenduProjet, Retard, Observation
from .forms import (
    CahierTexteForm, AbsenceForm, AbsenceMultipleForm, ProjetForm, 
    RenduProjetForm, RetardForm, ObservationForm, ClasseSelectForm, 
    FiltreDateForm
)
from responsable_filiere.models import Classe, Eleve, Matiere

class DashboardView(LoginRequiredMixin, ResponsableClasseRequiredMixin, TemplateView):
    """Vue du tableau de bord pour le responsable de classe"""
    template_name = 'responsable_classe/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        # Filtrer par la classe de l'utilisateur
        queryset = CahierTexte.objects.filter(classe=self.request.user.classe)
        absences = Absence.objects.filter(eleve__classe=self.request.user.classe)
        projets = Projet.objects.filter(classe=self.request.user.classe)
        retards = Retard.objects.filter(eleve__classe=self.request.user.classe)
        observations = Observation.objects.filter(eleve__classe=self.request.user.classe)
        
        # Statistiques générales
        context['total_cahiers'] = queryset.count()
        context['absences_non_justifiees'] = absences.filter(justifiee=False).count()
        context['projets_en_cours'] = projets.filter(
            statut__in=['ATTRIBUE', 'EN_COURS']
        ).count()
        context['retards_aujourd_hui'] = retards.filter(date=today).count()
        
        # Projets à échéance proche (7 jours)
        date_limite = today + timedelta(days=7)
        context['projets_urgents'] = projets.filter(
            date_limite__lte=date_limite,
            statut__in=['ATTRIBUE', 'EN_COURS']
        ).order_by('date_limite')[:5]
        
        # Dernières observations
        context['dernieres_observations'] = observations.select_related(
            'eleve', 'matiere'
        ).order_by('-date')[:5]
        
        # Absences récentes non justifiées
        context['absences_recentes'] = absences.filter(
            justifiee=False
        ).select_related('eleve', 'matiere').order_by('-date')[:5]
        
        return context

# === CAHIER DE TEXTE ===
class CahierTexteListView(LoginRequiredMixin, ListView):
    model = CahierTexte
    template_name = 'responsable_classe/cahier_texte_list.html'
    context_object_name = 'cahiers'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            queryset = queryset.filter(classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            queryset = queryset.filter(classe=self.request.user.classe)
        
        classe_id = self.request.GET.get('classe')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if classe_id and self.request.user.has_perm('responsable_filiere.can_view_all_eleves'):
            queryset = queryset.filter(classe_id=classe_id)
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
            
        return queryset.select_related('classe', 'matiere')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = FiltreDateForm(self.request.GET or None, user=self.request.user)
        return context

class CahierTexteDetailView(LoginRequiredMixin, DetailView):
    model = CahierTexte
    template_name = 'responsable_classe/cahier_texte_detail.html'
    context_object_name = 'cahier'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            return queryset.filter(classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            return queryset.filter(classe=self.request.user.classe)
        return queryset

class CahierTexteCreateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, CreateView):
    model = CahierTexte
    form_class = CahierTexteForm
    template_name = 'responsable_classe/cahier_texte_form.html'
    success_url = reverse_lazy('responsable_classe:cahier_texte_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class CahierTexteUpdateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, UpdateView):
    model = CahierTexte
    form_class = CahierTexteForm
    template_name = 'responsable_classe/cahier_texte_form.html'
    
    def get_success_url(self):
        return reverse_lazy('responsable_classe:cahier_texte_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return super().get_queryset().filter(classe=self.request.user.classe)

class CahierTexteDeleteView(LoginRequiredMixin, ResponsableClasseRequiredMixin, DeleteView):
    model = CahierTexte
    template_name = 'responsable_classe/cahier_texte_confirm_delete.html'
    success_url = reverse_lazy('responsable_classe:cahier_texte_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(classe=self.request.user.classe)

# === ABSENCES ===
@login_required
@permission_required('responsable_classe.can_manage_absences')
def absence_list(request):
    """Liste des absences avec filtrage"""
    form = FiltreDateForm(request.GET or None, user=request.user)
    absences = Absence.objects.select_related('eleve', 'matiere')
    
    if request.user.is_responsable_classe:
        absences = absences.filter(eleve__classe=request.user.classe)
    elif request.user.is_eleve:
        absences = absences.filter(eleve__numero_etudiant=request.user.numero_etudiant)
    
    if form.is_valid():
        classe = form.cleaned_data.get('classe')
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        
        if classe and request.user.has_perm('responsable_filiere.can_view_all_eleves'):
            absences = absences.filter(eleve__classe=classe)
        if date_debut:
            absences = absences.filter(date__gte=date_debut)
        if date_fin:
            absences = absences.filter(date__lte=date_fin)
    
    absences = absences.order_by('-date', '-heure_debut')
    
    return render(request, 'responsable_classe/absence_list.html', {
        'absences': absences,
        'form': form
    })

@login_required
@permission_required('responsable_classe.can_manage_absences')
def absence_create(request):
    """Créer une absence"""
    if request.method == 'POST':
        form = AbsenceForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            absence = form.save(commit=False)
            if request.user.is_responsable_classe and absence.eleve.classe != request.user.classe:
                return HttpResponseForbidden("Vous ne pouvez enregistrer des absences que pour votre classe.")
            absence.save()
            return redirect('responsable_classe:absence_list')
    else:
        form = AbsenceForm(user=request.user)
    
    return render(request, 'responsable_classe/absence_form.html', {
        'form': form,
        'title': 'Créer une absence'
    })

@login_required
@permission_required('responsable_classe.can_manage_absences')
def absence_multiple_create(request):
    """Créer plusieurs absences en une fois"""
    if request.method == 'POST':
        form = AbsenceMultipleForm(request.POST, user=request.user)
        if form.is_valid():
            eleves = form.cleaned_data['eleves']
            if request.user.is_responsable_classe and form.cleaned_data['classe'] != request.user.classe:
                return HttpResponseForbidden("Vous ne pouvez enregistrer des absences que pour votre classe.")
            for eleve in eleves:
                Absence.objects.create(
                    eleve=eleve,
                    date=form.cleaned_data['date'],
                    matiere=form.cleaned_data['matiere'],
                    type_absence=form.cleaned_data['type_absence'],
                    heure_debut=form.cleaned_data['heure_debut'],
                    heure_fin=form.cleaned_data['heure_fin']
                )
            return redirect('responsable_classe:absence_list')
    else:
        form = AbsenceMultipleForm(user=request.user)
    
    return render(request, 'responsable_classe/absence_multiple_form.html', {
        'form': form,
        'title': 'Marquer plusieurs absences'
    })

class AbsenceUpdateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, UpdateView):
    model = Absence
    form_class = AbsenceForm
    template_name = 'responsable_classe/absence_form.html'
    success_url = reverse_lazy('responsable_classe:absence_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier une absence'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

class AbsenceDeleteView(LoginRequiredMixin, ResponsableClasseRequiredMixin, DeleteView):
    model = Absence
    template_name = 'responsable_classe/absence_confirm_delete.html'
    success_url = reverse_lazy('responsable_classe:absence_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

@login_required
@permission_required('responsable_classe.can_manage_absences')
def rapport_absences(request):
    """Génère un rapport d'absences au format Excel"""
    queryset = Absence.objects.select_related('eleve', 'matiere', 'eleve__classe')
    
    if request.user.is_responsable_classe:
        queryset = queryset.filter(eleve__classe=request.user.classe)
    elif request.user.is_eleve:
        queryset = queryset.filter(eleve__numero_etudiant=request.user.numero_etudiant)
    
    classe_id = request.GET.get('classe')
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    if classe_id and request.user.has_perm('responsable_filiere.can_view_all_eleves'):
        queryset = queryset.filter(eleve__classe_id=classe_id)
    if date_debut:
        queryset = queryset.filter(date__gte=date_debut)
    if date_fin:
        queryset = queryset.filter(date__lte=date_fin)
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Rapport Absences')
    
    headers = [
        'Élève', 'Classe', 'Date', 'Matière', 'Type', 
        'Heure début', 'Heure fin', 'Durée (min)', 
        'Justifiée', 'Motif'
    ]
    
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    for row, absence in enumerate(queryset, 1):
        worksheet.write(row, 0, str(absence.eleve))
        worksheet.write(row, 1, str(absence.eleve.classe))
        worksheet.write(row, 2, absence.date.strftime('%d/%m/%Y'))
        worksheet.write(row, 3, str(absence.matiere))
        worksheet.write(row, 4, absence.get_type_absence_display())
        worksheet.write(row, 5, absence.heure_debut.strftime('%H:%M'))
        worksheet.write(row, 6, absence.heure_fin.strftime('%H:%M'))
        worksheet.write(row, 7, absence.duree_minutes)
        worksheet.write(row, 8, 'Oui' if absence.justifiee else 'Non')
        worksheet.write(row, 9, absence.motif or '')
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="rapport_absences_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    response.write(output.read())
    
    return response

# === PROJETS ===
class ProjetListView(LoginRequiredMixin, ListView):
    model = Projet
    template_name = 'responsable_classe/projet_list.html'
    context_object_name = 'projets'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            queryset = queryset.filter(classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            queryset = queryset.filter(classe=self.request.user.classe)
        
        statut = self.request.GET.get('statut')
        classe_id = self.request.GET.get('classe')
        
        if statut:
            queryset = queryset.filter(statut=statut)
        if classe_id and self.request.user.has_perm('responsable_filiere.can_view_all_eleves'):
            queryset = queryset.filter(classe_id=classe_id)
            
        return queryset.select_related('classe', 'matiere')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuts'] = Projet.STATUT_CHOICES
        context['classes'] = Classe.objects.all()
        return context

class ProjetDetailView(LoginRequiredMixin, DetailView):
    model = Projet
    template_name = 'responsable_classe/projet_detail.html'
    context_object_name = 'projet'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            return queryset.filter(classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            return queryset.filter(classe=self.request.user.classe)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rendus = RenduProjet.objects.filter(projet=self.object).select_related('eleve')
        if self.request.user.is_eleve:
            rendus = rendus.filter(eleve__numero_etudiant=self.request.user.numero_etudiant)
        context['rendus'] = rendus.order_by('date_rendu')
        
        total_eleves = self.object.classe.eleves.count()
        rendus_count = context['rendus'].count()
        context['stats'] = {
            'total_eleves': total_eleves,
            'rendus_count': rendus_count,
            'taux_rendu': (rendus_count / total_eleves * 100) if total_eleves > 0 else 0
        }
        
        return context

class ProjetCreateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, CreateView):
    model = Projet
    form_class = ProjetForm
    template_name = 'responsable_classe/projet_form.html'
    success_url = reverse_lazy('responsable_classe:projet_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ProjetUpdateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, UpdateView):
    model = Projet
    form_class = ProjetForm
    template_name = 'responsable_classe/projet_form.html'
    
    def get_success_url(self):
        return reverse_lazy('responsable_classe:projet_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return super().get_queryset().filter(classe=self.request.user.classe)

class ProjetDeleteView(LoginRequiredMixin, ResponsableClasseRequiredMixin, DeleteView):
    model = Projet
    template_name = 'responsable_classe/projet_confirm_delete.html'
    success_url = reverse_lazy('responsable_classe:projet_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(classe=self.request.user.classe)

@login_required
@permission_required('responsable_classe.can_manage_projets')
def corriger_rendus(request, projet_id):
    """Interface de correction des rendus d'un projet"""
    projet = get_object_or_404(Projet, id=projet_id)
    if request.user.is_responsable_classe and projet.classe != request.user.classe:
        return HttpResponseForbidden("Vous ne pouvez corriger que les rendus de votre classe.")
    
    rendus = RenduProjet.objects.filter(projet=projet).select_related('eleve')
    
    if request.method == 'POST':
        for rendu in rendus:
            note = request.POST.get(f'note_{rendu.id}')
            commentaire = request.POST.get(f'commentaire_{rendu.id}')
            
            if note:
                rendu.note = float(note)
                rendu.commentaire_professeur = commentaire
                rendu.date_correction = timezone.now()
                rendu.save()
        
        projet.statut = 'CORRIGE'
        projet.save()
        
        return redirect('responsable_classe:projet_detail', pk=projet.id)
    
    return render(request, 'responsable_classe/corriger_rendus.html', {
        'projet': projet,
        'rendus': rendus
    })

# === RETARDS ===
@login_required
@permission_required('responsable_classe.can_manage_retards')
def retard_list(request):
    """Liste des retards avec filtrage"""
    form = FiltreDateForm(request.GET or None, user=request.user)
    retards = Retard.objects.select_related('eleve', 'matiere')
    
    if request.user.is_responsable_classe:
        retards = retards.filter(eleve__classe=request.user.classe)
    elif request.user.is_eleve:
        retards = retards.filter(eleve__numero_etudiant=request.user.numero_etudiant)
    
    if form.is_valid():
        classe = form.cleaned_data.get('classe')
        date_debut = form.cleaned_data.get('date_debut')
        date_fin = form.cleaned_data.get('date_fin')
        
        if classe and request.user.has_perm('responsable_filiere.can_view_all_eleves'):
            retards = retards.filter(eleve__classe=classe)
        if date_debut:
            retards = retards.filter(date__gte=date_debut)
        if date_fin:
            retards = retards.filter(date__lte=date_fin)
    
    retards = retards.order_by('-date', '-heure_arrivee')
    
    return render(request, 'responsable_classe/retard_list.html', {
        'retards': retards,
        'form': form
    })

@login_required
@permission_required('responsable_classe.can_manage_retards')
def retard_create(request):
    """Créer un retard"""
    if request.method == 'POST':
        form = RetardForm(request.POST, user=request.user)
        if form.is_valid():
            retard = form.save(commit=False)
            if request.user.is_responsable_classe and retard.eleve.classe != request.user.classe:
                return HttpResponseForbidden("Vous ne pouvez enregistrer des retards que pour votre classe.")
            retard.save()
            return redirect('responsable_classe:retard_list')
    else:
        form = RetardForm(user=request.user)
    
    return render(request, 'responsable_classe/retard_form.html', {
        'form': form,
        'title': 'Enregistrer un retard'
    })

class RetardUpdateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, UpdateView):
    model = Retard
    form_class = RetardForm
    template_name = 'responsable_classe/retard_form.html'
    success_url = reverse_lazy('responsable_classe:retard_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Modifier un retard'
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

class RetardDeleteView(LoginRequiredMixin, ResponsableClasseRequiredMixin, DeleteView):
    model = Retard
    template_name = 'responsable_classe/retard_confirm_delete.html'
    success_url = reverse_lazy('responsable_classe:retard_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

# === OBSERVATIONS ===
class ObservationListView(LoginRequiredMixin, ListView):
    model = Observation
    template_name = 'responsable_classe/observation_list.html'
    context_object_name = 'observations'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            queryset = queryset.filter(eleve__classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            queryset = queryset.filter(eleve__numero_etudiant=self.request.user.numero_etudiant)
        
        type_obs = self.request.GET.get('type')
        classe_id = self.request.GET.get('classe')
        
        if type_obs:
            queryset = queryset.filter(type_observation=type_obs)
        if classe_id and self.request.user.has_perm('responsable_filiere.can_view_all_eleves'):
            queryset = queryset.filter(eleve__classe_id=classe_id)
            
        return queryset.select_related('eleve', 'matiere', 'eleve__classe')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['types'] = Observation.TYPE_OBSERVATION_CHOICES
        context['classes'] = Classe.objects.all()
        return context

class ObservationDetailView(LoginRequiredMixin, DetailView):
    model = Observation
    template_name = 'responsable_classe/observation_detail.html'
    context_object_name = 'observation'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            return queryset.filter(eleve__classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            return queryset.filter(eleve__numero_etudiant=self.request.user.numero_etudiant)
        return queryset

class ObservationCreateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, CreateView):
    model = Observation
    form_class = ObservationForm
    template_name = 'responsable_classe/observation_form.html'
    success_url = reverse_lazy('responsable_classe:observation_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class ObservationUpdateView(LoginRequiredMixin, ResponsableClasseRequiredMixin, UpdateView):
    model = Observation
    form_class = ObservationForm
    template_name = 'responsable_classe/observation_form.html'
    
    def get_success_url(self):
        return reverse_lazy('responsable_classe:observation_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

class ObservationDeleteView(LoginRequiredMixin, ResponsableClasseRequiredMixin, DeleteView):
    model = Observation
    template_name = 'responsable_classe/observation_confirm_delete.html'
    success_url = reverse_lazy('responsable_classe:observation_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(eleve__classe=self.request.user.classe)

# === STATISTIQUES ET RAPPORTS ===
@login_required
def statistiques_classe(request):
    """Page de statistiques pour les classes"""
    form = ClasseSelectForm(request.GET or None, user=request.user)
    stats = {}
    
    if form.is_valid() and form.cleaned_data.get('classe'):
        classe = form.cleaned_data['classe']
        if request.user.is_responsable_classe and classe != request.user.classe:
            return HttpResponseForbidden("Vous ne pouvez voir les statistiques que de votre classe.")
        
        date_fin = timezone.now().date()
        date_debut = date_fin - timedelta(days=30)
        
        absences = Absence.objects.filter(
            eleve__classe=classe,
            date__range=[date_debut, date_fin]
        )
        
        stats['absences'] = {
            'total': absences.count(),
            'justifiees': absences.filter(justifiee=True).count(),
            'non_justifiees': absences.filter(justifiee=False).count(),
            'par_eleve': absences.values('eleve__nom', 'eleve__prenom').annotate(
                total=Count('id')
            ).order_by('-total')[:5]
        }
        
        retards = Retard.objects.filter(
            eleve__classe=classe,
            date__range=[date_debut, date_fin]
        )
        
        stats['retards'] = {
            'total': retards.count(),
            'justifies': retards.filter(justifie=True).count(),
            'par_eleve': retards.values('eleve__nom', 'eleve__prenom').annotate(
                total=Count('id')
            ).order_by('-total')[:5]
        }
        
        projets = Projet.objects.filter(classe=classe)
        rendus = RenduProjet.objects.filter(
            projet__classe=classe,
            date_rendu__date__range=[date_debut, date_fin]
        )
        
        stats['projets'] = {
            'total': projets.count(),
            'en_cours': projets.filter(statut__in=['ATTRIBUE', 'EN_COURS']).count(),
            'corriges': projets.filter(statut='CORRIGE').count(),
            'note_moyenne': rendus.aggregate(Avg('note'))['note__avg'] or 0,
            'taux_rendu': (rendus.count() / (projets.count() * classe.eleves.count()) * 100) 
                         if projets.count() > 0 and classe.eleves.count() > 0 else 0
        }
        
        observations = Observation.objects.filter(
            eleve__classe=classe,
            date__range=[date_debut, date_fin]
        )
        
        stats['observations'] = {
            'total': observations.count(),
            'positives': observations.filter(type_observation='POSITIVE').count(),
            'negatives': observations.filter(type_observation='NEGATIVE').count(),
            'disciplinaires': observations.filter(type_observation='DISCIPLINAIRE').count()
        }
    
    return render(request, 'responsable_classe/statistiques.html', {
        'form': form,
        'stats': stats
    })

@login_required
def ajax_eleves_classe(request):
    """Retourne la liste des élèves d'une classe en AJAX"""
    classe_id = request.GET.get('classe_id')
    if classe_id:
        if request.user.is_responsable_classe and str(request.user.classe.id) != classe_id:
            return JsonResponse({'error': 'Accès non autorisé'}, status=403)
        eleves = Eleve.objects.filter(classe_id=classe_id).values('id', 'nom', 'prenom')
        return JsonResponse({'eleves': list(eleves)})
    return JsonResponse({'eleves': []})
