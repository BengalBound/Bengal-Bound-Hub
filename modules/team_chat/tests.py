from django.test import TestCase
from .models import Channel, ChannelMember, Message, MessageReaction, DirectMessage

class ChannelModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Channel, "objects"))

class ChannelMemberModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(ChannelMember, "objects"))

class MessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(Message, "objects"))

class MessageReactionModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(MessageReaction, "objects"))

class DirectMessageModelTest(TestCase):
    def test_model_exists(self):
        self.assertTrue(hasattr(DirectMessage, "objects"))

