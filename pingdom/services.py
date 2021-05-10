from django.db import DatabaseError

from django.contrib.auth.models import User


class CheckDatabase:
    name = "database"

    def check(self):
        try:
            User.objects.exists()
            return True, ""
        except DatabaseError as e:
            return False, e


services_to_check = (CheckDatabase,)
