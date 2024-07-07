
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

@login_required
def no_person(request):
    return render(request, 'catalog/no_person.html')


@login_required
def no_room(request):
    return render(request, 'catalog/no_room.html')
