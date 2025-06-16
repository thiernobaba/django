from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.forms import formset_factory
from django.db.models import Avg, Count
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
import pandas as pd
import hashlib
import xlsxwriter
from io import BytesIO
from authentification.mixins import ResponsableFiliereRequiredMixin, ResponsableClasseRequiredMixin, EleveRequiredMixin
from responsable_classe.models import Eleve, Matiere, Classe, CahierTexte, Absence, Projet, Retard
from .forms import (
    EleveForm, MatiereForm, NoteForm, EleveSelectForm, 
    MatiereSelectForm, NoteMultipleForm, NoteFormSet,NoteFilterForm
)
from .models import Note


class DashboardView(ResponsableFiliereRequiredMixin, TemplateView):
    template_name = 'responsable_filiere/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_eleves'] = Eleve.objects.count()
        context['total_classes'] = Classe.objects.count()
        context['total_matieres'] = Matiere.objects.count()
        context['eleves_par_classe'] = Classe.objects.annotate(
            nb_eleves=Count('eleves')
        ).values('niveau', 'nb_eleves')
        context['projets_a_venir'] = Projet.objects.order_by('date_limite')[:5]
        return context

class EleveListView(LoginRequiredMixin, ListView):
    model = Eleve
    template_name = 'responsable_filiere/eleve_list.html'
    context_object_name = 'eleves'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EleveSelectForm(self.request.GET or None)
        context['fields'] = ['numero_etudiant', 'nom', 'prenom', 'classe', 'email']
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            queryset = queryset.filter(classe=self.request.user.classe)
        elif self.request.user.is_eleve:
            queryset = queryset.filter(numero_etudiant=self.request.user.numero_etudiant)
        classe_id = self.request.GET.get('classe')
        if classe_id and self.request.user.is_responsable_filiere:
            queryset = queryset.filter(classe_id=classe_id)
        return queryset

class EleveDetailView(LoginRequiredMixin, DetailView):
    model = Eleve
    template_name = 'responsable_filiere/eleve_detail.html'
    context_object_name = 'eleve'
    
    def get_object(self, queryset=None):
        if self.request.user.is_eleve:
            return get_object_or_404(Eleve, numero_etudiant=self.request.user.numero_etudiant)
        return super().get_object(queryset)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        eleve = self.get_object()
        context['notes'] = Note.objects.filter(eleve=eleve).order_by('matiere')
        moyenne_generale = Note.objects.filter(eleve=eleve).aggregate(Avg('valeur'))
        context['moyenne_generale'] = moyenne_generale['valeur__avg']
        context['absences'] = Absence.objects.filter(eleve=eleve).order_by('-date')
        context['retards'] = Retard.objects.filter(eleve = eleve).order_by('-date')
        return context

class EleveCreateView(ResponsableFiliereRequiredMixin, CreateView):
    model = Eleve
    form_class = EleveForm
    template_name = 'responsable_filiere/eleve_form.html'
    success_url = reverse_lazy('responsable_filiere:eleve_list')

class EleveUpdateView(ResponsableFiliereRequiredMixin, UpdateView):
    model = Eleve
    form_class = EleveForm
    template_name = 'responsable_filiere/eleve_form.html'
    success_url = reverse_lazy('responsable_filiere:eleve_list')

class EleveDeleteView(ResponsableFiliereRequiredMixin, DeleteView):
    model = Eleve
    template_name = 'responsable_filiere/eleve_confirm_delete.html'
    success_url = reverse_lazy('responsable_filiere:eleve_list')

class MatiereListView(LoginRequiredMixin, ListView):
    model = Matiere
    template_name = 'responsable_filiere/matiere_list.html'
    context_object_name = 'matieres'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MatiereSelectForm(self.request.GET or None)
        return context
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_responsable_classe:
            queryset = queryset.filter(classes=self.request.user.classe)
        classe_id = self.request.GET.get('classe')
        if classe_id and self.request.user.is_responsable_filiere:
            queryset = queryset.filter(classes__id=classe_id)
        return queryset

class MatiereDetailView(LoginRequiredMixin, DetailView):
    model = Matiere
    template_name = 'responsable_filiere/matiere_detail.html'
    context_object_name = 'matiere'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        matiere = self.get_object()
        context['classes'] = matiere.classes.all()
        context['moyenne_matiere'] = matiere.notes.aggregate(avg=Avg('valeur'))['avg']
        return context

class MatiereCreateView(ResponsableFiliereRequiredMixin, CreateView):
    model = Matiere
    form_class = MatiereForm
    template_name = 'responsable_filiere/matiere_form.html'
    success_url = reverse_lazy('responsable_filiere:matiere_list')

class MatiereUpdateView(ResponsableFiliereRequiredMixin, UpdateView):
    model = Matiere
    form_class = MatiereForm
    template_name = 'responsable_filiere/matiere_form.html'
    success_url = reverse_lazy('responsable_filiere:matiere_list')

