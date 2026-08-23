from django.test import TestCase

from authentication.models import CustomUser
from chat.models import Conversation
from chat.serializers import ConversationSerializer


class ConversationDuplicationTests(TestCase):
    def setUp(self):
        self.alice = CustomUser.objects.create_user(
            username="alice", email="alice@example.com", password="pass12345"
        )
        self.bob = CustomUser.objects.create_user(
            username="bob", email="bob@example.com", password="pass12345"
        )

    def _create(self, user, participant_ids, **extra):
        serializer = ConversationSerializer(
            data=extra or {"is_group": False},
            context={"request": type("R", (), {"user": user})(), "participant_ids": participant_ids},
        )
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def test_direct_conversation_is_reused(self):
        first = self._create(self.alice, [str(self.bob.id)])
        second = self._create(self.bob, [str(self.alice.id)])

        self.assertEqual(first.pk, second.pk)
        self.assertTrue(getattr(second, "_reused", False))
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(Conversation.objects.get(pk=first.pk).participants.count(), 2)

    def test_new_direct_conversation_created_for_other_pair(self):
        carol = CustomUser.objects.create_user(
            username="carol", email="carol@example.com", password="pass12345"
        )
        first = self._create(self.alice, [str(self.bob.id)])
        other = self._create(self.alice, [str(carol.id)])

        self.assertNotEqual(first.pk, other.pk)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_group_conversations_are_never_reused(self):
        first = self._create(
            self.alice, [str(self.bob.id)], is_group=True, name="Team"
        )
        second = self._create(
            self.alice, [str(self.bob.id)], is_group=True, name="Team copy"
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(Conversation.objects.count(), 2)
