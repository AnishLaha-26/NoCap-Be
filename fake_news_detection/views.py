from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import requests
import json
import time


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
        # Step 1: Extract content from URL using Extractor API with retries
        extracted_data = extract_data_from_url(url)
        
        # Handle error response from extract_data_from_url
        if extracted_data and 'error' in extracted_data:
            return Response(
                {'error': extracted_data['error']},
                status=status.HTTP_504_GATEWAY_TIMEOUT if 'timeout' in str(extracted_data.get('error', '')).lower() 
                      else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if not extracted_data:
            return Response(
                {'error': 'Failed to extract content from URL after multiple attempts'}, 
                status=status.HTTP_504_GATEWAY_TIMEOUT
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
        error_msg = str(e)
        print(f"Error in analyze_news: {error_msg}")
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Provide more specific error messages for common issues
        if 'timeout' in error_msg.lower():
            error_msg = "The request timed out while processing the URL"
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif 'connection' in error_msg.lower():
            error_msg = "Could not connect to the content extraction service"
        
        return Response(
            {'error': error_msg}, 
            status=status_code
        )


def extract_data_from_url(url, max_retries=3, initial_timeout=60):  # Increased initial timeout to 60 seconds
    """
    Extract full data from URL using Extractor API with retries and backoff
    Returns the complete API response JSON or error dict if all retries fail
    """
    API_KEY = "97eb467b8ae65f155821a44df22fadbb051f2020"
    api_url = "https://extractorapi.com/api/v1/extractor/"
    
    params = {
        "apikey": API_KEY,
        "url": url,
        "fields": "title,author,date_published,domain,images"
    }
    
    for attempt in range(max_retries):
        try:
            # Increase timeout with each retry (exponential backoff)
            timeout = initial_timeout * (attempt + 1)
            print(f"Attempt {attempt + 1}/{max_retries} - Timeout: {timeout}s")
            
            response = requests.get(
                api_url, 
                params=params, 
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'text' in data and data['text']:
                    print("Successfully extracted data from URL")
                    return data
                elif 'status' in data and data['status'] == 'error':
                    error_msg = f"Extractor API Error: {data.get('message', 'Unknown error')}"
                    print(error_msg)
                else:
                    print("No text content found in response")
            else:
                print(f"Extractor API Error ({response.status_code}): {response.text}")
            
            # If we get here, the request failed but didn't raise an exception
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after {timeout} seconds"
            print(error_msg)
            if attempt == max_retries - 1:
                return {
                    "error": "Request to content extraction service timed out",
                    "status": "error"
                }
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(error_msg)
            if attempt == max_retries - 1:
                return {
                    "error": f"Failed to fetch content: {str(e)}",
                    "status": "error"
                }
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(error_msg)
            if attempt == max_retries - 1:
                return {
                    "error": "An unexpected error occurred while processing the request",
                    "status": "error"
                }
    
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


