from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('responsable_filiere', 'Responsable de Filière'),
        ('responsable_classe', 'Responsable de Classe'),
        ('eleve', 'Élève'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    classe = models.ForeignKey('responsable_filiere.Classe', on_delete=models.SET_NULL, blank=True, null=True)
    numero_etudiant = models.CharField(max_length=20, blank=True, null=True, unique=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    date_naissance = models.DateField(blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"
    
    @property
    def is_responsable_filiere(self):
        return self.user_type == 'responsable_filiere'
    
    @property
    def is_responsable_classe(self):
        return self.user_type == 'responsable_classe'
    
    @property
    def is_eleve(self):
        return self.user_type == 'eleve'

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'