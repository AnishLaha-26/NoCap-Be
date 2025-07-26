from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
import json


@api_view(['GET'])
def fake_news_detection_view(request):
    """
    Basic info endpoint for fake news detection service
    """
    return Response({
        'service': 'Fake News Detection',
        'description': 'Detects fake news and misinformation',
        'endpoints': {
            'analyze': '/fake-news-detection/analyze/ (POST)'
        }
    })


@api_view(['POST'])
def analyze_news(request):
    """
    Analyze news content for fake news detection
    Extract text from URL using API Tier, then fact-check using AI Hack Club
    """
    url = request.data.get('url', '')
    
    if not url:
        return Response(
            {'error': 'URL is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Step 1: Extract content from URL using Extractor API
        extracted_data = extract_data_from_url(url)
        if not extracted_data:
            return Response(
                {'error': 'Failed to extract content from URL'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Step 2: Fact-check using the full API response data
        fact_check_result = fact_check_with_ai(extracted_data)
        
        result = {
            'url': url,
            'extracted_text': extracted_data.get('text', '')[:500] + '...' if len(extracted_data.get('text', '')) > 500 else extracted_data.get('text', ''),
            'extracted_metadata': {
                'title': extracted_data.get('title', ''),
                'author': extracted_data.get('author', ''),
                'date_published': extracted_data.get('date_published', ''),
                'domain': extracted_data.get('domain', '')
            },
            'fact_check_result': fact_check_result,
            'status': 'success'
        }
        
        return Response(result)
    
    except Exception as e:
        return Response(
            {'error': f'Analysis failed: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def extract_data_from_url(url):
    """
    Extract full data from URL using Extractor API
    Returns the complete API response JSON for comprehensive fact-checking
    """
    API_KEY = "97eb467b8ae65f155821a44df22fadbb051f2020"
    api_url = "https://extractorapi.com/api/v1/extractor/"
    
    params = {
        "apikey": API_KEY,
        "url": url,
        "fields": "title,author,date_published,domain,images"  # Request additional metadata
    }
    
    try:
        print(f"Sending request to Extractor API for URL: {url}")
        response = requests.get(api_url, params=params, timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text[:500]}...")  # Print first 500 chars of response
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Parsed JSON data keys: {list(data.keys())}")
                
                # Check if the response contains text (successful extraction)
                if 'text' in data and data['text']:
                    print("Successfully extracted data from URL")
                    return data  # Return the full JSON response
                elif 'status' in data and data['status'] == 'error':
                    error_msg = f"Extractor API Error: {data.get('message', 'Unknown error')}"
                    print(error_msg)
                    return None
                else:
                    print("No text content found in response")
                    return None
                    
            except json.JSONDecodeError:
                error_msg = "Failed to parse API response as JSON"
                print(error_msg)
                return None
        else:
            error_msg = f"Extractor API Error ({response.status_code}): {response.text}"
            print(error_msg)
            return None
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        print(error_msg)
        return None
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return None


def fact_check_with_ai(extracted_data):
    """
    Fact-check content using AI Hack Club API (same service as text AI detection)
    Takes the full JSON response from Extractor API for comprehensive analysis
    """
    ai_url = "https://ai.hackclub.com/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Extract relevant information from the API response
    text = extracted_data.get('text', '')
    title = extracted_data.get('title', '')
    author = extracted_data.get('author', '')
    date_published = extracted_data.get('date_published', '')
    domain = extracted_data.get('domain', '')
    url = extracted_data.get('url', '')
    
    # Create comprehensive prompt for fact-checking analysis with metadata
    analysis_prompt = f"""
Analyze the following article for factual accuracy, misinformation, and credibility using both the content and metadata.

Article Metadata:
- URL: {url}
- Domain: {domain}
- Title: {title}
- Author: {author}
- Date Published: {date_published}

Article Content:
"{text}"

Provide your analysis in this exact JSON format:
{{
    "credibility_score": <number between 0-100>,
    "fake_news_likelihood_percentage": <number between 0-100>,
    "fact_check_reasoning": "<detailed explanation considering both content and source credibility>",
    "confidence": "<high/medium/low>",
    "key_claims": ["<list of key claims that need verification>"],
    "red_flags": ["<list of potential red flags, biases, or source issues>"],
    "recommendation": "<trustworthy/questionable/likely_false>"
}}
"""
    
    payload = {
        "messages": [
            {
                "role": "user", 
                "content": analysis_prompt
            }
        ]
    }
    
    try:
        response = requests.post(ai_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        ai_response = response.json()
        ai_content = ai_response.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # Try to parse the AI response as JSON
        try:
            # Extract JSON from the response if it's wrapped in markdown or other text
            import re
            json_match = re.search(r'\{[^}]*"credibility_score"[^}]*"recommendation"[^}]*\}', ai_content, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group())
                return analysis_data
            else:
                # Try to find JSON block in markdown
                json_block_match = re.search(r'```json\s*(\{.*?\})\s*```', ai_content, re.DOTALL)
                if json_block_match:
                    analysis_data = json.loads(json_block_match.group(1))
                    return analysis_data
                else:
                    raise ValueError("No valid JSON found in response")
        except (json.JSONDecodeError, ValueError):
            # Fallback: parse manually or provide default analysis
            print(f"Could not parse AI response as JSON: {ai_content}")
            
            # Try to extract percentages from text response
            credibility_match = re.search(r'credibility.*?(\d+)%', ai_content, re.IGNORECASE)
            fake_match = re.search(r'fake.*?(\d+)%', ai_content, re.IGNORECASE)
            
            credibility_score = int(credibility_match.group(1)) if credibility_match else 70
            fake_percentage = int(fake_match.group(1)) if fake_match else 30
            
            return {
                "credibility_score": credibility_score,
                "fake_news_likelihood_percentage": fake_percentage,
                "fact_check_reasoning": ai_content[:300] + "..." if len(ai_content) > 300 else ai_content,
                "confidence": "medium",
                "key_claims": ["Analysis completed"],
                "red_flags": ["Manual parsing used"],
                "recommendation": "questionable" if fake_percentage > 50 else "trustworthy"
            }
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling Hack Club AI API: {str(e)}")
        return {
            "credibility_score": 50,
            "fake_news_likelihood_percentage": 50,
            "fact_check_reasoning": "Fact-checking service temporarily unavailable",
            "confidence": "low",
            "key_claims": [],
            "red_flags": ["Service unavailable"],
            "recommendation": "questionable"
        }
    except Exception as e:
        print(f"Error in fact-checking: {str(e)}")
        return {
            "credibility_score": 50,
            "fake_news_likelihood_percentage": 50,
            "fact_check_reasoning": "Fact-checking failed due to technical error",
            "confidence": "low",
            "key_claims": [],
            "red_flags": ["Technical error"],
            "recommendation": "questionable"
        }


