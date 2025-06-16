# responsable_classe/urls.py
from django.urls import path
from . import views

app_name = 'responsable_classe'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Cahier de texte - URLs
    path('cahier-texte/', views.CahierTexteListView.as_view(), name='cahier_texte_list'),
    path('cahier-texte/creer/', views.CahierTexteCreateView.as_view(), name='cahier_texte_create'),
    path('cahier-texte/<int:pk>/', views.CahierTexteDetailView.as_view(), name='cahier_texte_detail'),
    path('cahier-texte/<int:pk>/modifier/', views.CahierTexteUpdateView.as_view(), name='cahier_texte_update'),
    path('cahier-texte/<int:pk>/supprimer/', views.CahierTexteDeleteView.as_view(), name='cahier_texte_delete'),
    
    # Absences - URLs
    path('absences/', views.absence_list, name='absence_list'),
    path('absences/creer/', views.absence_create, name='absence_create'),
    path('absences/multiple/', views.absence_multiple_create, name='absence_multiple_create'),
    path('absences/<int:pk>/modifier/', views.AbsenceUpdateView.as_view(), name='absence_update'),
    path('absences/<int:pk>/supprimer/', views.AbsenceDeleteView.as_view(), name='absence_delete'),
    path('absences/rapport/', views.rapport_absences, name='rapport_absences'),
    
    # Projets - URLs
    path('projets/', views.ProjetListView.as_view(), name='projet_list'),
    path('projets/<int:pk>/', views.ProjetDetailView.as_view(), name='projet_detail'),
    path('projets/creer/', views.ProjetCreateView.as_view(), name='projet_create'),
    path('projets/<int:pk>/modifier/', views.ProjetUpdateView.as_view(), name='projet_update'),
    path('projets/<int:pk>/supprimer/', views.ProjetDeleteView.as_view(), name='projet_delete'),
    path('projets/<int:projet_id>/corriger/', views.corriger_rendus, name='corriger_rendus'),
    
    # Retards - URLs
    path('retards/', views.retard_list, name='retard_list'),
    path('retards/creer/', views.retard_create, name='retard_create'),
    path('retards/<int:pk>/modifier/', views.RetardUpdateView.as_view(), name='retard_update'),
    path('retards/<int:pk>/supprimer/', views.RetardDeleteView.as_view(), name='retard_delete'),
    
    # Observations - URLs
    path('observations/', views.ObservationListView.as_view(), name='observation_list'),
    path('observations/<int:pk>/', views.ObservationDetailView.as_view(), name='observation_detail'),
    path('observations/creer/', views.ObservationCreateView.as_view(), name='observation_create'),
    path('observations/<int:pk>/modifier/', views.ObservationUpdateView.as_view(), name='observation_update'),
    path('observations/<int:pk>/supprimer/', views.ObservationDeleteView.as_view(), name='observation_delete'),
    
    # Rapports et statistiques - URLs
    path('statistiques/', views.statistiques_classe, name='statistiques'),
    path('ajax/eleves-classe/', views.ajax_eleves_classe, name='ajax_eleves_classe'),
]