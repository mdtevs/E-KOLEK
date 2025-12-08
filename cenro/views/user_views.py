"""
User management views for CENRO admin panel
Handles user approval, editing, deletion, and QR code generation
"""
# Standard library
import logging
import time
import traceback
import uuid

# Django
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError

# Local apps
from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule, RewardCategory,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from accounts.sms_service import send_approval_notification, send_rejection_notification
from cenro.models import AdminActionHistory
from game.models import Question, Choice, WasteCategory, WasteItem
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required
from .utils import generate_qr_code_base64


logger = logging.getLogger(__name__)


@admin_required
@permission_required('can_manage_users')
def adminuser(request):
    """
    Display admin user management dashboard.
    
    Shows pending and approved users with filtering by barangay for 
    Operations Managers. Provides statistics on users, families, and redemptions.
    
    Permissions:
        - Requires admin authentication
        - Requires 'can_manage_users' permission
        - Operations Managers see only their assigned barangays
    
    Args:
        request: HTTP request object with admin session
        
    Returns:
        Rendered template with:
            - users: All users query (for compatibility)
            - pending_users: Users awaiting approval
            - approved_users: Approved active users
            - barangays: Available barangays (filtered for Ops Managers)
            - Statistics: counts for users, families, redemptions
    """
    # Get current admin user from session
    admin_user_id = request.session.get('admin_user_id')
    current_admin = None
    
    if admin_user_id:
        try:
            from cenro.models import AdminUser
            current_admin = AdminUser.objects.get(id=admin_user_id)
        except AdminUser.DoesNotExist:
            pass
    
    # Start with all regular users 
    users_query = Users.objects.filter(is_superuser=False, is_staff=False).select_related('family', 'family__barangay')
    
    # Filter by barangay assignments for Operations Managers
    if current_admin and current_admin.role == 'operations_manager':
        assigned_barangays = current_admin.assigned_barangays.all()
        if assigned_barangays.exists():
            # Filter users by assigned barangays
            users_query = users_query.filter(family__barangay__in=assigned_barangays)
    
    # Order by status (pending first) then creation date
    users = users_query.order_by('status', '-created_at')
    
    # Separate users by status for different tabs
    pending_users = users.filter(status='pending').order_by('-created_at')
    approved_users = users.filter(status='approved').order_by('-created_at')
    
    # Get statistics for the dashboard - only count approved users and their families
    approved_users_count = approved_users.count()
    total_users = approved_users_count  # Only count approved users
    from accounts.models import Family
    
    # Calculate family count based on barangay restrictions
    families_query = Family.objects.filter(members__status='approved')
    if current_admin and current_admin.role == 'operations_manager':
        assigned_barangays = current_admin.assigned_barangays.all()
        if assigned_barangays.exists():
            families_query = families_query.filter(barangay__in=assigned_barangays)
    
    total_families = families_query.distinct().count()
    total_redemptions = Redemption.objects.count()
    
    # Filter barangays list for Operations Managers
    barangays = Barangay.objects.all()
    if current_admin and current_admin.role == 'operations_manager':
        assigned_barangays = current_admin.assigned_barangays.all()
        if assigned_barangays.exists():
            barangays = assigned_barangays
    
    context = {
        'users': users,  # Keep this for backward compatibility if needed
        'pending_users': pending_users,
        'approved_users': approved_users,
        'pending_users_count': pending_users.count(),
        'barangays': barangays,
        'total_users': total_users,
        'total_families': total_families,
        'approved_users_count': approved_users_count,  # Changed the key name to avoid conflict
        'total_redemptions': total_redemptions,
        'timestamp': int(time.time()),
        'admin_user': current_admin,  # Add admin user context
        'barangay_restricted': current_admin and current_admin.role == 'operations_manager' and current_admin.assigned_barangays.exists(),
    }
    
    return render(request, 'adminuser.html', context)


def view_user(request):
    users = Users.objects.all()
    # Generate QR codes for each user using their user ID
    for user in users:
        user.qr_code_data_url = generate_qr_code_base64(str(user.id))
    return render(request, 'idcard.html', {'users': users})

# admincontrol - view for admin control management


def view_single_idcard(request, user_id):
    user = get_object_or_404(Users, id=user_id)
    # Generate QR code using user ID instead of family code
    qr_code_data_url = generate_qr_code_base64(str(user.id))
    user.qr_code_data_url = qr_code_data_url  # Add QR code to user object
    return render(request, 'idcard.html', {'users': [user]})


