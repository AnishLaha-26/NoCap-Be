import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ClaudeAPIView(APIView):
    """
    API View to handle requests to Claude 3.5
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize the Anthropic client with API key from environment variables
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to the Claude 3.5 API
        
        Expected request body:
        {
            "messages": [
                {"role": "user", "content": "Hello, Claude!"}
            ],
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 1000,
            "temperature": 0.7,
            "system": "You are a helpful AI assistant."
        }
        """
        try:
            # Get the request data
            messages = request.data.get('messages', [])
            model = request.data.get('model', 'claude-3-5-sonnet-20240620')
            max_tokens = request.data.get('max_tokens', 1000)
            temperature = request.data.get('temperature', 0.7)
            system = request.data.get('system', 'You are a helpful AI assistant.')
            
            # Validate required fields
            if not messages:
                return Response(
                    {"error": "Messages are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Make the API call to Claude
            with self.client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                
                # Return the full response
                return Response({
                    "response": full_response,
                    "model": model
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
