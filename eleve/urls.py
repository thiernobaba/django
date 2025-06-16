from django.urls import path
from . import views

app_name = 'eleve'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profil/', views.EleveDetailView.as_view(), name='eleve_detail'),
    path('notes/', views.NoteListView.as_view(), name='note_list'),
    path('absences/', views.AbsenceListView.as_view(), name='absence_list'),
    path('projets/', views.ProjetListView.as_view(), name='projet_list'),
    path('cahier-texte/', views.CahierTexteListView.as_view(), name='cahier_texte_list'),
    path('cahier-texte/<int:pk>/', views.CahierTexteDetailView.as_view(), name='cahier_texte_detail'),

]