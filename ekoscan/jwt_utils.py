"""
JWT utility functions for EkoScan Admin Authentication
Provides custom JWT token generation and validation for AdminUser model
"""
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from cenro.models import AdminUser

logger = logging.getLogger(__name__)


class AdminRefreshToken(RefreshToken):
    """
    Custom JWT refresh token for AdminUser authentication
    Extends simplejwt RefreshToken to work with AdminUser model instead of Users model
    """
    
    @classmethod
    def for_admin(cls, admin_user):
        """
        Returns an authorization token for the given admin user that will be
        provided after the OTP verification.
        """
        token = cls()
        
        # Set admin user ID in token
        token['admin_id'] = str(admin_user.id)
        token['username'] = admin_user.username
        token['role'] = admin_user.role
        token['email'] = admin_user.email
        
        # Add admin-specific claims
        token['is_admin'] = True
        token['can_manage_users'] = getattr(admin_user, 'can_manage_users', False)
        token['can_manage_controls'] = getattr(admin_user, 'can_manage_controls', False)
        token['can_manage_points'] = getattr(admin_user, 'can_manage_points', False)
        token['can_manage_rewards'] = getattr(admin_user, 'can_manage_rewards', False)
        
        return token


class AdminJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class for AdminUser model
    Authenticates admin users using JWT tokens
    """
    
    def get_user(self, validated_token):
        """
        Returns the admin user associated with the given validated token
        Overrides the default get_user to work with AdminUser model
        """
        try:
            admin_id = validated_token.get('admin_id')
            
            if not admin_id:
                raise InvalidToken('Token contained no recognizable admin identification')
            
            try:
                admin_user = AdminUser.objects.get(id=admin_id)
                
                # Check if admin is still active
                if not admin_user.is_active:
                    raise InvalidToken('Admin user is inactive')
                
                return admin_user
                
            except AdminUser.DoesNotExist:
                raise InvalidToken('Admin user not found')
                
        except KeyError:
            raise InvalidToken('Token contained no recognizable admin identification')


def create_admin_tokens(admin_user):
    """
    Create JWT tokens for admin user
    Returns dict with access_token, refresh_token, and admin info
    """
    try:
        refresh = AdminRefreshToken.for_admin(admin_user)
        
        admin_data = {
            'success': True,
            'message': 'Login successful',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer',
            'expires_in': 3600,  # 1 hour in seconds
            'admin_info': {
                'id': str(admin_user.id),
                'username': admin_user.username,
                'email': admin_user.email,
                'role': admin_user.role,
                'full_name': admin_user.full_name,
                'permissions': {
                    'can_manage_users': getattr(admin_user, 'can_manage_users', False),
                    'can_manage_controls': getattr(admin_user, 'can_manage_controls', False),
                    'can_manage_points': getattr(admin_user, 'can_manage_points', False),
                    'can_manage_rewards': getattr(admin_user, 'can_manage_rewards', False),
                }
            }
        }
        
        logger.info(f"JWT tokens created for admin: {admin_user.username}")
        return admin_data
        
    except Exception as e:
        logger.error(f"Error creating admin JWT tokens: {str(e)}")
        raise


def refresh_admin_token(refresh_token_str):
    """
    Refresh admin JWT tokens
    Returns new access_token and refresh_token
    """
    try:
        refresh = AdminRefreshToken(refresh_token_str)
        
        return {
            'success': True,
            'message': 'Token refreshed successfully',
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': 'Bearer',
            'expires_in': 3600
        }
        
    except TokenError as e:
        logger.error(f"Error refreshing admin token: {str(e)}")
        raise
