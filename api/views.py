from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify the API is running
    """
    return Response(
        {
            'status': 'success',
            'message': 'NoCap API is running',
            'version': '1.0.0'
        },
        status=status.HTTP_200_OK
    )
