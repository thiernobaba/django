from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# Fonction utilitaire pour récupérer l'utilisateur d'un élève
def get_user_for_eleve(eleve):
    """
    Fonction corrigée pour récupérer l'utilisateur associé à un élève
    """
    # Méthode 1: Si l'élève a un champ user direct
    if hasattr(eleve, 'user') and eleve.user:
        return eleve.user
    
    # Méthode 2: Recherche par numéro étudiant
    if hasattr(eleve, 'numero_etudiant'):
        try:
            return User.objects.get(username=eleve.numero_etudiant)
        except User.DoesNotExist:
            pass
    
    # Méthode 3: Autres méthodes de liaison possibles
    try:
        # Si vous avez une relation OneToOneField explicite
        return eleve.user_profile.user
    except (AttributeError, User.DoesNotExist):
        pass
    
    logger.warning(f"Aucun utilisateur trouvé pour l'élève {eleve}")
    return None

# Fonction utilitaire pour créer une notification
def create_notification(user, message, notification_type, related_id=None):
    """
    Fonction utilitaire pour créer une notification de manière sécurisée
    """
    if user:
        try:
            notification = Notification.objects.create(
                user=user,
                message=message,
                notification_type=notification_type,
                related_id=related_id
            )
            logger.info(f"Notification créée pour {user.username}: {message}")
            return notification
        except Exception as e:
            logger.error(f"Erreur lors de la création de notification: {str(e)}")
    return None

class Notification(models.Model):
    """Modèle pour les notifications des élèves"""

    NOTIFICATION_TYPES = [
        ('CAHIER', 'Nouveau cahier de texte'),
        ('ABSENCE', 'Nouvelle absence'),
        ('PROJET', 'Nouveau projet'),
        ('NOTE', 'Nouvelle note'),
        ('GENERAL', 'Notification générale'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Utilisateur"
    )
    message = models.TextField(verbose_name="Message")
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name="Type de notification"
    )
    related_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID de l'objet concerné"
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name="Lu"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de lecture"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.get_notification_type_display()} - {self.user.username}"

    def mark_as_read(self):
        """Marquer la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def get_absolute_url(self):
        """Retourner l'URL de la notification selon son type"""
        try:
            if self.notification_type == 'CAHIER' and self.related_id:
                return reverse('cahier_detail', args=[self.related_id])
            elif self.notification_type == 'ABSENCE' and self.related_id:
                return reverse('absence_detail', args=[self.related_id])
            elif self.notification_type == 'PROJET' and self.related_id:
                return reverse('projet_detail', args=[self.related_id])
            elif self.notification_type == 'NOTE' and self.related_id:
                return reverse('note_detail', args=[self.related_id])
            else:
                return reverse('notifications_list')
        except:
            return reverse('notifications_list')

    @property
    def is_recent(self):
        """Vérifier si la notification est récente (moins de 24h)"""
        return (timezone.now() - self.created_at).days == 0
