import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RoomAss.settings')  

# Initialize Django
django.setup()

from django.utils.timezone import now
from catalog.models import CustomEvent



def delete_ended_events():
    current_time = now()
    print(current_time)
    targets = CustomEvent.objects.filter(end__lt=current_time)
    print(f"Deleted {targets.count()} expired event(s).")

    targets.delete()

if __name__ == "__main__":
    delete_ended_events()