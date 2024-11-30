from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models import Person, Building, Section, CustomEvent, Room
from schedule.models import Calendar, Event
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils.timezone import now
import logging

class PersonModelTest(TestCase):


    def test_name_max_length(self):
        person = Person(name= 'x' * 31) # exceed max length
        with self.assertRaises(ValidationError):
            person.full_clean() # validate field
    
    def test_user_null_allowed(self):
        person = Person.objects.create(name="Testperson", user=None)
        self.assertIsNone(person.user)

    def test_user_del_cascades(self):
        user = User.objects.create(username='testuser')
        person = Person.objects.create(name="Testperson", user=user)
        self.assertEqual(person.user,user)
        self.assertTrue(Person.objects.filter(id=person.id).exists())
        user.delete()
        self.assertFalse(Person.objects.filter(id=person.id).exists())
    
    def test_parent_relationship(self):
        parent = Person.objects.create(name="Parent")
        child = Person.objects.create(name="Child", parent=parent)
        self.assertEqual(parent, child.parent)
        self.assertIn(child, parent.children.all())
        parent.delete()
        child.refresh_from_db()
        self.assertIsNone(child.parent)

    def test_no_incestuous_timeloop_family_structure(self):
        person = Person.objects.create(name="Testperson")
        person.parent = person
        with self.assertRaises(ValueError):
            person.save()

    def test_preference_default(self):
        person = Person.objects.create(name="Testperson")
        self.assertEqual(person.preference, Person.Preference.ANYONE)

    def test_preference_choices(self):
        person = Person.objects.create(name="Testperson", preference=Person.Preference.MEMBERS)
        self.assertEqual(person.preference, Person.Preference.MEMBERS)
        person.preference = Person.Preference.KNOWN
        self.assertEqual(person.preference, Person.Preference.KNOWN)

    def test_str_method(self):
        person = Person.objects.create(name="Testperson")
        self.assertEqual(str(person), "Testperson")

class BuildingModelTest(TestCase):

    def test_name_max_length(self):
        building = Building(name= 'x' * 31) # exceed max length
        with self.assertRaises(ValidationError):
            building.full_clean() # validate field

    def test_area_max_length(self):
        building = Building(area= 'x' * 31) # exceed max length
        with self.assertRaises(ValidationError):
            building.full_clean() # validate field

    def test_is_offline(self):
        building = Building.objects.create(name="Testbuilding")
        self.assertEqual(building.is_offline, False)
        building.is_offline = True
        self.assertEqual(building.is_offline,True)

    def test_str_method(self):
        building = Building.objects.create(name="Testbuilding")
        self.assertEqual(str(building), "Testbuilding")

class SectionModelTest(TestCase):
    
    def setUp(self):
        self.building = Building.objects.create(name="Testbuilding")
        self.section = Section.objects.create(name="Testsection" ,building = self.building)

    def test_name_max_length(self):
        section = Section(name="x" * 31)
        with self.assertRaises(ValidationError):
            section.full_clean()

    def test_is_offline(self):
        self.assertEqual(self.section.is_offline, False)
        self.section.is_offline = True
        self.assertEqual(self.section.is_offline,True)

    def test_str_method(self):
        self.assertEqual(str(self.section), "Testbuilding / Testsection")
    
    def test_no_building(self):
        section = Section(name = "Testsection")

        with self.assertRaises(ValidationError):
            section.full_clean()

    def test_del_building(self):
        self.building.delete()
        id = self.section.id
        with self.assertRaises(Section.DoesNotExist):
            Section.objects.get(id=id)
    

    def test_del_avail_event(self):
        room = Room.objects.create(section=self.section, number=1)
        calendar = room.calendar

        # clearing it out because a long term availability event is auto created on room instantiation
        CustomEvent.objects.filter(calendar=calendar).delete()

        # create our own event independent of scary invisble stranger code
        start_time = now()
        end_time = start_time + timedelta(days=1)

        custom_event = CustomEvent.objects.create(
            start=start_time,
            end=end_time,
            event_type='availability',
            guest_type=CustomEvent.GuestType.MEMBER,
            guest_name="John Doe",
            calendar=calendar
        )
        id = custom_event.id

        # Verify the event exists before deletion
        self.assertEqual(CustomEvent.objects.filter(calendar=calendar).count(), 1)

        # Call the delete method on the section
        self.section.delete_availability_events()

        # Verify that the event has been deleted
        with self.assertRaises(CustomEvent.DoesNotExist):
            CustomEvent.objects.get(id=id)



class RoomModelTest(TestCase):
    def test_test(self):
        building = Building.objects.create(name="Testbuilding") 
        section = Section.objects.create(name="Testsection", building = building)
        room = Room.objects.create(section=section, number= 8888888)
        self.assertTrue(True)