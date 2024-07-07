from django.urls import path
from catalog.views.main_views import (
    home, all_guests, 
    rooms_master, my_guests, my_room
)
from catalog.views.occupancy_views import(
    delete_event, extend_booking, shorten_booking, extend_conflict,create_booking,
)
from catalog.views.availability_views import( create_availability, edit_availability, delete_availability,edit_guest_preferences)
from catalog.views.error_views import (no_room, no_person)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),  # Home page
    
    path('my_room/', my_room, name='my_room'),
    path('create_booking/', create_booking, name='create_booking'),

    path('create_availability/<int:room_id>/', create_availability, name='create_availability'),
    path('edit_availability/<int:room_id>/', edit_availability, name='edit_availability'),
    path('delete_availability/<int:room_id>/', delete_availability, name='delete_availability'),

    path('edit_guest_preferences/<int:person_id>/', edit_guest_preferences, name='edit_guest_preferences'),

    path('all_guests/', all_guests, name='all_guests'),
    path('my_guests/', my_guests, name='my_guests'),

    path('delete_event/<int:event_id>/', delete_event, name='delete_event'),
    path('extend_booking/<int:event_id>/', extend_booking, name='extend_booking'),
    path('shorten_booking/<int:event_id>/', shorten_booking, name='shorten_booking'),
    path('extend_conflict/', extend_conflict, name='extend_conflict'),
    path('no_room/', no_room, name='no_room'),

    path('rooms_master/', rooms_master, name='rooms_master'),
    path('rooms_master/<int:room_id>/', rooms_master, name='rooms_master_with_room'),

        # path('rooms_master/room/<int:room_id>/', rooms_master, name='rooms_master_with_room'),  # New URL pattern for rooms without owners

    path('no_person/', no_person, name='no_person'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)