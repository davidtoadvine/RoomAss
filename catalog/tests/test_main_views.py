from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models import Person, Building, Section, CustomEvent, Room
from schedule.models import Calendar, Event
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from django.utils.timezone import now, is_aware, get_current_timezone, make_aware, make_naive
from unittest.mock import patch
from django.utils import timezone
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import timedelta
from catalog.forms import DateRangeForm
from django.utils.text import slugify

DEFAULT_GUEST_TYPE = 2 #known

TODAY_STRING = datetime.today().strftime('%Y-%m-%d')
TOMORRROW_STRING = (datetime.today()+ timedelta(days=1)).strftime('%Y-%m-%d')

class AvailableRoomsTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name = "Building")
        self.section = Section.objects.create(name = "Section" ,building = self.building)


        self.start = timezone.now()

    def test_get_request_default(self):

        response = self.client.get(reverse('available_rooms'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/available_rooms.html')

        self.assertIn('form', response.context)
        self.assertIn('available_rooms_info', response.context)
        self.assertIn('start_date', response.context)
        self.assertIn('end_date', response.context)
        self.assertIn('guest_type', response.context)


        self.assertEqual(response.context['start_date'], TODAY_STRING)
        self.assertEqual(response.context['end_date'], TOMORRROW_STRING)
        self.assertEqual(response.context['guest_type'], DEFAULT_GUEST_TYPE)

    

    def test_get_request_with_session_dates(self):
        
         session = self.client.session

         session['start_date'] = (self.start + timedelta(days=5)).strftime('%Y-%m-%d')
         session['end_date'] = (self.start + timedelta(days=9)).strftime('%Y-%m-%d')
         session['guest_type'] = 3
         session.save()

         response = self.client.get(reverse('available_rooms'))

         self.assertEqual(response.context['start_date'], session['start_date'])
         self.assertEqual(response.context['end_date'], session['end_date'])
         self.assertEqual(response.context['guest_type'], session['guest_type'])


         
    
    def test_valid_post_request(self):
        form_data = {
            'start_date': TODAY_STRING,
            'end_date': TOMORRROW_STRING,
            'guest_type': DEFAULT_GUEST_TYPE
        }

        form = DateRangeForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        response = self.client.post(reverse('available_rooms'),form_data)
        self.assertEqual(response.status_code, 302), #Redirect after valid form submisison
        self.assertRedirects(response, reverse('available_rooms'))

        session = self.client.session
        self.assertEqual(session['start_date'], form_data['start_date'])
        self.assertEqual(session['end_date'], form_data['end_date'])
        self.assertEqual(int(session['guest_type']), form_data['guest_type'])

    def test_invalid_post_request(self):
  
        form_data = {
            'start_date': '',  
            'end_date': '',    
            'guest_type': '' 
        }
        response = self.client.post(reverse('available_rooms'), form_data)


       # Check that the form is invalid and has the appropriate errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('start_date', form.errors)
        self.assertIn('end_date', form.errors)
        self.assertIn('guest_type', form.errors)
    
        # Verify the error messages for required fields
        self.assertEqual(form.errors['start_date'], ['This field is required.'])
        self.assertEqual(form.errors['end_date'], ['This field is required.'])
        self.assertEqual(form.errors['guest_type'], ['This field is required.'])
    
    def test_available_rooms_no_rooms(self):
       
        session = self.client.session

        session['start_date'] = (self.start + timedelta(days=5)).strftime('%Y-%m-%d')
        session['end_date'] = (self.start + timedelta(days=9)).strftime('%Y-%m-%d')
        session['guest_type'] = 3
        session.save()

        response = self.client.get(reverse('available_rooms'))

        self.assertEqual(response.context['available_rooms_info'], [])

    def test_available_rooms_all_unavailable(self):

        unavailable_room_1 = Room.objects.create(
            number = 1,
            section = self.section,
            calendar=Calendar.objects.create(slug= slugify(1)),

        )
        unavailable_room_1.calendar.delete()

        unavailable_room_2 = Room.objects.create(
            number = 2,
            section = self.section,
            calendar=Calendar.objects.create(slug = slugify(2)),
        )
        unavailable_room_2.calendar.delete()


        session = self.client.session

        session['start_date'] = (self.start + timedelta(days=5)).strftime('%Y-%m-%d')
        session['end_date'] = (self.start + timedelta(days=9)).strftime('%Y-%m-%d')
        session['guest_type'] = 3
        session.save()

        response = self.client.get(reverse('available_rooms'))

        self.assertEqual(response.context['available_rooms_info'], [])


    def test_available_rooms_mixture(self):

        # open room without owner
        room1 = Room.objects.create(
            number = 1,
            section = self.section,
            calendar=Calendar.objects.create(slug= slugify(1)),
        )

        # open room with owner
        person_for_2 = Person.objects.create(name = 'person_for_2', preference = Person.Preference.ANYONE)
        room2 = Room.objects.create(
            number = 2,
            section = self.section,
            calendar=Calendar.objects.create(slug= slugify(2)),
            owner = person_for_2
        )
        CustomEvent.objects.create(
              event_type = 'availability',
              guest_name = "guest_for_2",
              calendar = room2.calendar,
              
                    start= self.start - timedelta(days=2),
                    end= self.start + timedelta(days=20),
                    title= "title2"
                )

        # unavailable room via guest type
        person_for_3= Person.objects.create(name = 'person_for_3', preference = Person.Preference.MEMBERS)

        room3 = Room.objects.create(
            number = 3,
            section = self.section,
            calendar=Calendar.objects.create(slug = slugify(3)),
            owner = person_for_3
        )
        CustomEvent.objects.create(
              event_type = 'availability',
              calendar = room3.calendar,
              
                    start= self.start - timedelta(days=2),
                    end= self.start + timedelta(days=20),
                    title= "title3"
                )




        # unavailable room via date range
        person_for_4= Person.objects.create(name = 'person_for_4', preference = Person.Preference.ANYONE)

        room4 = Room.objects.create(
            number = 4,
            section = self.section,
            calendar=Calendar.objects.create(slug = slugify(4)),
            owner = person_for_4
        )

        CustomEvent.objects.create(
              event_type = 'availability',
              calendar = room4.calendar,
              
                    start= self.start + timedelta(days=7),
                    end= self.start + timedelta(days=20),
                    title= "title4"
                )
        
        # unavailable room via date range
        person_for_5= Person.objects.create(name = 'person_for_5', preference = Person.Preference.ANYONE)

        room5 = Room.objects.create(
            number = 5,
            section = self.section,
            calendar=Calendar.objects.create(slug = slugify(5)),
            owner = person_for_5
        )

        CustomEvent.objects.create(
              event_type = 'availability',
              calendar = room5.calendar,
              
                    start= self.start + timedelta(days=3),
                    end= self.start + timedelta(days=8),
                    title= "title5"
                )
        
        # open room with owner
        person_for_6 = Person.objects.create(name = 'person_for_6', preference = Person.Preference.KNOWN)
        room6 = Room.objects.create(
            number = 6,
            section = self.section,
            calendar=Calendar.objects.create(slug= slugify(6)),
            owner = person_for_6
        )
        CustomEvent.objects.create(
              event_type = 'availability',
              guest_name = "guest_for_6",
              calendar = room6.calendar,
              
                    start= self.start + timedelta(days=4),
                    end= self.start + timedelta(days=10),
                    title= "title6"
                )



        session = self.client.session

        session['start_date'] = (self.start + timedelta(days=5)).strftime('%Y-%m-%d')
        session['end_date'] = (self.start + timedelta(days=9)).strftime('%Y-%m-%d')
        session['guest_type'] = 2
        session.save()

        response = self.client.get(reverse('available_rooms'))

        self.assertEqual(response.context['available_rooms_info'][0][0], room1)
        self.assertEqual(response.context['available_rooms_info'][1][0], room2)
        self.assertEqual(response.context['available_rooms_info'][2][0], room6)

class AllGuestsTest(TestCase):
    def setUp(self):
        self.building = Building.objects.create(name = "Building")
        self.section = Section.objects.create(name = "Section" ,building = self.building)

    
    def test_all_guests_renders_successfully(self):
        response = self.client.get(reverse('all_guests'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/all_guests.html')

    def test_all_guests_no_events(self):
        response = self.client.get(reverse('all_guests'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['occupancy_events'], [])

    def test_all_guests_room_without_owner(self):

        calendar1 = Calendar.objects.create(slug = slugify(2))
        room1= Room.objects.create(section = self.section, number =1,calendar = calendar1)
        calendar1.room=room1
        room1.save()
        calendar1.save()

        CustomEvent.objects.create(
            event_type='occupancy',
            calendar= calendar1,
            guest_name="John Doe",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )
        response = self.client.get(reverse('all_guests'))
        events = response.context['occupancy_events']

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['room_owner'], "Unassigned")

    def test_all_guests_room_with_owner(self):

        owner = Person.objects.create(name="Alice")
        calendar1 = Calendar.objects.create(slug = slugify(1))
        room1= Room.objects.create(section = self.section, number = 1,calendar = calendar1, owner = owner)
        calendar1.room = room1
        room1.save()
        calendar1.save()

        CustomEvent.objects.create(
            event_type='occupancy',
            calendar=calendar1,
            guest_name="Jane Doe",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )
        response = self.client.get(reverse('all_guests'))
        events = response.context['occupancy_events']

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['room_owner'], owner)
    
    def test_all_guests_only_occupancy_events(self):
        owner = Person.objects.create(name="Alice")

        calendar1 = Calendar.objects.create(slug = slugify(1))
        room1= Room.objects.create(section = self.section, number = 1,calendar = calendar1, owner = owner)
        calendar1.room = room1
        room1.save()
        calendar1.save()

        # Occupancy Event
        CustomEvent.objects.create(
            event_type='occupancy',
            calendar=calendar1,
            guest_name="Occupancy Guest",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )

        # Availability Event
        CustomEvent.objects.create(
            event_type='availability',
            calendar=calendar1,
            guest_name="Availability Guest",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(reverse('all_guests'))
        events = response.context['occupancy_events']

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['guest_name'], "Occupancy Guest")
    
    def test_all_guests_event_details(self):

        owner = Person.objects.create(name="Owner Name")
        calendar1 = Calendar.objects.create(slug = slugify(1))
        room1= Room.objects.create(section = self.section, number = 1,calendar = calendar1, owner = owner)
        calendar1.room = room1
        room1.save()
        calendar1.save()

        event = CustomEvent.objects.create(
            event_type='occupancy',
            calendar=calendar1,
            guest_name="John Doe",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(reverse('all_guests'))
        events = response.context['occupancy_events']

        self.assertEqual(len(events), 1)
        event_info = events[0]
        self.assertEqual(event_info['guest_name'], "John Doe")
        #self.assertEqual(event_info['creator'], "Admin")
        self.assertEqual(event_info['start_date'], event.start)
        self.assertEqual(event_info['end_date'], event.end)
        self.assertEqual(event_info['room_name'], str(room1))
        self.assertEqual(event_info['room_id'], room1.id)
        self.assertEqual(event_info['room_owner'], owner)
    
    def test_all_guests_multiple_events(self):
        owner1 = Person.objects.create(name="Alice")

        calendar1 = Calendar.objects.create(slug = slugify(1))
        room1= Room.objects.create(section = self.section, number = 1,calendar = calendar1, owner = owner1)
        calendar1.room = room1
        room1.save()
        calendar1.save()

        owner2 = Person.objects.create(name="Bob")

        calendar2 = Calendar.objects.create(slug = slugify(2))
        room2= Room.objects.create(section = self.section, number = 2,calendar = calendar2, owner = owner2)
        calendar2.room = room2
        room2.save()
        calendar2.save()

        CustomEvent.objects.create(
            event_type='occupancy',
            calendar=calendar1,
            guest_name="John Doe",
            start=timezone.now(),
            end=timezone.now() + timedelta(days=1),
        )

        CustomEvent.objects.create(
            event_type='occupancy',
            calendar=calendar2,
            guest_name="Jane Doe",
            start=timezone.now() - timedelta(days=1),
            end=timezone.now(),
        )

        response = self.client.get(reverse('all_guests'))
        events = response.context['occupancy_events']

        self.assertEqual(len(events), 2)