@admin_required
@permission_required('can_manage_users')
@require_POST
def edit_user(request):
    from django.db import IntegrityError
    from django.http import JsonResponse
    
    try:
        user_id = request.POST.get('user_id')
        logger.debug(f"Editing user with ID: {user_id}")
        
        user = get_object_or_404(Users, id=user_id)
        family_id = user.family.id  # Store family ID separately
        logger.debug(f"Found user: {user.full_name}, family ID: {family_id}")
        
        # Store old values for debugging
        old_full_name = user.full_name
        old_email = user.email
        old_phone = user.phone
        old_is_representative = user.is_family_representative
        
        # Get new values
        new_full_name = request.POST.get('full_name')
        new_email = request.POST.get('email')
        new_phone = request.POST.get('phone')
        new_date_of_birth = request.POST.get('date_of_birth')
        new_gender = request.POST.get('gender')
        is_representative = request.POST.get('is_family_representative') == 'true'
        
        # Validation: Check for duplicate phone (excluding current user)
        if new_phone and new_phone != old_phone:
            if Users.objects.filter(phone=new_phone).exclude(id=user_id).exists():
                return JsonResponse({
                    'success': False,
                    'field': 'phone',
                    'error': 'This phone number is already registered to another user.'
                })
            if Family.objects.filter(representative_phone=new_phone).exclude(id=family_id).exists():
                return JsonResponse({
                    'success': False,
                    'field': 'phone',
                    'error': 'This phone number is already registered as a family representative.'
                })
        
        # Validation: Check for duplicate email (excluding current user)
        if new_email and new_email.strip() and new_email != old_email:
            if Users.objects.filter(email=new_email.strip()).exclude(id=user_id).exists():
                return JsonResponse({
                    'success': False,
                    'field': 'email',
                    'error': 'This email address is already registered to another user.'
                })
        
        # Update user fields
        user.full_name = new_full_name
        user.phone = new_phone
        user.is_family_representative = is_representative
        
        # Update email if provided
        if new_email and new_email.strip():
            user.email = new_email.strip()
            logger.debug(f"Updated email: {user.email}")
        elif new_email == '':
            user.email = None
            logger.debug(f"Cleared email")
        
        # Update date_of_birth if provided
        if new_date_of_birth:
            from datetime import datetime
            try:
                user.date_of_birth = datetime.strptime(new_date_of_birth, '%Y-%m-%d').date()
                logger.debug(f"Updated date_of_birth: {user.date_of_birth}")
            except ValueError:
                logger.debug(f"Invalid date format for date_of_birth: {new_date_of_birth}")
        elif new_date_of_birth == '':
            user.date_of_birth = None
            logger.debug(f"Cleared date_of_birth")
            
        # Update gender if provided - accept short codes and full words, normalize to canonical values
        if new_gender is not None:
            ng = new_gender.strip()
            if ng == '':
                user.gender = None
                logger.debug(f"Cleared gender")
            else:
                ng_lower = ng.lower()
                # Map possible inputs to canonical values
                if ng_lower in ['m', 'male']:
                    user.gender = 'male'
                elif ng_lower in ['f', 'female']:
                    user.gender = 'female'
                elif ng_lower in ['o', 'other']:
                    user.gender = 'other'
                else:
                    # Unknown input - keep previous or set to 'other' as fallback
                    user.gender = 'other'
                logger.debug(f"Updated gender (normalized): {user.gender}")
        
        logger.debug(f"Changes - Name: {old_full_name} -> {user.full_name}")
        logger.debug(f"Changes - Email: {old_email} -> {user.email}")
        logger.debug(f"Changes - Phone: {old_phone} -> {user.phone}")
        logger.debug(f"Changes - Representative: {old_is_representative} -> {user.is_family_representative}")
        
        user.save()
        logger.debug(f"User save completed")
        
        # Get fresh family instance from database
        family = Family.objects.get(id=family_id)
        logger.debug(f"Fresh family instance - Name: {family.family_name}")
        
        # Update family information if this user is the family representative
        family_updated = False
        if user.is_family_representative:
            logger.debug(f"User is family representative, updating family info")
            
            # Update family representative information
            if family.representative_name != user.full_name:
                family.representative_name = user.full_name
                family_updated = True
                logger.debug(f"Updated family representative name: {family.representative_name}")
            
            if family.representative_phone != user.phone:
                family.representative_phone = user.phone
                family_updated = True
                logger.debug(f"Updated family representative phone: {family.representative_phone}")
        
        # Save family if updated
        if family_updated:
            family.save()
            logger.debug(f"Family save completed")
            
            # Refresh family from database to verify
            family.refresh_from_db()
            logger.debug(f"After family refresh - Rep name: {family.representative_name}, Rep phone: {family.representative_phone}")
        
        # Refresh user from database to verify
        user.refresh_from_db()
        logger.debug(f"After final refresh - Name: {user.full_name}, Email: {user.email}, Phone: {user.phone}, Representative: {user.is_family_representative}")
        
        return JsonResponse({'success': True})
        
    except IntegrityError as e:
        logger.debug(f"IntegrityError in edit_user: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Parse the error to determine which field caused the issue
        error_msg = str(e)
        if 'phone' in error_msg.lower():
            return JsonResponse({
                'success': False,
                'field': 'phone',
                'error': 'This phone number is already registered.'
            })
        elif 'email' in error_msg.lower():
            return JsonResponse({
                'success': False,
                'field': 'email',
                'error': 'This email address is already registered.'
            })
        else:
            return JsonResponse({
                'success': False,
                'field': 'general',
                'error': 'A database constraint was violated. Please check your input.'
            })
        
    except Exception as e:
        logger.debug(f"Error in edit_user: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'field': 'general',
            'error': f'An error occurred: {str(e)}'
        })


