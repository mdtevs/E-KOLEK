"""
Game Configuration API Views for Mobile App
Provides endpoints for Flutter app to fetch game cooldown configurations
"""

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response
from rest_framework import status
from game.models import GameConfiguration
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_game_configurations(request):
    """
    Get all active game cooldown configurations for the mobile app.
    
    Returns cooldown durations in milliseconds for compatibility with Flutter Duration.
    
    Response format:
    {
        "quiz": {
            "cooldown_hours": 72,
            "cooldown_minutes": 0,
            "total_milliseconds": 259200000,
            "formatted_duration": "72 hours"
        },
        "drag_drop": {
            "cooldown_hours": 72,
            "cooldown_minutes": 0,
            "total_milliseconds": 259200000,
            "formatted_duration": "72 hours"
        },
        "default": {
            "cooldown_hours": 72,
            "cooldown_minutes": 0,
            "total_milliseconds": 259200000,
            "formatted_duration": "72 hours"
        }
    }
    """
    try:
        # Get configurations for each game type
        game_types = ['quiz', 'drag_drop']
        configurations = {}
        
        for game_type in game_types:
            cooldown = GameConfiguration.get_cooldown_for_game(game_type)
            
            if cooldown:
                configurations[game_type] = {
                    'cooldown_hours': cooldown.cooldown_hours,
                    'cooldown_minutes': cooldown.cooldown_minutes,
                    'total_milliseconds': cooldown.total_cooldown_milliseconds,
                    'total_seconds': cooldown.total_cooldown_seconds,
                    'formatted_duration': cooldown.get_formatted_duration(),
                    'is_active': cooldown.is_active
                }
            else:
                # No configuration found - return inactive state
                configurations[game_type] = {
                    'cooldown_hours': 0,
                    'cooldown_minutes': 0,
                    'total_milliseconds': 0,
                    'total_seconds': 0,
                    'formatted_duration': 'Not configured',
                    'is_active': False
                }
        
        # Also provide the default/all configuration
        default_config = GameConfiguration.get_cooldown_for_game('all')
        if default_config:
            configurations['default'] = {
                'cooldown_hours': default_config.cooldown_hours,
                'cooldown_minutes': default_config.cooldown_minutes,
                'total_milliseconds': default_config.total_cooldown_milliseconds,
                'total_seconds': default_config.total_cooldown_seconds,
                'formatted_duration': default_config.get_formatted_duration(),
                'is_active': default_config.is_active
            }
        else:
            configurations['default'] = {
                'cooldown_hours': 0,
                'cooldown_minutes': 0,
                'total_milliseconds': 0,
                'total_seconds': 0,
                'formatted_duration': 'Not configured',
                'is_active': False
            }
        
        logger.info(f"User {request.user.username} fetched game configurations")
        
        return Response({
            'success': True,
            'configurations': configurations
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching game configurations: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch game configurations'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_game_cooldown(request, game_type):
    """
    Get cooldown configuration for a specific game type.
    
    URL Parameters:
    - game_type: 'quiz' or 'drag_drop'
    
    Response format:
    {
        "success": true,
        "game_type": "quiz",
        "cooldown_hours": 72,
        "cooldown_minutes": 0,
        "total_milliseconds": 259200000,
        "formatted_duration": "72 hours"
    }
    """
    try:
        # Validate game type
        valid_game_types = ['quiz', 'drag_drop', 'all']
        if game_type not in valid_game_types:
            return Response({
                'success': False,
                'error': f'Invalid game type. Must be one of: {", ".join(valid_game_types)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get configuration
        cooldown = GameConfiguration.get_cooldown_for_game(game_type)
        
        if cooldown:
            response_data = {
                'success': True,
                'game_type': game_type,
                'cooldown_hours': cooldown.cooldown_hours,
                'cooldown_minutes': cooldown.cooldown_minutes,
                'total_milliseconds': cooldown.total_cooldown_milliseconds,
                'total_seconds': cooldown.total_cooldown_seconds,
                'formatted_duration': cooldown.get_formatted_duration(),
                'is_active': cooldown.is_active
            }
        else:
            # Return inactive state if no configuration exists
            response_data = {
                'success': True,
                'game_type': game_type,
                'cooldown_hours': 0,
                'cooldown_minutes': 0,
                'total_milliseconds': 0,
                'total_seconds': 0,
                'formatted_duration': 'Not configured',
                'is_active': False,
                'note': 'No cooldown configured - games are unrestricted'
            }
        
        logger.info(f"User {request.user.username} fetched cooldown for {game_type}")
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error fetching game cooldown for {game_type}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to fetch game cooldown'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_quiz_cooldown(request):
    """
    Convenience endpoint to get quiz game cooldown configuration.
    Returns cooldown in milliseconds for Flutter Duration compatibility.
    """
    return get_game_cooldown(request, 'quiz')


@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_dragdrop_cooldown(request):
    """
    Convenience endpoint to get drag-and-drop game cooldown configuration.
    Returns cooldown in milliseconds for Flutter Duration compatibility.
    """
    return get_game_cooldown(request, 'drag_drop')
