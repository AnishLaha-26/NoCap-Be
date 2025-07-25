import os
import uuid
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import anthropic
from dotenv import load_dotenv
from .models import ClaudeConversation, ClaudeMessage, ClaudeAPIUsage
from .serializers import ClaudeConversationSerializer, ClaudeMessageSerializer

# Load environment variables
load_dotenv()


class ClaudeAPIView(APIView):
    """
    Enhanced API View to handle requests to Claude 3.5 with conversation tracking
    """
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the Anthropic client with API key from environment variables
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to the Claude 3.5 API with conversation tracking
        
        Expected request body:
        {
            "message": "Hello, Claude!",
            "session_id": "optional-session-id",
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1000,
            "temperature": 0.7,
            "system": "You are a helpful AI assistant.",
            "save_conversation": true
        }
        """
        try:
            # Get the request data
            message = request.data.get('message', '')
            session_id = request.data.get('session_id', str(uuid.uuid4()))
            model = request.data.get('model', 'claude-3-5-sonnet-20240620')
            max_tokens = request.data.get('max_tokens', 1000)
            temperature = request.data.get('temperature', 0.7)
            system = request.data.get('system', 'You are a helpful AI assistant.')
            save_conversation = request.data.get('save_conversation', True)
            
            # Validate required fields
            if not message:
                return Response(
                    {"error": "Message is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create conversation
            conversation = None
            if save_conversation:
                conversation, created = ClaudeConversation.objects.get_or_create(
                    session_id=session_id,
                    defaults={'user': request.user if request.user.is_authenticated else None}
                )
                
                # Save user message
                ClaudeMessage.objects.create(
                    conversation=conversation,
                    role='user',
                    content=message,
                    model_used=model
                )
            
            # Prepare messages for API call
            messages = [{"role": "user", "content": message}]
            
            # If we have a conversation, include previous messages for context
            if conversation and conversation.messages.count() > 1:
                previous_messages = conversation.messages.exclude(
                    role='user', content=message
                ).order_by('created_at')[:10]  # Limit to last 10 messages for context
                
                api_messages = []
                for msg in previous_messages:
                    api_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
                api_messages.append({"role": "user", "content": message})
                messages = api_messages
            
            # Make the API call to Claude
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages
            )
            
            # Extract response content
            response_content = ""
            if response.content and len(response.content) > 0:
                response_content = response.content[0].text
            
            # Track API usage
            if save_conversation:
                ClaudeAPIUsage.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    model_used=model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    estimated_cost=self._calculate_cost(model, response.usage.input_tokens, response.usage.output_tokens)
                )
                
                # Save assistant response
                ClaudeMessage.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=response_content,
                    model_used=model,
                    tokens_used=response.usage.output_tokens
                )
            
            # Return the response
            return Response({
                "response": response_content,
                "session_id": session_id,
                "model": model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }, status=status.HTTP_200_OK)
                
        except anthropic.APIConnectionError as e:
            return Response(
                {"error": f"Connection error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except anthropic.RateLimitError as e:
            return Response(
                {"error": "Rate limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except anthropic.APIStatusError as e:
            return Response(
                {"error": f"API error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_cost(self, model, input_tokens, output_tokens):
        """
        Calculate estimated cost based on Claude pricing
        """
        # Claude 3.5 Sonnet pricing (as of 2024)
        pricing = {
            'claude-3-5-sonnet-20240620': {
                'input': 0.003,  # per 1K tokens
                'output': 0.015  # per 1K tokens
            }
        }
        
        if model in pricing:
            input_cost = (input_tokens / 1000) * pricing[model]['input']
            output_cost = (output_tokens / 1000) * pricing[model]['output']
            return Decimal(str(input_cost + output_cost))
        
        return Decimal('0.0')


class ConversationListView(APIView):
    """
    View to list user's conversations
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        conversations = ClaudeConversation.objects.filter(
            user=request.user
        ).prefetch_related('messages')
        
        serializer = ClaudeConversationSerializer(conversations, many=True)
        return Response(serializer.data)


class ConversationDetailView(APIView):
    """
    View to get conversation details with messages
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        try:
            conversation = ClaudeConversation.objects.get(
                session_id=session_id,
                user=request.user
            )
            serializer = ClaudeConversationSerializer(conversation)
            return Response(serializer.data)
        except ClaudeConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
