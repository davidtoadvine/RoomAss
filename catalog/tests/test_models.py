from django.test import TestCase
from django.contrib.auth.models import User
from catalog.models import Person
from django.core.exceptions import ValidationError

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
        person.preference = Person.Preference.KNOWN_PEOPLE
        self.assertEqual(person.preference, Person.Preference.KNOWN_PEOPLE)

    def test_str_method(self):
        person = Person.objects.create(name="Testperson")
        self.assertEqual(str(person), "Testperson")