class MatiereDeleteView(ResponsableFiliereRequiredMixin, DeleteView):
    model = Matiere
    template_name = 'responsable_filiere/matiere_confirm_delete.html'
    success_url = reverse_lazy('responsable_filiere:matiere_list')

@login_required
@permission_required('responsable_filiere.can_manage_notes')
def note_list(request):
    # Commencer avec toutes les notes
    notes = Note.objects.all().select_related('eleve', 'matiere', 'eleve__classe').order_by('-date')
    
    # Appliquer les restrictions de permissions
    if hasattr(request.user, 'is_responsable_classe') and request.user.is_responsable_classe:
        notes = notes.filter(eleve__classe=request.user.classe)
    elif hasattr(request.user, 'is_eleve') and request.user.is_eleve:
        notes = notes.filter(eleve__numero_etudiant=request.user.numero_etudiant)
    
    # Créer le formulaire de filtrage
    form = NoteFilterForm(request.GET or None, user=request.user)
    
    # Debug - Afficher les paramètres GET
    print(f"GET parameters: {request.GET}")
    print(f"Form is bound: {form.is_bound}")
    print(f"Form is valid: {form.is_valid()}")
    if form.is_bound:
        print(f"Form errors: {form.errors}")
    
    # Appliquer les filtres si le formulaire est valide
    if form.is_valid():
        classe = form.cleaned_data.get('classe')
        matiere = form.cleaned_data.get('matiere')
        date = form.cleaned_data.get('date')
        
        print(f"Filters - Classe: {classe}, Matiere: {matiere}, Date: {date}")
        
        if classe:
            notes = notes.filter(eleve__classe=classe)
            print(f"After classe filter: {notes.count()} notes")
        
        if matiere:
            notes = notes.filter(matiere=matiere)
            print(f"After matiere filter: {notes.count()} notes")
        
        if date:
            notes = notes.filter(date=date)
            print(f"After date filter: {notes.count()} notes")
    
    print(f"Final notes count: {notes.count()}")
    
    return render(request, 'responsable_filiere/note_list.html', {
        'form': form,
        'notes': notes
    })

@login_required
@permission_required('responsable_filiere.can_manage_notes')
def note_create(request):
    if request.method == 'POST':
        # Vérifier si NoteForm accepte le paramètre user
        try:
            form = NoteForm(request.POST, user=request.user)
        except TypeError:
            form = NoteForm(request.POST)
            
        if form.is_valid():
            note = form.save(commit=False)
            # Vérification des permissions
            if (hasattr(request.user, 'is_responsable_classe') and 
                request.user.is_responsable_classe and 
                note.eleve.classe != request.user.classe):
                messages.error(request, "Vous ne pouvez ajouter des notes que pour les élèves de votre classe.")
                return render(request, 'responsable_filiere/note_form.html', {'form': form})
            note.save()
            messages.success(request, "Note ajoutée avec succès.")
            return redirect('responsable_filiere:note_list')
    else:
        # Vérifier si NoteForm accepte le paramètre user
        try:
            form = NoteForm(user=request.user)
        except TypeError:
            form = NoteForm()
    
    return render(request, 'responsable_filiere/note_form.html', {'form': form})

@login_required
@permission_required('responsable_filiere.can_manage_notes')
def save_class_notes(request):
    if request.method == 'POST':
        NoteFormSet = formset_factory(NoteForm, extra=0)
        formset = NoteFormSet(request.POST)
        
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data.get('valeur'):
                    note = form.save(commit=False)
                    if (hasattr(request.user, 'is_responsable_filiere') and 
                        request.user.is_responsable_filiere and 
                        note.eleve.classe != request.user.classe):
                        continue  # Ignorer les notes pour les élèves d'autres classes
                    note.save()
            messages.success(request, "Notes sauvegardées avec succès.")
            return redirect('responsable_filiere:note_list')
        else:
            return render(request, 'responsable_filiere/note_class_form.html', {'formset': formset})
    
    return redirect('responsable_filiere:note_class_create')

