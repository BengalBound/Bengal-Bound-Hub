from django.urls import path, include
from django.conf import settings

urlpatterns = [
    path('', include('workspace_admin.urls', namespace='workspace_admin')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', include('public_site.urls', namespace='public_site')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
