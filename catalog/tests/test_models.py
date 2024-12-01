from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models import Person, Building, Section, CustomEvent, Room
from schedule.models import Calendar, Event
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from django.utils.timezone import now, is_aware,get_current_timezone
from unittest.mock import patch
from django.utils import timezone

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

    def test_delete_building(self):
        self.building.delete()
        id = self.section.id
        with self.assertRaises(Section.DoesNotExist):
            Section.objects.get(id=id)
    

    def test_delete_avail_event(self):
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

    def setUp(self):
        self.building = Building.objects.create(name="Testbuilding")
        self.section = Section.objects.create(name="Testsection" ,building = self.building)
        self.room = Room.objects.create(number=1, section=self.section)
        self.assertIsInstance(self.room, Room)

    def test_room_creates_calendar(self):
        self.assertIsNotNone(self.room.calendar)

    def test_room_deletes_calendar(self):
        calendar = self.room.calendar
        self.room.delete()
        # Try to retrieve the calendar object and assert that it's deleted
        with self.assertRaises(Calendar.DoesNotExist):
           Calendar.objects.get(id=calendar.id)  # The calendar should be deleted

        # Refresh the in-memory room instance
        with self.assertRaises(Room.DoesNotExist):
            self.room.refresh_from_db()
    
    def test_room_owner_and_calendar_delete(self):
        # don't want deletion of owner or calendar to delete the room
        self.owner = Person.objects.create(name="Testperson")
        self.room.owner = self.owner
        self.room.owner.delete()
        self.room.calendar.delete()
        self.room.refresh_from_db()
        self.assertIsNotNone(self.room)


    def test_creation_and_default_values(self):
        # starts off line
        self.assertFalse(self.room.is_offline)
        # no room number fails
        self.room = Room(section = self.section)
        with self.assertRaises(ValidationError):
            self.room.full_clean()
        # no section fails
        self.room = Room(number=1)
        with self.assertRaises(ValidationError):
            self.room.full_clean()


    def test_delete_section_cascades(self):
        id = self.room.id
        self.section.delete()   
        with self.assertRaises(Room.DoesNotExist):
            Room.objects.get(id=id)


    def test_delete_owner(self):
        self.owner = Person.objects.create(name="Testperson")
        self.room.owner = self.owner
        self.assertTrue(self.room.owner)
        self.room.owner.delete()
        self.room.refresh_from_db()
        self.assertIsNone(self.room.owner)
    
    def test_str_method(self):
        self.assertEqual(str(self.room), "Testbuilding / Testsection / 1")


    ###
    ### tests for is_available function
    ###
    def test_is_avail_no_calendar(self):

        self.room.calendar.delete()
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_available(now(),now()))
    
    def test_is_avail_bad_date(self):

         with self.assertRaises(ValueError):
             self.room.is_available(now(),"string")
         with self.assertRaises(ValueError):
             self.room.is_available("string", now())
        

    def test_is_avail_naive_date(self):

         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'availability', start = start_date, end = end_date)

         naive_start = datetime(3000, 1, 5, 12, 0)
         naive_end = datetime(3000, 1, 6, 12, 0)
        
        # this creates a mock version of make_aware that keeps track of whether or not it has been called
         with patch('django.utils.timezone.make_aware',side_effect=timezone.make_aware) as mocked_make_aware:
        
            # Call the function that should invoke make_aware
            result = self.room.is_available(naive_start,naive_end)

            # Check if make_aware was called with the correct datetime and timezone
            mocked_make_aware.assert_any_call(naive_start, get_current_timezone())
            mocked_make_aware.assert_any_call(naive_end, get_current_timezone())
            
            self.assertEqual(mocked_make_aware.call_count, 2)
            self.assertTrue(result)

    def test_is_avail_no_availability(self):
 
         naive_start = datetime(3000, 1, 5, 12, 0)
         naive_end = datetime(3000, 1, 6, 12, 0)
         self.assertFalse(self.room.is_available(naive_start, naive_end))
   
    def test_is_avail_basic_dates(self):

         start_date = datetime(3000, 1, 2, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'availability', start = start_date, end = end_date)
         
         # requested start is too early
         naive_start = datetime(3000, 1, 1, 12, 0)
         naive_end = datetime(3000, 1, 9, 12, 0)
         self.assertFalse(self.room.is_available(naive_start, naive_end))

         # requested end is too late
         naive_start = datetime(3000, 1, 3, 12, 0)
         naive_end = datetime(3000, 1, 11, 12, 0)
         self.assertFalse(self.room.is_available(naive_start, naive_end))

        # requested dates within range
         naive_start = datetime(3000, 1, 3, 12, 0)
         naive_end = datetime(3000, 1, 5, 12, 0)
         self.assertTrue(self.room.is_available(naive_start, naive_end))
    
    def test_is_avail_exact_dates(self):

         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'availability', start = start_date, end = end_date)
         
         naive_start = datetime(3000, 1, 1, 12, 0)
         naive_end = datetime(3000, 1, 10, 12, 0)
         self.assertTrue(self.room.is_available(naive_start, naive_end))
    

    def test_is_avail_avails_and_occs(self):

         # create availability event
         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'availability', start = start_date, end = end_date)
         
         # create occupation in beginning of availability
         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 3, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'occupancy', start = start_date, end = end_date)
         
         # should be unavailable for full range
         naive_start = datetime(3000, 1, 1, 12, 0)
         naive_end = datetime(3000, 1, 10, 12, 0)
         self.assertFalse(self.room.is_available(naive_start, naive_end))

         # redefine occupation at end of availability
         start_date = datetime(3000, 1, 8, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'occupation', start = start_date, end = end_date)
         # should be unavailable for full range
         self.assertFalse(self.room.is_available(naive_start, naive_end))

         # request for this shorter span should work
         naive_start = datetime(3000, 1, 4, 12, 0)
         naive_end = datetime(3000, 1, 6, 12, 0)
         self.assertTrue(self.room.is_available(naive_start, naive_end))


    def test_is_avail_mult_avails(self):
        
        # create availability event
         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 10, 12, 0)
         self.event = CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'availability', start = start_date, end = end_date)
         
         # create availability event that overlaps
         start_date = datetime(3000, 1, 1, 12, 0)
         end_date = datetime(3000, 1, 5, 12, 0)
         CustomEvent.objects.create(calendar = self.room.calendar, event_type = 'availability', start = start_date, end = end_date)
         
         # overlapping availabilities shouldn't exist but
         # if one works it should return True
         naive_start = datetime(3000, 1, 2, 12, 0)
         naive_end = datetime(3000, 1, 8, 12, 0)
         self.assertTrue(self.room.is_available(naive_start, naive_end))



    
    ###
    ### tests for get_last_available_date
    ###
    def test_get_last_avail_datetime_input(self):
        with self.assertRaises(ValueError):
            self.room.get_last_available_date("string")

    def test_get_last_avail_no_calendar(self):
       
        self.room.calendar.delete()
        self.room.refresh_from_db()
        self.assertIsNone(self.room.get_last_available_date(now()))

    def test_get_last_avail_naive_input_and_open_avail(self):

        start_date = timezone.make_aware(datetime(3000, 1, 1, 12, 0))
        end_date = timezone.make_aware(datetime(3000, 1, 10, 12, 0))
        CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'availability', start = start_date, end = end_date)

        naive_start = datetime(3000, 1, 5, 12, 0)

        # this creates a mock version of get_last_available_room that keeps track of whether or not it has been called
        with patch('django.utils.timezone.make_aware',side_effect=timezone.make_aware) as mocked_make_aware:
        
            # Call the function that should invoke make_aware
            result = self.room.get_last_available_date(naive_start)

            # Check if make_aware was called with the correct datetime and timezone
            mocked_make_aware.assert_any_call(naive_start, get_current_timezone())
            # Make sure the actual function return value is end date
            self.assertEqual(result, end_date)

    
    def test_get_last_avail_no_availabilities(self):
        naive_start = datetime(3000, 1, 5, 12, 0)
        result = self.room.get_last_available_date(naive_start)
        self.assertIsNone(result)

    def test_get_last_avail_doubled_availabilities(self):

        start_date_1 = timezone.make_aware(datetime(3000, 1, 1, 12, 0))
        end_date_1 = timezone.make_aware(datetime(3000, 1, 20, 12, 0))
        CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'availability', start = start_date_1, end = end_date_1)

        start_date_2 = timezone.make_aware(datetime(3000, 1, 1, 12, 0))
        end_date_2 = timezone.make_aware(datetime(3000, 1, 10, 12, 0))
        CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'availability', start = start_date_2, end = end_date_2)


        naive_start = datetime(3000, 1, 5, 12, 0)
        result = self.room.get_last_available_date(naive_start)

        # Make sure the actual function return value is end date
        self.assertEqual(result, end_date_1)



    def test_get_last_avail_another_occupancy_exists(self):
        start_date_1 = timezone.make_aware(datetime(3000, 1, 1, 12, 0))
        end_date_1 = timezone.make_aware(datetime(3000, 1, 20, 12, 0))
        CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'availability', start = start_date_1, end = end_date_1)

        start_date_2 = timezone.make_aware(datetime(3000, 1, 7, 12, 0))
        end_date_2 = timezone.make_aware(datetime(3000, 1, 10, 12, 0))
        CustomEvent.objects.create(calendar = self.room.calendar , event_type = 'occupancy', start = start_date_2, end = end_date_2)

        naive_start = datetime(3000, 1, 5, 12, 0)
        result = self.room.get_last_available_date(naive_start)

        # Make sure the actual function return value is end date
        self.assertEqual(result, start_date_2)






        

class CustomEventModelTest(TestCase):
    def test_test(self):
        self.assertTrue(True)