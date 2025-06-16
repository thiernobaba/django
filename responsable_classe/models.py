from django.db import models
from django.utils import timezone
from responsable_filiere.models import Classe, Eleve, Matiere

class CahierTexte(models.Model):
    """Modèle pour le cahier de texte - version responsable classe"""
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='cahiers_classe')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cahiers_classe')
    date = models.DateField(default=timezone.now)
    titre = models.CharField(max_length=200, help_text="Titre de la séance")
    contenu = models.TextField(help_text="Contenu de la séance")
    travail_a_faire = models.TextField(blank=True, help_text="Travail à faire pour la prochaine séance")
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cahier de texte"
        verbose_name_plural = "Cahiers de texte"
        ordering = ['-date']
        unique_together = ['classe', 'matiere', 'date', 'titre']
        permissions = [
            ("can_manage_cahier_texte", "Peut gérer le cahier de texte"),
        ]
    
    def __str__(self):
        return f"{self.classe} - {self.matiere} - {self.date} - {self.titre}"

class Absence(models.Model):
    """Modèle pour gérer les absences - version responsable classe"""
    TYPE_ABSENCE_CHOICES = [
        ('COURS', 'Cours'),
        ('TP', 'Travaux Pratiques'),
        ('EXAMEN', 'Examen'),
        ('AUTRE', 'Autre'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='absences_classe')
    date = models.DateField(default=timezone.now)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='absences_classe')
    type_absence = models.CharField(max_length=10, choices=TYPE_ABSENCE_CHOICES, default='COURS')
    heure_debut = models.TimeField(help_text="Heure de début de l'absence")
    heure_fin = models.TimeField(help_text="Heure de fin de l'absence")
    justifiee = models.BooleanField(default=False)
    motif = models.TextField(blank=True, help_text="Motif de l'absence")
    date_justification = models.DateField(null=True, blank=True)
    document_justificatif = models.FileField(
        upload_to='justificatifs/', 
        blank=True, 
        null=True,
        help_text="Document justificatif (certificat médical, etc.)"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date', '-heure_debut']
        permissions = [
            ("can_manage_absences", "Peut gérer les absences"),
            ("can_view_own_absences", "Peut voir ses propres absences"),
        ]
    
    def __str__(self):
        return f"{self.eleve} - {self.date} ({self.heure_debut}-{self.heure_fin})"
    
    @property
    def duree_minutes(self):
        """Calcule la durée de l'absence en minutes"""
        from datetime import datetime, timedelta
        debut = datetime.combine(self.date, self.heure_debut)
        fin = datetime.combine(self.date, self.heure_fin)
        duree = fin - debut
        return int(duree.total_seconds() / 60)

class Projet(models.Model):
    """Modèle pour les projets et devoirs - version responsable classe"""
    STATUT_CHOICES = [
        ('ATTRIBUE', 'Attribué'),
        ('EN_COURS', 'En cours'),
        ('RENDU', 'Rendu'),
        ('CORRIGE', 'Corrigé'),
        ('ARCHIVE', 'Archivé'),
    ]
    
    TYPE_PROJET_CHOICES = [
        ('DEVOIR', 'Devoir'),
        ('PROJET', 'Projet'),
        ('EXPOSE', 'Exposé'),
        ('RAPPORT', 'Rapport'),
        ('TP', 'Travail Pratique'),
    ]
    
    titre = models.CharField(max_length=200)
    description = models.TextField()
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='projets_classe')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='projets_classe')
    type_projet = models.CharField(max_length=10, choices=TYPE_PROJET_CHOICES, default='DEVOIR')
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='ATTRIBUE')
    date_attribution = models.DateField(default=timezone.now)
    date_limite = models.DateField()
    coefficient = models.PositiveIntegerField(default=1, help_text="Coefficient pour la notation")
    consignes = models.TextField(blank=True, help_text="Consignes détaillées")
    fichier_sujet = models.FileField(upload_to='sujets/', blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['date_limite']
        permissions = [
            ("can_manage_projets", "Peut gérer les projets"),
        ]
    
    def __str__(self):
        return f"{self.titre} ({self.classe}) - {self.date_limite}"
    
    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants avant la date limite"""
        from datetime import date
        delta = self.date_limite - date.today()
        return delta.days
    
    @property
    def est_en_retard(self):
        """Vérifie si le projet est en retard"""
        from datetime import date
        return date.today() > self.date_limite and self.statut not in ['RENDU', 'CORRIGE', 'ARCHIVE']

class RenduProjet(models.Model):
    """Modèle pour les rendus de projets par les élèves"""
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name='rendus')
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='rendus_projets')
    date_rendu = models.DateTimeField(default=timezone.now)
    fichier_rendu = models.FileField(upload_to='rendus/', blank=True, null=True)
    commentaire_eleve = models.TextField(blank=True, help_text="Commentaire de l'élève")
    note = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Note sur 20"
    )
    commentaire_professeur = models.TextField(blank=True, help_text="Commentaire du professeur")
    date_correction = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Rendu de projet"
        verbose_name_plural = "Rendus de projets"
        unique_together = ['projet', 'eleve']
        ordering = ['-date_rendu']
        permissions = [
            ("can_view_own_rendus", "Peut voir ses propres rendus"),
        ]
    
    def __str__(self):
        return f"{self.eleve} - {self.projet.titre}"
    
    @property
    def est_en_retard(self):
        """Vérifie si le rendu est en retard"""
        return self.date_rendu.date() > self.projet.date_limite

class Retard(models.Model):
    """Modèle pour gérer les retards"""
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='retards')
    date = models.DateField(default=timezone.now)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='retards')
    heure_arrivee = models.TimeField(help_text="Heure d'arrivée de l'élève")
    heure_prevue = models.TimeField(help_text="Heure prévue du cours")
    motif = models.TextField(blank=True, help_text="Motif du retard")
    justifie = models.BooleanField(default=False)
    sanction = models.TextField(blank=True, help_text="Sanction éventuelle")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Retard"
        verbose_name_plural = "Retards"
        ordering = ['-date', '-heure_arrivee']
        permissions = [
            ("can_manage_retards", "Peut gérer les retards"),
        ]
    
    def __str__(self):
        return f"{self.eleve} - {self.date} - Retard de {self.duree_retard} min"
    
    @property
    def duree_retard(self):
        """Calcule la durée du retard en minutes"""
        from datetime import datetime, timedelta
        prevue = datetime.combine(self.date, self.heure_prevue)
        arrivee = datetime.combine(self.date, self.heure_arrivee)
        if arrivee > prevue:
            duree = arrivee - prevue
            return int(duree.total_seconds() / 60)
        return 0

class Observation(models.Model):
    """Modèle pour les observations disciplinaires ou pédagogiques"""
    TYPE_OBSERVATION_CHOICES = [
        ('POSITIVE', 'Observation positive'),
        ('NEGATIVE', 'Observation négative'),
        ('NEUTRE', 'Observation neutre'),
        ('DISCIPLINAIRE', 'Observation disciplinaire'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='observations')
    date = models.DateField(default=timezone.now)
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='observations', blank=True, null=True)
    type_observation = models.CharField(max_length=15, choices=TYPE_OBSERVATION_CHOICES)
    titre = models.CharField(max_length=200)
    contenu = models.TextField()
    action_menee = models.TextField(blank=True, help_text="Action menée suite à cette observation")
    suivi_necessaire = models.BooleanField(default=False, help_text="Un suivi est-il nécessaire ?")
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Observation"
        verbose_name_plural = "Observations"
        ordering = ['-date']
        permissions = [
            ("can_manage_observations", "Peut gérer les observations"),
            ("can_view_own_observations", "Peut voir ses propres observations"),
        ]
    
    def __str__(self):
        return f"{self.eleve} - {self.date} - {self.titre}"
    


