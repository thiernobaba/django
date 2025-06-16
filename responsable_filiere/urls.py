# responsable_filiere/urls.py

from django.urls import path
from . import views

app_name = 'responsable_filiere'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Gestion des élèves
    path('eleves/', views.EleveListView.as_view(), name='eleve_list'),
    path('eleves/<int:pk>/', views.EleveDetailView.as_view(), name='eleve_detail'),
    path('eleves/creer/', views.EleveCreateView.as_view(), name='eleve_create'),
    path('eleves/<int:pk>/modifier/', views.EleveUpdateView.as_view(), name='eleve_update'),
    path('eleves/<int:pk>/supprimer/', views.EleveDeleteView.as_view(), name='eleve_delete'),
    path('eleves/<int:eleve_id>/bulletin/', views.generer_bulletin, name='generer_bulletin'),
    
    # Gestion des matières
    path('matieres/', views.MatiereListView.as_view(), name='matiere_list'),
    path('matieres/<int:pk>/', views.MatiereDetailView.as_view(), name='matiere_detail'),
    path('matieres/creer/', views.MatiereCreateView.as_view(), name='matiere_create'),
    path('matieres/<int:pk>/modifier/', views.MatiereUpdateView.as_view(), name='matiere_update'),
    path('matieres/<int:pk>/supprimer/', views.MatiereDeleteView.as_view(), name='matiere_delete'),
    
    # Gestion des notes
    path('notes/', views.note_list, name='note_list'),
    path('notes/creer/', views.note_create, name='note_create'),    
    # Informations pédagogiques
    path('infos-pedagogiques/', views.infos_pedagogiques, name='infos_pedagogiques'),
]