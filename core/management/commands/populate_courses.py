# core/management/commands/populate_courses.py
from django.core.management.base import BaseCommand
from core.models import HorseRacingCourse

class Command(BaseCommand):
    help = 'Populate HorseRacingCourse with known courses'

    def handle(self, *args, **options):
        courses = [
            {'course_id': 204, 'name': 'Auteuil', 'region': 'FR'},
            {'course_id': 47, 'name': 'Southwell', 'region': 'GB'},
            # Add more courses as needed
        ]
        for course in courses:
            course_obj, created = HorseRacingCourse.objects.get_or_create(
                course_id=course['course_id'],
                defaults={'name': course['name'], 'region': course['region']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created course: {course['name']}"))
            else:
                self.stdout.write(f"Course already exists: {course['name']}")