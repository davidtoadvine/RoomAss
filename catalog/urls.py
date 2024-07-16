from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from catalog.views.main_views import (
    home, all_guests, 
    rooms_master, my_guests, my_room,
    buildings_offline_toggle, toggle_offline_section,
    remove_owner, assign_owner
)
from catalog.views.occupancy_views import (
    delete_booking, extend_booking, shorten_booking,
    extend_conflict, create_booking
)
from catalog.views.availability_views import (
    create_availability, edit_availability, delete_availability, edit_guest_preferences
)
from catalog.views.error_views import no_room, no_person


urlpatterns = [
    path('', home, name='home'),  # Home page
    
    path('my_room/', my_room, name='my_room'),
    path('create_booking/', create_booking, name='create_booking'),

    path('create_availability/room/<int:room_id>/', create_availability, name='create_availability_with_room_redirect'),
        path('create_availability/section/<int:section_id>/', create_availability, name='create_availability_with_section_redirect'),

    path('edit_availability/room/<int:room_id>/', edit_availability, name='edit_availability_with_room_redirect'),
    path('edit_availability/section/<int:section_id>/', edit_availability, name='edit_availability_with_section_redirect'),


    path('delete_availability/room/<int:room_id>/', delete_availability, name='delete_availability_with_room_redirect'),
        path('delete_availability/section/<int:section_id>/', delete_availability, name='delete_availability_with_section_redirect'),


    path('edit_guest_preferences/<int:room_id>/<int:person_id>/', edit_guest_preferences, name='edit_guest_preferences'),
    path('edit_guest_preferences/<int:room_id>/<int:person_id>/<int:section_id>/', edit_guest_preferences, name='edit_guest_preferences_with_section'),


    path('all_guests/', all_guests, name='all_guests'),
    path('my_guests/', my_guests, name='my_guests'),

    path('delete_booking/<int:event_id>/', delete_booking, name='delete_booking'),
    path('delete_booking/<int:event_id>/<int:section_id>/', delete_booking, name='delete_booking_with_section'),

    path('extend_booking/<int:event_id>/', extend_booking, name='extend_booking'),
    path('extend_booking/<int:event_id>/<int:section_id>/', extend_booking, name='extend_booking_with_section'),


    path('shorten_booking/<int:event_id>/', shorten_booking, name='shorten_booking'),
    path('shorten_booking/<int:event_id>/<int:section_id>/', shorten_booking, name='shorten_booking_with_section'),

    path('extend_conflict/', extend_conflict, name='extend_conflict'),
    path('no_room/', no_room, name='no_room'),

    path('rooms_master/', rooms_master, name='rooms_master'),
    path('rooms_master/room/<int:room_id>/', rooms_master, name='rooms_master_with_room'),
        path('rooms_master/section/<int:section_id>/', rooms_master, name='rooms_master_with_section'),


    path('buildings_offline_toggle/', buildings_offline_toggle, name='buildings_offline_toggle'),

        path('toggle_offline_section/', toggle_offline_section, name='toggle_offline_section'),
        # path('rooms_master/room/<int:room_id>/', rooms_master, name='rooms_master_with_room'),  # New URL pattern for rooms without owners

    path('no_person/', no_person, name='no_person'),

        path('remove_owner/', remove_owner, name='remove_owner'),
        path('remove_owner/<int:section_id>/', remove_owner, name='remove_owner_with_section'),

        path('assign_owner/<int:room_id>/', assign_owner, name='assign_owner'),
        path('assign_owner/<int:room_id>/<int:section_id>/', assign_owner, name='assign_owner_with_section'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)