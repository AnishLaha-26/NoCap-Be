from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
import json
import re
import base64
import logging
import os

logger = logging.getLogger(__name__)

@api_view(['GET'])
def scam_detector_view(request):
    """
    Basic info endpoint for scam detection service
    """
    return Response({
        'service': 'Scam Detection',
        'description': 'Analyzes screenshots of potential scam messages (SMS, email, etc.)',
        'endpoints': {
            'analyze': '/scam-detector/analyze/ (POST)'
        }
    })


@api_view(['POST'])
def analyze_scam_screenshot(request):
    """
    Analyze screenshot for scam detection using OpenAI GPT-4o
    Accepts base64 encoded screenshots from frontend
    """
    image_base64 = request.data.get('image_base64', '')
    
    if not image_base64:
        return Response(
            {'error': 'Base64 encoded screenshot is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate base64 format
        if ',' in image_base64:
            # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
            image_base64 = image_base64.split(',')[1]
        
        # Test if base64 is valid
        try:
            base64.b64decode(image_base64)
        except Exception:
            return Response(
                {'error': 'Invalid base64 image format'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize OpenAI client with API key from environment variables
        try:
            import os
            import logging
            from openai import OpenAI
            
            # Get API key from environment variables
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            
            # Log the API key for debugging (first few characters only)
            logger.info(f"Initializing OpenAI client with API key: {api_key[:8]}...")
            
            # Create client configuration
            client_config = {
                'api_key': api_key,
            }
            
            # Initialize the client with explicit configuration
            client = OpenAI(**client_config)
        except Exception as init_error:
            logger.error(f"Failed to initialize OpenAI client: {str(init_error)}")
            return Response(
                {
                    'error': 'Failed to initialize AI service',
                    'details': str(init_error)
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Create comprehensive prompt for scam detection
        analysis_prompt = """
Analyze the provided screenshot for potential scam indicators. This could be a screenshot of SMS messages, emails, social media messages, or any other communication that might be a scam.

Look for common scam patterns including:
- Urgent language and time pressure
- Requests for personal information (passwords, SSN, bank details)
- Suspicious links or phone numbers
- Grammar and spelling errors
- Impersonation of legitimate organizations
- Too-good-to-be-true offers
- Threats or fear tactics
- Requests for money or gift cards
- Poor formatting or unprofessional appearance

Provide your analysis in this exact JSON format:
{
    "scam_likelihood_percentage": <number between 0-100>,
    "scam_confidence": "<low/medium/high>",
    "scam_type": "<type of scam detected or 'unknown'>",
    "red_flags": ["<list of specific red flags found>"],
    "legitimate_indicators": ["<list of indicators suggesting legitimacy>"],
    "risk_level": "<low/medium/high/critical>",
    "recommended_action": "<specific recommendation for the user>",
    "analysis_summary": "<brief summary of the analysis>"
}

Be thorough in your analysis and consider both scam indicators and legitimate communication patterns.
"""
        
        # Make request to OpenAI GPT-4o
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )
        
        ai_content = response.choices[0].message.content
        
        # Try to parse the AI response as JSON
        try:
            # Extract JSON from the response if it's wrapped in markdown or other text
            json_match = re.search(r'\{[^}]*"scam_likelihood_percentage"[^}]*"analysis_summary"[^}]*\}', ai_content, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Try to find JSON block in markdown
                json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_content, re.DOTALL)
                if json_block_match:
                    analysis_data = json.loads(json_block_match.group(1))
                else:
                    raise ValueError("No valid JSON found in response")
        except (json.JSONDecodeError, ValueError):
            # Fallback: parse manually or provide default analysis
            logger.warning(f"Could not parse AI response as JSON: {ai_content}")
            
            # Try to extract percentages from text response
            scam_percentage_match = re.search(r'scam.*?(\d+)%', ai_content, re.IGNORECASE)
            risk_match = re.search(r'risk.*?(low|medium|high|critical)', ai_content, re.IGNORECASE)
            
            scam_percentage = int(scam_percentage_match.group(1)) if scam_percentage_match else 50
            risk_level = risk_match.group(1).lower() if risk_match else "medium"
            
            analysis_data = {
                "scam_likelihood_percentage": scam_percentage,
                "scam_confidence": "medium",
                "scam_type": "unknown",
                "red_flags": ["Analysis completed"],
                "legitimate_indicators": [],
                "risk_level": risk_level,
                "recommended_action": "Review the message carefully",
                "analysis_summary": ai_content[:300] + "..." if len(ai_content) > 300 else ai_content
            }
        
        # Format the comprehensive response
        result = {
            'screenshot_analyzed': True,
            # Scam Detection Results
            'scam_likelihood_percentage': analysis_data.get('scam_likelihood_percentage', 50),
            'scam_confidence': analysis_data.get('scam_confidence', 'medium'),
            'scam_type': analysis_data.get('scam_type', 'unknown'),
            'is_likely_scam': analysis_data.get('scam_likelihood_percentage', 50) > 60,
            # Analysis Details
            'red_flags': analysis_data.get('red_flags', []),
            'legitimate_indicators': analysis_data.get('legitimate_indicators', []),
            'risk_level': analysis_data.get('risk_level', 'medium'),
            'recommended_action': analysis_data.get('recommended_action', 'Review carefully'),
            'analysis_summary': analysis_data.get('analysis_summary', 'Scam analysis completed'),
            # Metadata
            'model_used': 'OpenAI GPT-4o',
            'analysis_type': 'scam_detection',
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        return Response(
            {
                'error': 'Failed to analyze screenshot - AI service unavailable',
                'details': str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
