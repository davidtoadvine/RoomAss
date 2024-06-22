from django.urls import path
from . import views
from .views import home, create_booking, create_availability
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),  # Home page
    path('buildings/', views.building_list, name='building_list'),
    path('buildings/<int:building_id>/', views.building_detail, name='building_detail'),
    path('sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('my_room/', views.my_room, name='my_room'),
    path('persons/<int:person_id>/', views.person_detail, name='person_detail'),
    path('create_booking/', create_booking, name='create_booking'),
    path('create_availability', create_availability, name = 'create_availability'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)