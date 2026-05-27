from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

app_name = 'community_forum'

urlpatterns = [
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.index, name='index'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('category/<slug:slug>/new/', views.create_topic, name='create_topic'),
    path('topic/<int:pk>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:pk>/reply/', views.create_post, name='create_post'),
    path('post/<int:pk>/reply/', views.reply_to_post, name='reply_to_post'),
    # Workspace Admin moderation (accessible from community subdomain)
    path('moderate/', views.moderation_panel, name='moderation_panel'),
] + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static') \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

