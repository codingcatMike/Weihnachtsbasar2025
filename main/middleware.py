from django.shortcuts import redirect
from .models import SiteStatus

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        status = SiteStatus.objects.first()
        maintenance_on = status.maintenance_mode if status else False
        bypass = getattr(request.user, 'is_superuser', False) or request.session.get('maintenance_bypass', False)

        # Print to console immediately
        print(f"[MaintenanceMiddleware] maintenance_bypass session value: {request.session.get('maintenance_bypass')}")
        print(f"[MaintenanceMiddleware] User: {request.user}, is_superuser: {getattr(request.user, 'is_superuser', False)}")
        print(f"[MaintenanceMiddleware] Maintenance mode: {maintenance_on}, Bypass: {bypass}")

        if maintenance_on and not bypass:
            if not request.path.startswith('/admin/') and request.path != '/501/' and not request.path.startswith('/api/'):
                return redirect('/501/')

        return self.get_response(request)
