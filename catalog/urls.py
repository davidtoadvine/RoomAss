from django.urls import path
from . import views
from .views import home, create_booking, create_availability, edit_guest_preferences, delete_availability
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', views.home, name='home'),  # Home page
    # path('buildings/', views.building_list, name='building_list'),
    # path('buildings/<int:building_id>/', views.building_detail, name='building_detail'),
    # path('sections/<int:section_id>/', views.section_detail, name='section_detail'),
    path('my_room/', views.my_room, name='my_room'),
    path('persons/<int:person_id>/', views.person_detail, name='person_detail'),
    path('create_booking/', create_booking, name='create_booking'),
    path('create_availability', create_availability, name = 'create_availability'),
    path('edit_availability', views.edit_availability, name = 'edit_availability'),
    path('edit_guest_preferences/<int:person_id>/', edit_guest_preferences, name='edit_guest_preferences'),
        path('delete_availability/', delete_availability, name='delete_availability'),]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)