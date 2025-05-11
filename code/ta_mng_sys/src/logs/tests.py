from django.test import TestCase
from django.contrib.auth import get_user_model
from logs.models import Log
from logs.utils import log_action

User = get_user_model()


class LogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_log_creation(self):
        log = log_action(self.user, 'Test action', 'TestModel', 1)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'Test action')
        self.assertEqual(log.model_name, 'TestModel')
        self.assertEqual(log.object_id, '1')
        
        # Check if log is saved in database
        saved_log = Log.objects.get(id=log.id)
        self.assertEqual(saved_log.action, 'Test action')