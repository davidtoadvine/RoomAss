from django.contrib import admin

# Register your models here.
from .models import Building, Section, Room, Person, CustomEvent

#admin.site.register(Building)
admin.site.register(Section)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
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
    list_display = ('title', 'start', 'end', 'event_type', 'calendar')
    search_fields = ('title', 'event_type')
    def save_model(self, request, obj, form, change):
        # Debug statement before saving
        print(f"Before saving: {obj.title}, start: {obj.start}, end: {obj.end}")
        
        # Call the superclass method to save the object
        super().save_model(request, obj, form, change)
        
        # Debug statement after saving
        print(f"After saving: {obj.title}, start: {obj.start}, end: {obj.end}")


# Define an inline admin descriptor for Person model
# which acts a bit like a singleton
class PersonInline(admin.StackedInline):
    model = Person
    can_delete = False
    verbose_name_plural = 'person'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (PersonInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)