from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import ClaudeConversation, ClaudeMessage, ClaudeAPIUsage


class ClaudeIntegrationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.conversation = ClaudeConversation.objects.create(
            user=self.user,
            session_id='test-session-123',
            title='Test Conversation'
        )

    def test_conversation_creation(self):
        self.assertEqual(self.conversation.user, self.user)
        self.assertEqual(self.conversation.session_id, 'test-session-123')
        self.assertEqual(self.conversation.title, 'Test Conversation')

    def test_message_creation(self):
        message = ClaudeMessage.objects.create(
            conversation=self.conversation,
            role='user',
            content='Hello, Claude!',
            model_used='claude-3-5-sonnet-20240620'
        )
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.role, 'user')
        self.assertEqual(message.content, 'Hello, Claude!')

    def test_api_usage_tracking(self):
        usage = ClaudeAPIUsage.objects.create(
            user=self.user,
            model_used='claude-3-5-sonnet-20240620',
            input_tokens=100,
            output_tokens=150,
            total_tokens=250,
            estimated_cost=0.001
        )
        self.assertEqual(usage.user, self.user)
        self.assertEqual(usage.total_tokens, 250)


class ClaudeAPIViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('claude_integration.views.anthropic.Anthropic')
    def test_claude_api_call(self, mock_anthropic):
        # Mock the Anthropic client response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Hello! How can I help you today?")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=15)
        
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        url = reverse('claude_integration:claude-chat')
        data = {
            'message': 'Hello, Claude!',
            'model': 'claude-3-5-sonnet-20240620',
            'max_tokens': 1000,
            'temperature': 0.7
        }

        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('response', response.data)
        self.assertIn('session_id', response.data)
        self.assertEqual(response.data['response'], "Hello! How can I help you today?")

    def test_claude_api_missing_message(self):
        url = reverse('claude_integration:claude-chat')
        data = {}

        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_conversation_list_view(self):
        # Create a test conversation
        conversation = ClaudeConversation.objects.create(
            user=self.user,
            session_id='test-session',
            title='Test Conversation'
        )

        url = reverse('claude_integration:conversation-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['session_id'], 'test-session')

    def test_conversation_detail_view(self):
        # Create a test conversation with messages
        conversation = ClaudeConversation.objects.create(
            user=self.user,
            session_id='test-session',
            title='Test Conversation'
        )
        ClaudeMessage.objects.create(
            conversation=conversation,
            role='user',
            content='Hello!',
            model_used='claude-3-5-sonnet-20240620'
        )

        url = reverse('claude_integration:conversation-detail', kwargs={'session_id': 'test-session'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['session_id'], 'test-session')
        self.assertEqual(len(response.data['messages']), 1)
