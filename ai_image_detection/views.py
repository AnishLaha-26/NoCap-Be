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

logger = logging.getLogger(__name__)

@api_view(['GET'])
def ai_image_detection_view(request):
    """
    Basic info endpoint for AI image detection service
    """
    return Response({
        'service': 'AI Image Detection',
        'description': 'Detects AI-generated images',
        'endpoints': {
            'analyze': '/ai-image-detection/analyze/ (POST)',
            'analyze_ai': '/ai-image-detection/analyze_ai/ (POST)'
        }
    })


@api_view(['POST'])
def analyze_image(request):
    """
    Analyze image for AI generation detection
    """
    image = request.FILES.get('image')
    image_url = request.data.get('image_url', '')
    
    if not image and not image_url:
        return Response(
            {'error': 'Image file or image URL is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Placeholder analysis logic
    # In a real implementation, this would use computer vision ML models
    result = {
        'image_provided': bool(image),
        'image_url': image_url,
        'is_ai_generated': False,  # Placeholder
        'confidence': 0.5,  # Placeholder
        'detected_artifacts': [],  # Placeholder
        'analysis': 'AI image analysis not yet implemented - placeholder response'
    }
    
    return Response(result)


@api_view(['POST'])
def analyze_image_ai(request):
    """
    Analyze image for AI generation detection using Hack Club AI API
    Accepts base64 encoded images from frontend
    """
    image_base64 = request.data.get('image_base64', '')
    
    if not image_base64:
        return Response(
            {'error': 'Base64 encoded image is required'}, 
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
        
        # Create comprehensive prompt for AI image detection
        analysis_prompt = f"""
Analyze the provided image for AI generation detection. Look for common AI-generated image artifacts and patterns.

Provide your analysis in this exact JSON format:
{{
    "ai_likelihood_percentage": <number between 0-100>,
    "ai_reasoning": "<brief explanation of AI detection analysis>",
    "ai_confidence": "<high/medium/low>",
    "detected_artifacts": ["<list of specific AI artifacts found>"],
    "image_quality_score": <number between 0-100>,
    "authenticity_score": <number between 0-100>
}}

Focus on detecting:
- Unnatural textures or smoothing
- Inconsistent lighting or shadows
- Anatomical inconsistencies (if humans present)
- Repetitive patterns or artifacts
- Digital compression anomalies typical of AI generation
- Style inconsistencies

Image (base64): {image_base64[:100]}...
"""
        
        # Make request to Hack Club AI API
        api_url = "https://ai.hackclub.com/chat/completions"
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
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
            ]
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        ai_response = response.json()
        ai_content = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Try to parse the AI response as JSON
        try:
            # Extract JSON from the response if it's wrapped in markdown or other text
            json_match = re.search(r'\{[^}]*"ai_likelihood_percentage"[^}]*"authenticity_score"[^}]*\}', ai_content)
            if json_match:
                analysis_data = json.loads(json_match.group())
            else:
                # Fallback parsing if JSON format is not found
                raise ValueError("No valid JSON found in response")
        except (json.JSONDecodeError, ValueError):
            # Fallback: parse manually or provide default analysis
            logger.warning(f"Could not parse AI response as JSON: {ai_content}")
            
            # Try to extract percentages from text response
            ai_percentage_match = re.search(r'AI.*?(\d+)%', ai_content, re.IGNORECASE)
            quality_match = re.search(r'quality.*?(\d+)%', ai_content, re.IGNORECASE)
            
            ai_percentage = int(ai_percentage_match.group(1)) if ai_percentage_match else 50
            quality_score = int(quality_match.group(1)) if quality_match else 70
            
            analysis_data = {
                "ai_likelihood_percentage": ai_percentage,
                "ai_reasoning": ai_content[:200] + "..." if len(ai_content) > 200 else ai_content,
                "ai_confidence": "medium",
                "detected_artifacts": ["Analysis completed"],
                "image_quality_score": quality_score,
                "authenticity_score": 100 - ai_percentage
            }
        
        # Format the comprehensive response
        result = {
            'image_analyzed': True,
            # AI Detection Results
            'ai_likelihood_percentage': analysis_data.get('ai_likelihood_percentage', 50),
            'ai_reasoning': analysis_data.get('ai_reasoning', 'AI detection analysis completed'),
            'ai_confidence': analysis_data.get('ai_confidence', 'medium'),
            'is_ai_generated': analysis_data.get('ai_likelihood_percentage', 50) > 50,
            # Additional Analysis
            'detected_artifacts': analysis_data.get('detected_artifacts', []),
            'image_quality_score': analysis_data.get('image_quality_score', 70),
            'authenticity_score': analysis_data.get('authenticity_score', 50),
            # Metadata
            'model_used': 'Hack Club AI Service',
            'analysis_type': 'image_ai_detection',
            'timestamp': request.META.get('HTTP_DATE', '')
        }
        
        return Response(result)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Hack Club AI API: {str(e)}")
        return Response(
            {
                'error': 'Failed to analyze image - AI service unavailable',
                'details': str(e)
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in image analysis: {str(e)}")
        return Response(
            {
                'error': 'Internal server error during image analysis',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
