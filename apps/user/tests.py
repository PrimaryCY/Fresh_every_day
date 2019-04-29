from django.test import TestCase
from django.test import Client
from rest_framework.reverse import reverse

class Login(TestCase):

    def test_login(self):
        response=self.client.get('http://127.0.0.1/web/login/')
        print(response.data)
