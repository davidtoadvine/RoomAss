from django.contrib import admin

# Register your models here.
from .models import Building, Section, Room, Person, CustomEvent

#admin.site.register(Building)
admin.site.register(Section)
#admin.site.register(Room)
#admin.site.register(Person)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1  # Number of empty sections to displa

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    inlines = [SectionInline] 

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('section', 'number', 'owner')
    search_fields = ('section__building__name', 'section__name', 'number', 'owner__name')
    list_filter = ('section__building', 'section')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['owner'].queryset = Person.objects.all()
        return form

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email')
    search_fields = ('name', 'contact_email')

@admin.register(CustomEvent)
class CustomEventAdmin(admin.ModelAdmin):
    pass