@login_required
def generer_bulletin(request, eleve_id):
    eleve = get_object_or_404(Eleve, pk=eleve_id)
    if hasattr(request.user, 'is_eleve') and request.user.is_eleve and eleve.numero_etudiant != request.user.numero_etudiant:
        return HttpResponseForbidden("Vous ne pouvez voir que votre propre bulletin.")
    if hasattr(request.user, 'is_responsable_classe') and request.user.is_responsable_classe and eleve.classe != request.user.classe:
        return HttpResponseForbidden("Vous ne pouvez générer des bulletins que pour les élèves de votre classe.")
    
    notes = Note.objects.filter(eleve=eleve).select_related('matiere')
    
    data = []
    for note in notes:
        data.append({
            'Matière': note.matiere.nom,
            'Code': note.matiere.code,
            'Coefficient': note.matiere.coefficient,
            'Note': float(note.valeur),
            'Type': note.type_evaluation,
            'Date': note.date,
            'Commentaire': note.commentaire
        })
    
    if not data:
        return HttpResponse("Aucune note disponible pour cet élève")
    
    df = pd.DataFrame(data)
    moyennes = df.groupby(['Matière', 'Code', 'Coefficient']).agg({'Note': 'mean'}).reset_index()
    
    if not moyennes.empty:
        moyennes['Note_ponderee'] = moyennes['Note'] * moyennes['Coefficient']
        moyenne_generale = moyennes['Note_ponderee'].sum() / moyennes['Coefficient'].sum()
    else:
        moyenne_generale = 0
    
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    header_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',
        'bg_color': '#4472C4',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        'border': 1
    })
    
    title_format = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'align': 'center',
        'valign': 'vcenter'
    })
    
    worksheet = workbook.add_worksheet("Bulletin")
    worksheet.merge_range('A1:G1', f"BULLETIN DE NOTES - {eleve.nom} {eleve.prenom}", title_format)
    
    worksheet.write('A3', "Nom:", cell_format)
    worksheet.write('B3', eleve.nom, cell_format)
    worksheet.write('A4', "Prénom:", cell_format)
    worksheet.write('B4', eleve.prenom, cell_format)
    worksheet.write('A5', "Classe:", cell_format)
    worksheet.write('B5', eleve.classe.niveau, cell_format)
    
    worksheet.write('A7', "Matière", header_format)
    worksheet.write('B7', "Code", header_format)
    worksheet.write('C7', "Coefficient", header_format)
    worksheet.write('D7', "Moyenne", header_format)
    
    row = 7
    for _, matiere_data in moyennes.iterrows():
        row += 1
        worksheet.write(f'A{row}', matiere_data['Matière'], cell_format)
        worksheet.write(f'B{row}', matiere_data['Code'], cell_format)
        worksheet.write(f'C{row}', matiere_data['Coefficient'], cell_format)
        worksheet.write(f'D{row}', round(matiere_data['Note'], 2), cell_format)
    
    row += 2
    worksheet.write(f'A{row}', "MOYENNE GÉNÉRALE:", header_format)
    worksheet.write(f'D{row}', round(moyenne_generale, 2), header_format)
    
    detail_sheet = workbook.add_worksheet("Détail des notes")
    detail_sheet.write('A1', "Matière", header_format)
    detail_sheet.write('B1', "Type", header_format)
    detail_sheet.write('C1', "Note", header_format)
    detail_sheet.write('D1', "Date", header_format)
    detail_sheet.write('E1', "Commentaire", header_format)
    
    row = 1
    for _, note_data in df.iterrows():
        row += 1
        detail_sheet.write(f'A{row}', note_data['Matière'], cell_format)
        detail_sheet.write(f'B{row}', note_data['Type'], cell_format)
        detail_sheet.write(f'C{row}', note_data['Note'], cell_format)
        detail_sheet.write(f'D{row}', note_data['Date'].strftime('%d/%m/%Y'), cell_format)
        detail_sheet.write(f'E{row}', note_data['Commentaire'], cell_format)
    
    workbook.close()
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=bulletin_{eleve.nom}_{eleve.prenom}.xlsx'
    
    return response

@login_required
def infos_pedagogiques(request):
    cahiers = CahierTexte.objects.select_related('classe', 'matiere').order_by('-date')
    absences = Absence.objects.select_related('eleve').order_by('-date')
    projets = Projet.objects.select_related('classe', 'matiere').order_by('date_limite')
    
    if hasattr(request.user, 'is_responsable_classe') and request.user.is_responsable_classe:
        cahiers = cahiers.filter(classe=request.user.classe)
        absences = absences.filter(eleve__classe=request.user.classe)
        projets = projets.filter(classe=request.user.classe)
    elif hasattr(request.user, 'is_eleve') and request.user.is_eleve:
        cahiers = cahiers.filter(classe=request.user.classe)
        absences = absences.filter(eleve__numero_etudiant=request.user.numero_etudiant)
        projets = projets.filter(classe=request.user.classe)
    
    form = EleveSelectForm(request.GET or None)
    if form.is_valid() and hasattr(request.user, 'is_responsable_filiere') and request.user.is_responsable_filiere:
        classe = form.cleaned_data.get('classe')
        if classe:
            cahiers = cahiers.filter(classe=classe) 
            absences = absences.filter(eleve__classe=classe)
            projets = projets.filter(classe=classe)
    
    context = {
        'form': form,
        'cahiers': cahiers,
        'absences': absences,
        'projets': projets
    }
    
    return render(request, 'responsable_filiere/infos_pedagogiques.html', context)