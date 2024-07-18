#
# Views for assigning and removing room owners
#

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden

from catalog.models import CustomEvent, Room, Person, Building, Section

@login_required
@user_passes_test(lambda u: u.is_superuser)

def remove_owner(request,section_id = None):
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        room = get_object_or_404(Room, id=room_id)

        if request.user.is_superuser or request.user.has_perm('app.change_room'):
            room.owner = None
            room.save()
            if section_id:
              return redirect('rooms_master_with_section', section_id = section_id)
            else:
              return redirect('rooms_master_with_room', room_id = room_id)
        else:
            return HttpResponseForbidden("You do not have permission to remove the owner.")
    return redirect('rooms_master')

@login_required
@user_passes_test(lambda u: u.is_superuser)

def assign_owner(request, room_id, section_id = None):
    if request.method == 'POST':
        member_id = request.POST.get('member_id')

        room = get_object_or_404(Room, id=room_id)
        member = get_object_or_404(Person, id=member_id)

        room.owner = member
        room.save()

        if section_id:
              return redirect('rooms_master_with_section', section_id = section_id)
        else:
              return redirect('rooms_master_with_room', room_id = room_id)
    return redirect('rooms_master')