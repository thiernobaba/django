from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden

class ResponsableClasseRequiredMixin(AccessMixin):
    """Mixin to restrict access to users with 'responsable_classe' user_type."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_responsable_classe:
            return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
        return super().dispatch(request, *args, **kwargs)

class ResponsableFiliereRequiredMixin(AccessMixin):
    """Mixin to restrict access to users with 'responsable_filiere' user_type."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_responsable_filiere:
            return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
        return super().dispatch(request, *args, **kwargs)

class EleveRequiredMixin(AccessMixin):
    """Mixin to restrict access to users with 'eleve' user_type."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_eleve:
            return HttpResponseForbidden("Vous n'avez pas la permission d'accéder à cette page.")
        return super().dispatch(request, *args, **kwargs)