from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse  # Import manquant
from django.contrib.auth import get_user_model
import hashlib

class Classe(models.Model):
    NIVEAU_CHOICES = [
        ('AS1', 'Analyse Statistique 1'),
        ('AS2', 'Analyse Statistique 2'),
        ('AS3', 'Analyse Statistique 3'),
    ]
    
    niveau = models.CharField(max_length=3, choices=NIVEAU_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        permissions = [
            ("can_view_own_classe", "Peut voir les données de sa classe"),
        ]
    
    def __str__(self):
        return self.get_niveau_display()
    
    def get_absolute_url(self):  # Méthode ajoutée
        return reverse('responsable_filiere:classe_detail', kwargs={'pk': self.pk})

class Eleve(models.Model):
    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    numero_etudiant = models.CharField(max_length=11, unique=True, blank=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=15, blank=True)
    adresse = models.TextField(blank=True)
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='eleves')
    photo = models.ImageField(upload_to='photos_eleves/', blank=True, null=True)
    date_inscription = models.DateField(auto_now_add=True)

    user = models.OneToOneField(
        get_user_model(), 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='eleve_profile'
    )
    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ['nom', 'prenom']
        permissions = [
            ("can_view_all_eleves", "Peut voir tous les élèves"),
            ("can_edit_all_eleves", "Peut modifier tous les élèves"),
        ]
    
    def save(self, *args, **kwargs):
        if not self.numero_etudiant:
            # Génération du numéro étudiant
            base_str = f"{self.nom[:3].upper()}{self.prenom[:2].upper()}{self.date_naissance.strftime('%d%m%y')}"
            
            # Création d'un hash pour garantir l'unicité
            hash_str = hashlib.md5(base_str.encode()).hexdigest()[:0].upper()
            self.numero_etudiant = f"{base_str}{hash_str}"
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.classe})"
    
    def get_absolute_url(self):
        return reverse('responsable_filiere:eleve_detail', kwargs={'pk': self.pk})
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
class Matiere(models.Model):
    nom = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    coefficient = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    classes = models.ManyToManyField(Classe, related_name='matieres')
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        permissions = [
            ("can_manage_matieres", "Peut gérer les matières"),
        ]
        
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    def get_absolute_url(self):  # Méthode ajoutée
        return reverse('responsable_filiere:matiere_detail', kwargs={'pk': self.pk})

class Note(models.Model):
    TYPE_EVALUATION_CHOICES = [  # Renommé pour être plus clair
        ('DEVOIR', 'Devoir'),
        ('EXAMEN', 'Examen'),
        ('TP', 'Travail Pratique'),
        ('PROJET', 'Projet'),
    ]
    
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='notes')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='notes')
    valeur = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(20)]
    )
    date = models.DateField()
    type_evaluation = models.CharField(
        max_length=20,
        choices=TYPE_EVALUATION_CHOICES
    )
    commentaire = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ['eleve', 'matiere', 'date', 'type_evaluation']
        permissions = [
            ("can_manage_notes", "Peut gérer les notes"),
        ]
        
    def __str__(self):
        return f"{self.eleve} - {self.matiere} - {self.valeur}/20 ({self.type_evaluation})"

class CahierTexte(models.Model):
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='cahiers_texte')
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='cahiers_texte')
    date = models.DateField()
    contenu = models.TextField()
    
    class Meta:
        verbose_name = "Cahier de texte"
        verbose_name_plural = "Cahiers de texte"
        ordering = ['-date']

class Absence(models.Model):
    eleve = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='absences')
    date = models.DateField()
    justifiee = models.BooleanField(default=False)
    motif = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Absence"
        verbose_name_plural = "Absences"
        ordering = ['-date']

class Projet(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField()
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='projets')
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name='projets')
    date_attribution = models.DateField()
    date_limite = models.DateField()
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['date_limite']
        
    def __str__(self):
        return f"{self.titre} ({self.classe}) - Échéance: {self.date_limite}"