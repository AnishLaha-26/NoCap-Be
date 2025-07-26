from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import requests
import json
import logging
import asyncio
import time
from urllib.parse import urlparse
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import requests
import httpx
from bs4 import BeautifulSoup
from boilerpy3 import extractors
import httpx
import re
import asyncio


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


from asgiref.sync import sync_to_async

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_news(request):
    """
    Analyze news content for fake news detection
    Extract text from URL using API Tier, then fact-check using AI Hack Club
    """
    print("Analyze news endpoint hit")  # Debug log
    
    # Get URL from request data
    url = request.data.get('url')
    if not url:
        print("No URL provided in request")  # Debug log
        return Response(
            {'error': 'URL is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    print(f"Processing URL: {url}")  # Debug log
    
    try:
        # Run the async function in an event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Extract text from URL using async function
        extracted_data = loop.run_until_complete(extract_data_from_url_async(url))
        print(f"Extraction result: {extracted_data.get('status', 'unknown')}")  # Debug log
        
        if not extracted_data.get('success', False):
            print(f"Extraction failed: {extracted_data.get('error', 'Unknown error')}")  # Debug log
            return Response(
                {'error': extracted_data.get('error', 'Failed to extract content from URL')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get fact check from AI (this part remains synchronous for now)
        fact_check_result = fact_check_with_ai(extracted_data)
        
        # Prepare response
        response_data = {
            'url': url,
            'extracted_text': extracted_data.get('text', '')[:1000] + '...' if extracted_data.get('text') else '',
            'extracted_metadata': {
                'title': extracted_data.get('title', ''),
                'author': extracted_data.get('author', ''),
                'date_published': extracted_data.get('date_published', ''),
                'domain': extracted_data.get('domain', ''),
                'word_count': extracted_data.get('word_count', 0)
            },
            'fact_check_result': fact_check_result,
            'status': 'success'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Error in analyze_news: {str(e)}", exc_info=True)  # Debug log with traceback
        error_msg = f"An error occurred while processing the request: {str(e)}"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Provide more specific error messages for common issues
        if 'timeout' in str(e).lower():
            error_msg = "The request timed out while processing the URL"
            status_code = status.HTTP_504_GATEWAY_TIMEOUT
        elif 'connection' in str(e).lower():
            error_msg = "Could not connect to the content extraction service"
        
        return Response(
            {'error': error_msg}, 
            status=status_code
        )


def clean_text(text):
    """Clean and normalize text by removing extra whitespace and special characters"""
    if not text:
        return ""
    
    # First, remove all non-ASCII characters
    text = text.encode('ascii', 'ignore').decode('ascii', 'ignore')
    
    # Replace multiple spaces, newlines, and tabs with a single space
    text = ' '.join(text.split())
    
    # Remove non-printable characters but keep common punctuation
    import string
    printable = set(string.printable + ' ' + '.,!?;:')
    text = ''.join(filter(lambda x: x in printable, text))
    
    # Remove URLs and email addresses
    import re
    text = re.sub(r'http\S+|www\.\S+', '', text)  # URLs
    text = re.sub(r'\S+@\S+', '', text)  # Email addresses
    
    # Remove any remaining non-alphanumeric characters except basic punctuation and spaces
    text = re.sub(r'[^\w\s.,!?;:]+', '', text)
    
    # Remove any words that are just numbers or single characters
    text = ' '.join([word for word in text.split() 
                    if len(word) > 1 or word.lower() in ['a', 'i']])
    
    # Trim any leading/trailing whitespace
    return text.strip()


async def extract_data_from_url_async(url, max_retries=3, timeout=30):
    """
    Extract text and metadata from a URL using a simple and reliable approach.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        for attempt in range(max_retries):
            try:
                # Make the HTTP request
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Extract title
                title = ''
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                
                # Remove script, style, and other non-content elements
                for element in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'button', 'nav', 'footer', 'header']):
                    element.decompose()
                
                # Get all text content with basic formatting
                full_text = soup.get_text(separator='\n', strip=True)
                
                # Clean up the text
                full_text = '\n'.join(line.strip() for line in full_text.splitlines() if line.strip())
                
                # If we don't have enough text, try to get paragraphs
                if len(full_text) < 100:
                    paragraphs = soup.find_all('p')
                    if paragraphs:
                        full_text = '\n\n'.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
                
                # If still no content, use the raw text (first 10,000 chars)
                if not full_text.strip():
                    full_text = response.text[:10000]
                
                # Extract metadata
                metadata = {
                    'title': title,
                    'author': '',
                    'date_published': '',
                    'domain': urlparse(url).netloc,
                    'word_count': len(full_text.split())
                }
                
                # Try to extract author and date from common meta tags
                for meta in soup.find_all('meta'):
                    property_attr = meta.get('property', '').lower()
                    name_attr = meta.get('name', '').lower()
                    content = meta.get('content', '')
                    
                    if not content:
                        continue
                        
                    # Check for author in meta tags
                    if any(x in property_attr for x in ['author', 'article:author']) or \
                       any(x in name_attr for x in ['author', 'article:author']):
                        metadata['author'] = content
                    
                    # Check for publication date in meta tags
                    if any(x in property_attr for x in ['article:published_time', 'og:published_time', 'pubdate']) or \
                       any(x in name_attr for x in ['date', 'pubdate', 'publishdate', 'timestamp']):
                        metadata['date_published'] = content
                    
                    # Also check for date in other attributes
                    for attr, value in meta.attrs.items():
                        if 'date' in attr.lower() and value and not metadata['date_published']:
                            metadata['date_published'] = value
                
                result = {
                    'success': True,
                    'url': url,
                    'text': full_text,
                    **metadata
                }
                return result
                
            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                print(error_msg)
                if attempt == max_retries - 1:  # Last attempt
                    error_details = str(e)
                    if hasattr(e, 'response') and e.response is not None:
                        error_details += f" | Status Code: {e.response.status_code}"
                        if hasattr(e.response, 'text'):
                            error_details += f" | Response: {e.response.text[:200]}"
                    return {
                        'success': False,
                        'error': f'Failed to fetch URL after {max_retries} attempts: {error_details}',
                        'status': 'error'
                    }
                backoff_time = 1 * (attempt + 1)
                print(f"Retrying in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)  # Use asyncio.sleep for async context
        
        return {
            'success': False,
            'error': 'Failed to extract content from URL',
            'status': 'error'
        }


def fact_check_with_ai(extracted_data):
    """
    Fact-check content using AI Hack Club API
    Analyzes the extracted content from BeautifulSoup for credibility and potential misinformation
    """
    ai_url = "https://ai.hackclub.com/chat/completions"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Extract information from the BeautifulSoup extraction
    text = extracted_data.get('text', '')
    title = extracted_data.get('title', '')
    author = extracted_data.get('author', 'Unknown')
    date_published = extracted_data.get('date_published', 'Not specified')
    domain = extracted_data.get('domain', 'Unknown domain')
    url = extracted_data.get('url', 'Unknown URL')
    word_count = extracted_data.get('word_count', 0)
    
    # Create a more detailed prompt for fact-checking
    analysis_prompt = f"""
You are a fact-checking assistant analyzing an article extracted from a webpage. 
The content was automatically extracted using web scraping and may contain some formatting artifacts.

SOURCE ANALYSIS:
- Source URL: {url}
- Domain: {domain}
- Article Title: "{title}"
- Author: {author} (note: this may be incomplete as it's automatically extracted)
- Publication Date: {date_published}
- Content Length: {word_count} words

CONTENT TO ANALYZE:
"""
    
    # Add the content in chunks to avoid hitting token limits
    max_content_length = 15000  # Leave room for the rest of the prompt
    content_preview = text[:max_content_length]
    if len(text) > max_content_length:
        content_preview += "\n[Content truncated due to length]"
    
    # Add the content to the prompt with proper escaping
    analysis_prompt += '""\n' + content_preview + '\n""\n'
    
    analysis_prompt += """

INSTRUCTIONS:
1. Evaluate the credibility of the content considering the source and content
2. Identify any potential misinformation, biases, or unsubstantiated claims
3. Consider that the content was automatically extracted and may be missing some context
4. Be particularly alert for:
   - Sensational or emotionally charged language
   - Lack of credible sources or references
   - Logical fallacies or inconsistencies
   - Outdated information (check against the publication date)
   - Potential bias in the reporting

OUTPUT FORMAT (JSON only, no other text):
{
    "credibility_score": <0-100, where 100 is most credible>,
    "fake_news_likelihood_percentage": <0-100, estimated likelihood of being misinformation>,
    "fact_check_reasoning": "<detailed analysis of the content's credibility, 3-5 sentences>",
    "confidence": "<high/medium/low, your confidence in this assessment>",
    "key_claims": ["<list the 3-5 most important claims that should be fact-checked>", "..."],
    "red_flags": ["<list any red flags found in the content or source>", "..."],
    "recommendation": "<trustworthy/questionable/likely_false, your overall assessment>",
    "source_reliability": "<reliable/mixed/unreliable, assessment of the source domain>"
}

IMPORTANT: Respond with ONLY the JSON object, no other text or markdown formatting.
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