@admin_required
@permission_required('can_manage_users')
@require_POST
def delete_user(request):
    try:
        user_id = request.POST.get('user_id')
        logger.debug(f"Deleting user with ID: {user_id}")
        
        user = get_object_or_404(Users, id=user_id)
        family_id = user.family.id  # Store family ID separately
        logger.debug(f"Found user: {user.full_name}")
        logger.debug(f"User family ID: {family_id}")
        logger.debug(f"Is family representative: {user.is_family_representative}")
        
        # Get fresh family instance from database
        family = Family.objects.get(id=family_id)
        logger.debug(f"Family: {family.family_name}")
        
        # Check if this is the family representative
        if user.is_family_representative:
            logger.debug(f"User is family representative")
            
            # Check if there are other members in the family
            other_members = family.members.exclude(id=user.id).filter(is_active=True)
            other_members_count = other_members.count()
            logger.debug(f"Other family members count: {other_members_count}")
            
            if other_members_count > 0:
                # Promote another member to be the representative
                new_representative = other_members.first()
                new_representative.is_family_representative = True
                new_representative.save()
                
                # Update family representative information
                family.representative_name = new_representative.full_name
                family.representative_phone = new_representative.phone
                family.save()
                logger.debug(f"Promoted {new_representative.full_name} as new family representative")
            else:
                # This is the last member, delete the family completely
                logger.debug(f"This is the last member of the family, deleting family")
                family_name = family.family_name
                family.delete()
                logger.debug(f"Family '{family_name}' deleted successfully")
                
                # Delete the user
                user.delete()
                logger.debug(f"User deleted successfully")
                
                # Return early since family is deleted
                return redirect('cenro:adminuser')
        
        # Update family member count before deleting user
        family.update_member_count()
        
        # Delete the user
        user.delete()
        logger.debug(f"User deleted successfully")
        
        # Update family member count and points after deletion
        family.refresh_from_db()
        family.update_member_count()
        family.update_family_points()
        logger.debug(f"Family member count and points updated")
        
    except Exception as e:
        logger.debug(f"Error in delete_user: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return redirect('cenro:adminuser') 


# def function for adminschedule add schedule, edit schedule, and delete schedule


@admin_required
@permission_required('can_manage_users')
@require_POST
def approve_user(request):
    try:
        user_id = request.POST.get('user_id')
        logger.debug(f"Received user_id: {user_id}")
        
        user = get_object_or_404(Users, id=user_id)
        family_id = user.family.id  # Store family ID separately
        logger.debug(f"Found user {user.full_name} (ID: {user.id})")
        logger.debug(f"User family ID: {family_id}")
        logger.debug(f"Before approval - User status: {user.status}, Family status: {user.family.status}")
        logger.debug(f"User referral info - referred_by_code: {user.referred_by_code}, bonus_awarded: {user.referral_bonus_awarded}")
        
        # Update user status
        user.status = 'approved'
        user.save()
        logger.debug(f"User save completed. New status should be: {user.status}")
        
        # Award referral bonus if user was referred and hasn't received bonus yet
        if user.referred_by_code and not user.referral_bonus_awarded:
            logger.debug(f"User has referral code {user.referred_by_code}, awarding bonus...")
            user.award_referral_bonus()
            logger.debug(f"Referral bonus awarded. User points: {user.total_points}, Bonus awarded: {user.referral_bonus_awarded}")
        
        # Refresh user from database to verify
        user.refresh_from_db()
        logger.debug(f"After user refresh - User status: {user.status}")
        
        # Get a fresh family instance from the database
        family = Family.objects.get(id=family_id)
        logger.debug(f"Fresh family instance - Name: {family.family_name}, Status: {family.status}")
        
        if family.status == 'pending':
            logger.debug(f"Family was pending, approving it now...")
            family.status = 'approved'
            family.save()
            logger.debug(f"Family save completed")
            
            # Refresh family from database to verify
            family.refresh_from_db()
            logger.debug(f"After family refresh - Family status: {family.status}")
            
            # Also refresh the user to get updated family relationship
            user.refresh_from_db()
            logger.debug(f"After final refresh - User family status: {user.family.status}")
        else:
            logger.debug(f"Family status was already: {family.status}")
        
        logger.debug(f"Final status - User: {user.status}, Family: {family.status}")
        
        # Send SMS notification to approved user
        try:
            logger.debug(f"Sending approval SMS to {user.phone}...")
            sms_result = send_approval_notification(user)
            
            if sms_result.get('success'):
                message_id = sms_result.get('message_id', 'unknown')
                logger.info(f"SMS approval notification sent successfully. Message ID: {message_id}")
                logger.info(f"Approval SMS sent to {user.full_name} ({user.phone}). Message ID: {message_id}")
                messages.success(request, f'User {user.full_name} approved successfully. SMS notification sent.')
            else:
                error = sms_result.get('error', 'Unknown error')
                logger.warning(f"SMS notification failed: {error}")
                logger.warning(f"Failed to send approval SMS to {user.full_name} ({user.phone}): {error}")
                messages.warning(request, f'User {user.full_name} approved successfully, but SMS notification failed: {error}')
                
        except Exception as sms_error:
            logger.warning(f"SMS notification error: {str(sms_error)}")
            logger.error(f"Error sending approval SMS to {user.full_name} ({user.phone}): {str(sms_error)}")
            messages.warning(request, f'User {user.full_name} approved successfully, but SMS notification encountered an error.')
        
    except Exception as e:
        logger.debug(f"Error in approve_user: {str(e)}")
        logger.error(f"Error in approve_user: {str(e)}")
        messages.error(request, f'Error approving user: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return redirect('cenro:adminuser')


@admin_required
@permission_required('can_manage_users')
@require_POST
def reject_user(request):
    """
    Reject and permanently delete a pending user registration.
    If the user is a family representative, the entire family will be deleted.
    This ensures rejected registrations don't clutter the database.
    """
    try:
        user_id = request.POST.get('user_id')
        rejection_reason = request.POST.get('rejection_reason', '')  # Optional reason from admin
        
        user = get_object_or_404(Users, id=user_id)
        user_full_name = user.full_name  # Store for logging
        user_phone = user.phone
        is_representative = user.is_family_representative
        family = user.family
        family_name = family.family_name
        family_id = family.id
        
        logger.debug(f"Rejecting and deleting user {user_full_name} (ID: {user.id})")
        logger.debug(f"User is family representative: {is_representative}")
        logger.debug(f"Family: {family_name} (ID: {family_id})")
        
        # Send SMS notification BEFORE deletion (while user object still exists)
        sms_sent = False
        sms_error_msg = None
        try:
            logger.debug(f"Sending rejection SMS to {user_phone}...")
            sms_result = send_rejection_notification(user, reason=rejection_reason)
            
            if sms_result.get('success'):
                message_id = sms_result.get('message_id', 'unknown')
                logger.info(f"SMS rejection notification sent successfully. Message ID: {message_id}")
                logger.info(f"Rejection SMS sent to {user_full_name} ({user_phone}). Message ID: {message_id}")
                sms_sent = True
            else:
                sms_error_msg = sms_result.get('error', 'Unknown error')
                logger.warning(f"SMS notification failed: {sms_error_msg}")
                logger.warning(f"Failed to send rejection SMS to {user_full_name} ({user_phone}): {sms_error_msg}")
                
        except Exception as sms_error:
            sms_error_msg = str(sms_error)
            logger.warning(f"SMS notification error: {sms_error_msg}")
            logger.error(f"Error sending rejection SMS to {user_full_name} ({user_phone}): {sms_error_msg}")
        
        # If this is a family representative, delete the entire family
        if is_representative:
            logger.debug(f"User is family representative - checking family members...")
            
            # Check if there are other members in the family
            other_members = family.members.exclude(id=user.id).filter(is_active=True)
            other_members_count = other_members.count()
            logger.debug(f"Other family members (excluding this user): {other_members_count}")
            
            if other_members_count > 0:
                # Delete all other family members first
                logger.debug(f"Deleting {other_members_count} other family member(s)...")
                for member in other_members:
                    logger.debug(f"- Deleting member: {member.full_name}")
                    member.delete()
            
            # Delete the family (this will cascade delete the representative user)
            logger.debug(f"Deleting family '{family_name}'...")
            family.delete()
            logger.info(f"Family '{family_name}' and all members permanently deleted from database")
            
            # Log the action
            logger.info(f"Family '{family_name}' (ID: {family_id}) rejected and deleted by admin. Representative: {user_full_name}")
            
        else:
            # This is a regular family member, just delete the user
            logger.debug(f"User is a family member - deleting user only...")
            user.delete()
            logger.info(f"User '{user_full_name}' permanently deleted from database")
            
            # Update family member count and points
            try:
                family.refresh_from_db()
                family.update_member_count()
                family.update_family_points()
                logger.debug(f"Family member count and points updated")
            except Family.DoesNotExist:
                logger.debug(f"Family no longer exists (may have been deleted)")
            
            # Log the action
            logger.info(f"User '{user_full_name}' (ID: {user_id}) rejected and deleted by admin from family '{family_name}'")
        
        # Show success message based on SMS status
        if sms_sent:
            messages.success(request, f'User {user_full_name} rejected and removed from database. SMS notification sent.')
        elif sms_error_msg:
            messages.warning(request, f'User {user_full_name} rejected and removed from database, but SMS notification failed: {sms_error_msg}')
        else:
            messages.success(request, f'User {user_full_name} rejected and removed from database.')
    
    except Exception as e:
        logger.debug(f"Error in reject_user: {str(e)}")
        logger.error(f"Error in reject_user: {str(e)}")
        messages.error(request, f'Error rejecting user: {str(e)}')
        import traceback
        traceback.print_exc()
    
    return redirect('cenro:adminuser')


# ✅ Get User Details by User ID (for QR scanner)
# @ratelimit(key='ip', rate='60/m', method='GET')  # Temporarily disabled - requires Redis/Memcached for production
@admin_required
def get_user_by_id(request):
    """
    Secure admin endpoint to get user details by ID
    """
    # Note: Rate limiting temporarily disabled - enable with Redis/Memcached in production
    # if getattr(request, 'limited', False):
    #     return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
    
    user_id = request.GET.get('id', '').strip()
    
    # Validate UUID format
    try:
        uuid.UUID(user_id)
    except (ValueError, AttributeError):
        return JsonResponse({'error': 'Invalid ID format'}, status=400)
    
    try:
        user = Users.objects.get(id=user_id, is_active=True, status='approved')
        return JsonResponse({
            'name': user.full_name,
            'family_code': user.family.family_code,
            'total_points': user.total_points,
            'user_id': str(user.id),
            'family_id': str(user.family.id)
        })
    except Users.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

# @ratelimit(key='ip', rate='30/m', method='POST')  # Temporarily disabled - requires Redis/Memcached for production


def get_user_by_family_code(request):
    code = request.GET.get('code')
    
    # Find family by family_code first
    family = Family.objects.filter(family_code=code).first()
    
    if not family:
        return JsonResponse({'name': '', 'family_code': ''})
    
    # Get the family representative or first active user from the family
    user = family.members.filter(is_active=True, status='approved').first()
    
    if user:
        return JsonResponse({'name': user.full_name, 'family_code': family.family_code})
    return JsonResponse({'name': '', 'family_code': ''})

# ✅ Get User Details by User ID (for QR scanner)
# @ratelimit(key='ip', rate='60/m', method='GET')  # Temporarily disabled - requires Redis/Memcached for production


