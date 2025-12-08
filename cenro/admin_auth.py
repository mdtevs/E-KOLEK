from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.db import transaction
from django.http import JsonResponse
from django.core.paginator import Paginator
from accounts.models import Family, Barangay
from cenro.models import AdminUser, AdminActionHistory
import logging

logger = logging.getLogger(__name__)

def admin_required(view_func):
    """Decorator to require admin authentication - Production Ready"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_user_id'):
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Please log in to access the admin panel.'}, status=401)
            messages.error(request, 'Please log in to access the admin panel.')
            return redirect('cenro:admin_login')
        
        # Check if admin user still exists and is active
        try:
            admin_user = AdminUser.objects.get(
                id=request.session['admin_user_id'],
                is_active=True
            )
            request.admin_user = admin_user
        except AdminUser.DoesNotExist:
            # Clear only admin session data, preserve user authentication
            request.session.pop('admin_user_id', None)
            request.session.pop('admin_username', None)
            request.session.pop('admin_role', None)
            request.session.pop('admin_full_name', None)
            request.session.save()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'success': False, 'error': 'Your admin session has expired. Please log in again.'}, status=401)
            messages.error(request, 'Your admin session has expired. Please log in again.')
            return redirect('cenro:admin_login')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(allowed_roles):
    """Decorator to require specific admin roles"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'admin_user'):
                messages.error(request, 'Please log in to access this page.')
                return redirect('cenro:admin_login')
            
            if request.admin_user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('cenro:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def permission_required(permission_name):
    """Decorator to require specific permissions"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'admin_user'):
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': 'Please log in to access this page.'}, status=401)
                messages.error(request, 'Please log in to access this page.')
                return redirect('cenro:admin_login')
            
            if not getattr(request.admin_user, permission_name, False):
                # Check if this is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    return JsonResponse({'success': False, 'error': 'You do not have permission to perform this action.'}, status=403)
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('cenro:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

@csrf_protect
def admin_login(request):
    """Admin login view"""
    # Don't process messages at view level - let JavaScript handle filtering
    # This prevents duplicate message issues
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            try:
                admin_user = AdminUser.objects.get(username=username, is_active=True)
                
                
                if admin_user.is_account_locked():
                    messages.error(request, 'Your account is temporarily locked due to too many failed login attempts. Please contact a Super Administrator.')
                    return redirect('cenro:admin_login')
                
                # Check password
                if admin_user.check_password(password):
                    # Handle different admin statuses
                    if admin_user.status == 'suspended':
                        messages.error(request, 'Your admin account has been suspended. Please contact a Super Admin.')
                        return redirect('cenro:admin_login')
                    
                    # Reset failed login attempts on successful login
                    admin_user.failed_login_attempts = 0
                    admin_user.account_locked_until = None
                    admin_user.last_login = timezone.now()
                    admin_user.save()
                    
                    # Handle password change requirement
                    if admin_user.must_change_password:
                        request.session['temp_admin_id'] = str(admin_user.id)
                        messages.info(request, 'You must change your password before continuing.')
                        return redirect('cenro:admin_change_password')
                    
                    # Create session for admin user
                    request.session['admin_user_id'] = admin_user.id
                    request.session['admin_username'] = admin_user.username
                    request.session['admin_role'] = admin_user.role
                    request.session['admin_full_name'] = admin_user.full_name
                    
                    # Log successful login
                    logger.info(f"Admin login successful: {username} ({admin_user.role})")
                    
                    # Log login action to AdminActionHistory
                    from cenro.admin_utils import log_admin_action
                    log_admin_action(admin_user, None, 'login', f'Successful login with role: {admin_user.role}', request)
                    
                    with open('security.log', 'a') as log_file:
                        log_file.write(f"[{timezone.now()}] Successful admin login: {username} ({admin_user.role})\n")
                    
                    # Redirect based on role
                    if admin_user.role == 'super_admin':
                        response = redirect('cenro:dashboard')  # Main admin landing page
                    elif admin_user.role == 'operations_manager':
                        response = redirect('cenro:dashboard')  # Main admin landing page
                    elif admin_user.role == 'content_rewards_manager':
                        response = redirect('cenro:dashboard')  # Main admin landing page
                    elif admin_user.role == 'security_analyst':
                        response = redirect('cenro:dashboard')  # Main admin landing page
                    else:
                        response = redirect('cenro:dashboard')  # Main admin landing page
                    
                    # Django session is already set above - no JWT needed
                    logger.info(f"Admin session created for {username}")
                    
                    return response
                else:
                    # Handle failed password - show remaining attempts for valid usernames only
                    admin_user.increment_failed_login()
                    
                    # Calculate remaining attempts AFTER incrementing
                    remaining_attempts = max(0, 5 - admin_user.failed_login_attempts)  
                    
                    # Debug logging
                    logger.debug(f"Failed login for {username}: {admin_user.failed_login_attempts} total attempts, {remaining_attempts} remaining")
                    
                    # Check if account is now locked after this failed attempt
                    if admin_user.is_account_locked():
                        # Send lock notification email
                        from cenro.admin_email_service import send_lock_notification_email
                        send_lock_notification_email(admin_user)
                        
                        # Create admin locked notification
                        from cenro.models import AdminNotification
                        AdminNotification.create_admin_locked_notification(admin_user)
                        
                        messages.error(request, 'Too many failed login attempts. Your account has been temporarily locked. Check your email for details.')
                        # Log account lock
                        with open('security.log', 'a') as log_file:
                            log_file.write(f"[{timezone.now()}] Account locked due to failed attempts: {username}\n")
                    else:
                        # Show remaining attempts
                        messages.error(request, f'Invalid password. {remaining_attempts} attempt{"s" if remaining_attempts != 1 else ""} remaining before account lock.')
                    
                    logger.warning(f"Failed admin login attempt: {username}")
                    # Use redirect instead of render to prevent form resubmission on refresh (PRG pattern)
                    return redirect('cenro:admin_login')
            except AdminUser.DoesNotExist:
                # Handle invalid username - don't show attempt count for security
                messages.error(request, 'Invalid username or password.')
                logger.warning(f"Failed admin login attempt with invalid username: {username}")
                # Use redirect to prevent form resubmission
                return redirect('cenro:admin_login')
                
            except Exception as e:
                # Handle system errors
                logger.error(f"Admin login error: {str(e)}")
                messages.error(request, 'An error occurred during login. Please try again.')
                # Use redirect to prevent form resubmission
                return redirect('cenro:admin_login')
        
        # If username or password is empty, redirect back
        return redirect('cenro:admin_login')
    
    return render(request, 'adminlogin.html')

@csrf_protect
def admin_create(request):
    """Create a new admin account (Super Admin only)"""
    # Check if user is logged in as admin
    admin_user_id = request.session.get('admin_user_id')
    if not admin_user_id:
        messages.error(request, 'Please log in as an admin to access this page.')
        return redirect('cenro:admin_login')
    
    try:
        current_admin = AdminUser.objects.get(id=admin_user_id)
        
        # Only Super Admins can create other admins
        if current_admin.role != 'super_admin':
            messages.error(request, 'Access denied. Only Super Admins can create new admin accounts.')
            return redirect('cenro:dashboard')
        
        # Get barangays for form
        barangays = Barangay.objects.all().order_by('name')
        
        if request.method == 'POST':
            full_name = request.POST.get('full_name', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password', '')
            confirm_password = request.POST.get('confirm_password', '')
            role = request.POST.get('role', '')
            selected_barangays = request.POST.getlist('barangays')
            
            # Validation
            if not all([full_name, username, email, password, confirm_password, role]):
                messages.error(request, 'All fields are required.')
                return render(request, 'admin_create.html', {'barangays': barangays})
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'admin_create.html', {'barangays': barangays})
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'admin_create.html', {'barangays': barangays})
            
            if AdminUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists.')
                return render(request, 'admin_create.html', {'barangays': barangays})
            
            # Check email uniqueness
            if AdminUser.objects.filter(email__iexact=email).exists():
                messages.error(request, 'Email address is already registered to another admin account.')
                return render(request, 'admin_create.html', {'barangays': barangays})
            
            try:
                with transaction.atomic():
                    # Store the plain password temporarily to send via email
                    temp_password = password
                    
                    # Create admin user
                    admin_user = AdminUser.objects.create(
                        username=username,
                        full_name=full_name,
                        email=email,
                        role=role,
                        status='approved',  # Auto-approved since created by Super Admin
                        approved_by=current_admin,
                        approval_date=timezone.now(),
                        assigned_by=current_admin,
                        must_change_password=True  # Force password change on first login
                    )
                    # Set password using the proper method
                    admin_user.set_password(password)
                    admin_user.save()  # This will trigger the save() method which sets permissions
                    
                    # Assign barangays if selected (mainly for Operations Managers)
                    if selected_barangays and role == 'operations_manager':
                        barangays_to_assign = Barangay.objects.filter(id__in=selected_barangays)
                        admin_user.assigned_barangays.set(barangays_to_assign)
                    
                    # Send credentials email to new admin
                    from cenro.admin_email_service import send_credentials_email
                    email_sent = send_credentials_email(admin_user, temp_password, current_admin)
                    
                    logger.info(f"New admin user created by {current_admin.username}: {username} ({role})")
                    
                    if email_sent:
                        messages.success(request, f'Admin account "{username}" has been created successfully! Credentials have been sent to {email}.')
                    else:
                        messages.warning(request, f'Admin account "{username}" was created, but the email notification failed to send. Please provide credentials manually.')
                    
                    # Log the creation for AdminActionHistory
                    from cenro.admin_utils import log_admin_action
                    barangay_detail = f" with barangays: {', '.join([b.name for b in barangays_to_assign])}" if selected_barangays and role == 'operations_manager' else ""
                    log_admin_action(current_admin, admin_user, 'create_admin', f'Admin account created with role: {role}{barangay_detail}', request)
                    
                    # Log the creation for security tracking
                    with open('security.log', 'a') as log_file:
                        log_file.write(f"[{timezone.now()}] Admin account created: {username} ({role}) by {current_admin.username} - Email: {email}\n")
                    
                    return redirect('cenro:admin_management')
                    
            except Exception as e:
                logger.error(f"Admin creation error: {str(e)}")
                messages.error(request, 'An error occurred while creating the account. Please try again.')
        
        return render(request, 'admin_create.html', {'barangays': barangays})
        
    except AdminUser.DoesNotExist:
        messages.error(request, 'Admin account not found. Please log in again.')
        return redirect('cenro:admin_login')

@csrf_protect
def admin_change_password(request):
    """Change password for admin (for first login or password reset)"""
    temp_admin_id = request.session.get('temp_admin_id')
    if not temp_admin_id:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('cenro:admin_login')
    
    try:
        admin_user = AdminUser.objects.get(id=temp_admin_id)
        
        if request.method == 'POST':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            # Validation
            if not all([current_password, new_password, confirm_password]):
                messages.error(request, 'All fields are required.')
                return render(request, 'admin_change_password.html', {'admin_user': admin_user})
            
            if not admin_user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'admin_change_password.html', {'admin_user': admin_user})
            
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return render(request, 'admin_change_password.html', {'admin_user': admin_user})
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'admin_change_password.html', {'admin_user': admin_user})
            
            # Update password
            admin_user.set_password(new_password)
            admin_user.must_change_password = False
            admin_user.password_changed_date = timezone.now()
            admin_user.save()
            
            # Clear temp session and create full session
            request.session.pop('temp_admin_id', None)
            request.session['admin_user_id'] = str(admin_user.id)
            request.session['admin_username'] = admin_user.username
            request.session['admin_role'] = admin_user.role
            request.session['admin_full_name'] = admin_user.full_name
            
            messages.success(request, 'Password changed successfully! You can now access the system.')
            logger.info(f"Password changed for admin: {admin_user.username}")
            
            # Log password change to AdminActionHistory
            from cenro.admin_utils import log_admin_action
            log_admin_action(admin_user, None, 'password_change', 'Password changed by user', request)
            
            # Redirect based on role
            if admin_user.role == 'super_admin':
                return redirect('cenro:dashboard')
            elif admin_user.role == 'operations_manager':
                return redirect('cenro:dashboard')
            elif admin_user.role == 'content_rewards_manager':
                return redirect('cenro:dashboard')
            elif admin_user.role == 'security_analyst':
                return redirect('cenro:security_dashboard')
            else:
                return redirect('cenro:dashboard')
        
        return render(request, 'admin_change_password.html', {'admin_user': admin_user})
    
    except AdminUser.DoesNotExist:
        messages.error(request, 'Admin account not found.')
        return redirect('cenro:admin_login')

def admin_logout(request):
    """Admin logout view - Production Ready
    
    Safely logs out admin without affecting user session.
    This ensures simultaneous user and admin logins work correctly.
    """
    admin_username = request.session.get('admin_username', 'Unknown')
    admin_user_id = request.session.get('admin_user_id')
    
    # Check if user is logged in to preserve session
    has_user_session = request.user.is_authenticated
    
    # Log logout action to AdminActionHistory if we have admin info
    if admin_user_id:
        try:
            admin_user = AdminUser.objects.get(id=admin_user_id)
            from cenro.admin_utils import log_admin_action
            log_admin_action(admin_user, None, 'logout', 'Admin logged out', request)
            logger.info(f"Admin '{admin_username}' logged out")
        except AdminUser.DoesNotExist:
            logger.warning(f"Admin logout attempted but admin user not found: {admin_username}")
    
    # Clear ONLY admin session keys (preserve user authentication)
    request.session.pop('admin_user_id', None)
    request.session.pop('admin_username', None)
    request.session.pop('admin_role', None)
    request.session.pop('admin_full_name', None)
    request.session.pop('temp_admin_id', None)  # Also clear any temp admin session
    
    # Save session to persist the changes
    request.session.save()
    
    # Log preservation of user session if exists
    if has_user_session:
        logger.info(f"Admin '{admin_username}' logged out (user session preserved)")
    
    # Clear any existing messages before adding logout message
    storage = messages.get_messages(request)
    storage.used = True
    
    messages.success(request, 'You have been logged out successfully.')
    
    # Redirect to admin login
    return redirect('cenro:admin_login')

@csrf_protect
@admin_required
def admin_management(request):
    """Admin management view for Super Admins to manage other admin accounts"""
    # Check if user has super_admin role
    if request.admin_user.role != 'super_admin':
        messages.error(request, 'Access denied. Only super admins can access admin management.')
        return redirect('cenro:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Handle admin creation
        if action == 'create':
            return admin_create(request)
        
        admin_id = request.POST.get('admin_id')
        
        try:
            target_admin = AdminUser.objects.get(id=admin_id)
            
            if action == 'suspend':
                # Prevent admin from suspending themselves
                if target_admin.id == request.admin_user.id:
                    messages.error(request, 'You cannot suspend your own account.')
                    return redirect('cenro:admin_management')
                
                suspension_reason = request.POST.get('suspension_reason', 'No reason provided')
                target_admin.suspend_admin(request.admin_user, suspension_reason)
                
                # Send suspension notification email
                from cenro.admin_email_service import send_suspension_email
                send_suspension_email(target_admin, request.admin_user, suspension_reason)
                
                # Create admin suspended notification
                from cenro.models import AdminNotification
                AdminNotification.create_admin_suspended_notification(target_admin, request.admin_user, suspension_reason)
                
                messages.success(request, f'Admin account "{target_admin.username}" has been suspended.')
                
                # Log the suspension
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'suspend_admin', f'Reason: {suspension_reason}', request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin suspended: {target_admin.username} by {request.admin_user.username} - Reason: {suspension_reason}\n")
                
                return redirect('cenro:admin_management')
            
            elif action == 'reactivate':
                target_admin.status = 'approved'
                target_admin.approved_by = request.admin_user
                target_admin.approval_date = timezone.now()
                target_admin.rejection_reason = None
                target_admin.is_active = True  # Ensure account is active
                target_admin.save()
                
                # Send reactivation notification email
                from cenro.admin_email_service import send_reactivation_email
                send_reactivation_email(target_admin, request.admin_user)
                
                messages.success(request, f'Admin account "{target_admin.username}" has been reactivated.')
                
                # Log the reactivation
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'reactivate_admin', 'Admin account reactivated', request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin reactivated: {target_admin.username} by {request.admin_user.username}\n")
                
                return redirect('cenro:admin_management')
            
            elif action == 'unsuspend':
                target_admin.status = 'approved'
                target_admin.approved_by = request.admin_user
                target_admin.approval_date = timezone.now()
                target_admin.rejection_reason = None  # Clear suspension reason
                target_admin.is_active = True
                target_admin.save()
                
                # Send reactivation notification email (same as reactivate)
                from cenro.admin_email_service import send_reactivation_email
                send_reactivation_email(target_admin, request.admin_user)
                
                # Create admin reactivated notification
                from cenro.models import AdminNotification
                AdminNotification.create_admin_reactivated_notification(target_admin, request.admin_user)
                
                messages.success(request, f'Admin account "{target_admin.username}" has been unsuspended.')
                
                # Log the unsuspension
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'unsuspend_admin', 'Admin account unsuspended', request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin unsuspended: {target_admin.username} by {request.admin_user.username}\n")
                
                return redirect('cenro:admin_management')
            
            elif action == 'unlock':
                target_admin.unlock_account()  # This resets both failed attempts and lock time
                
                # Send unlock notification email
                from cenro.admin_email_service import send_unlock_notification_email
                send_unlock_notification_email(target_admin, request.admin_user)
                
                messages.success(request, f'Admin account "{target_admin.username}" has been unlocked.')
                
                # Log the unlock
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'unlock_admin', 'Admin account unlocked', request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin account unlocked: {target_admin.username} by {request.admin_user.username}\n")
                
                return redirect('cenro:admin_management')
            
            elif action == 'edit_barangays':
                # Edit barangay assignments for Operations Managers
                if target_admin.role != 'operations_manager':
                    messages.error(request, 'Barangay assignments can only be edited for Operations Managers.')
                    return redirect('cenro:admin_management')
                
                selected_barangays = request.POST.getlist('barangays')
                
                # Update barangay assignments
                from accounts.models import Barangay
                if selected_barangays:
                    barangays_to_assign = Barangay.objects.filter(id__in=selected_barangays)
                    target_admin.assigned_barangays.set(barangays_to_assign)
                    barangay_names = ', '.join([b.name for b in barangays_to_assign])
                    messages.success(request, f'Updated barangay assignments for "{target_admin.username}": {barangay_names}')
                    barangay_info = barangay_names
                else:
                    target_admin.assigned_barangays.clear()
                    messages.success(request, f'"{target_admin.username}" now has access to all barangays.')
                    barangay_info = "All barangays"
                
                # Create barangay assignment change notification
                from cenro.models import AdminNotification
                AdminNotification.create_barangay_assignment_notification(
                    affected_admin=target_admin,
                    changed_by=request.admin_user,
                    barangay_info=barangay_info
                )
                
                # Log the change
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'edit_barangays', f'Barangay assignments updated: {barangay_info}', request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Barangay assignments updated for {target_admin.username} by {request.admin_user.username}: {barangay_info}\n")
            
            elif action == 'reset_password':
                # Generate secure temporary password
                from cenro.admin_utils import generate_secure_password, log_admin_action
                from cenro.admin_email_service import send_password_reset_email
                
                temp_password = generate_secure_password(length=12, include_symbols=True)
                
                # Reset the admin's password
                target_admin.set_password(temp_password)
                target_admin.must_change_password = True
                target_admin.password_changed_date = timezone.now()
                target_admin.failed_login_attempts = 0
                target_admin.account_locked_until = None
                target_admin.save()
                
                # Create admin unlocked notification if account was locked
                if target_admin.account_locked_until:
                    from cenro.models import AdminNotification
                    AdminNotification.create_admin_unlocked_notification(target_admin, request.admin_user)
                
                # Get reset reason
                reset_reason = request.POST.get('reset_reason', '').strip()
                log_details = f"Reason: {reset_reason}" if reset_reason else "No reason provided"
                
                # Send password reset email to the admin
                email_sent = send_password_reset_email(
                    admin_user=target_admin,
                    temporary_password=temp_password,
                    reset_by_admin=request.admin_user,
                    reset_reason=reset_reason if reset_reason else None
                )
                
                if email_sent:
                    log_details += f" | Email sent to {target_admin.email}"
                else:
                    log_details += f" | Email failed to send to {target_admin.email}"
                
                # Log to security.log
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Password reset for {target_admin.username} by {request.admin_user.username}. {log_details}\n")
                
                # Log using utility function (creates database record)
                log_admin_action(request.admin_user, target_admin, 'password_reset', log_details, request)
                
                # If this is an AJAX request, return JSON response
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Password successfully reset for {target_admin.username}. {"Temporary password sent to their email." if email_sent else "Failed to send email - please share the password manually."}',
                        'temporary_password': temp_password,
                        'email_sent': email_sent
                    })
                else:
                    messages.success(request, f'Password reset for {target_admin.username}. Temporary password: {temp_password}')
            
            elif action == 'edit_admin':
                # Prevent admin from editing themselves (except for updating their own email/name in profile)
                if target_admin.id == request.admin_user.id:
                    messages.error(request, 'You cannot edit your own account through this interface.')
                    return redirect('cenro:admin_management')
                
                # Get form data
                full_name = request.POST.get('full_name', '').strip()
                email = request.POST.get('email', '').strip()
                role = request.POST.get('role', '').strip()
                
                # Validate inputs
                if not full_name or not email or not role:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'All fields are required.'}, status=400)
                    messages.error(request, 'All fields are required.')
                    return redirect('cenro:admin_management')
                
                # Validate email uniqueness (excluding current admin)
                if AdminUser.objects.filter(email__iexact=email).exclude(id=target_admin.id).exists():
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'This email address is already in use by another admin account.'}, status=400)
                    messages.error(request, 'This email address is already in use by another admin account.')
                    return redirect('cenro:admin_management')
                
                # Store old values for logging
                old_values = {
                    'full_name': target_admin.full_name,
                    'email': target_admin.email,
                    'role': target_admin.role
                }
                
                # Update admin details
                target_admin.full_name = full_name
                target_admin.email = email
                
                # Only allow role change if not super_admin
                if target_admin.role != 'super_admin':
                    old_role = target_admin.role
                    target_admin.role = role
                    # Clear barangay assignments if changing from operations_manager to another role
                    if old_role == 'operations_manager' and role != 'operations_manager':
                        target_admin.assigned_barangays.clear()
                
                target_admin.save()
                
                # Create change log
                changes = []
                if old_values['full_name'] != full_name:
                    changes.append(f"Name: {old_values['full_name']} → {full_name}")
                if old_values['email'] != email:
                    changes.append(f"Email: {old_values['email']} → {email}")
                if old_values['role'] != target_admin.role:
                    changes.append(f"Role: {old_values['role']} → {target_admin.role}")
                
                change_details = '; '.join(changes) if changes else 'No changes'
                
                # Log the edit action
                from cenro.admin_utils import log_admin_action
                log_admin_action(request.admin_user, target_admin, 'edit_admin', change_details, request)
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin edited: {target_admin.username} by {request.admin_user.username} - Changes: {change_details}\n")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Admin account "{target_admin.username}" has been updated successfully.',
                        'changes': change_details
                    })
                
                messages.success(request, f'Admin account "{target_admin.username}" has been updated successfully.')
                return redirect('cenro:admin_management')
            
            elif action == 'delete_admin':
                # Prevent admin from deleting themselves
                if target_admin.id == request.admin_user.id:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'You cannot delete your own account.'}, status=400)
                    messages.error(request, 'You cannot delete your own account.')
                    return redirect('cenro:admin_management')
                
                # Prevent deletion of super_admin by other super_admins (optional safety measure)
                if target_admin.role == 'super_admin':
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'error': 'Super admin accounts cannot be deleted through this interface for security reasons.'}, status=403)
                    messages.error(request, 'Super admin accounts cannot be deleted through this interface for security reasons.')
                    return redirect('cenro:admin_management')
                
                deletion_reason = request.POST.get('deletion_reason', 'No reason provided')
                
                # Store admin details before deletion
                deleted_username = target_admin.username
                deleted_email = target_admin.email
                deleted_role = target_admin.get_role_display()
                
                # Log the deletion BEFORE actually deleting
                from cenro.admin_utils import log_admin_action
                log_admin_action(
                    request.admin_user, 
                    target_admin, 
                    'delete_admin', 
                    f'Deleted: {deleted_username} ({deleted_role}) - Email: {deleted_email} - Reason: {deletion_reason}', 
                    request
                )
                
                with open('security.log', 'a') as log_file:
                    log_file.write(f"[{timezone.now()}] Admin deleted: {deleted_username} ({deleted_role}) by {request.admin_user.username} - Reason: {deletion_reason}\n")
                
                # Perform soft delete (deactivate) instead of hard delete to maintain referential integrity
                target_admin.is_active = False
                target_admin.status = 'deleted'
                target_admin.rejection_reason = f'Deleted by {request.admin_user.username}: {deletion_reason}'
                target_admin.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Admin account "{deleted_username}" has been deleted successfully.'
                    })
                
                messages.success(request, f'Admin account "{deleted_username}" has been deleted successfully.')
                return redirect('cenro:admin_management')
            
            return redirect('cenro:admin_management')
            
        except AdminUser.DoesNotExist:
            messages.error(request, 'Admin account not found.')
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    
    # GET request - show admin management page
    # Get all admin accounts grouped by status
    approved_admins = AdminUser.objects.filter(status='approved').order_by('-created_at')
    suspended_admins = AdminUser.objects.filter(status='suspended').order_by('-created_at')
    locked_admins = AdminUser.objects.filter(account_locked_until__isnull=False).order_by('-created_at')
    
    # Get barangays for the creation form
    from accounts.models import Barangay
    barangays = Barangay.objects.all().order_by('name')
    
    # Get admin action history
    admin_history_queryset = AdminActionHistory.objects.select_related('admin_user', 'target_admin').all()
    
    # Debug: Print count
    print(f"DEBUG: Total AdminActionHistory records: {admin_history_queryset.count()}")
    
    # Apply filters if provided
    action_filter = request.GET.get('action_filter')
    admin_filter = request.GET.get('admin_filter')
    limit = int(request.GET.get('limit', 50))
    
    if action_filter:
        admin_history_queryset = admin_history_queryset.filter(action=action_filter)
    
    if admin_filter:
        admin_history_queryset = admin_history_queryset.filter(admin_user__username=admin_filter)
    
    # Limit results
    admin_history_queryset = admin_history_queryset[:limit]
    
    # Paginate history
    page = request.GET.get('page', 1)
    paginator = Paginator(admin_history_queryset, 20)  # 20 records per page
    admin_history = paginator.get_page(page)
    
    # Debug: Print history data being passed
    print(f"DEBUG: admin_history count: {len(admin_history)}")
    print(f"DEBUG: admin_history object_list: {list(admin_history.object_list)}")
    
    # Get all admins for filter dropdown
    all_admins = AdminUser.objects.filter(is_active=True).order_by('full_name')
    
    context = {
        'admin_user': request.admin_user,
        'approved_admins': approved_admins,
        'suspended_admins': suspended_admins,
        'locked_admins': locked_admins,
        'barangays': barangays,
        'total_admins': AdminUser.objects.count(),
        'approved_count': approved_admins.count(),
        'suspended_count': suspended_admins.count(),
        'locked_count': locked_admins.count(),
        'admin_history': admin_history,
        'all_admins': all_admins,
    }
    
    return render(request, 'admin_management.html', context)

@admin_required
def security_dashboard(request):
    """
    Comprehensive Security Dashboard for Security Analysts
    Provides overview of security logs, user activity, redemptions, and reports
    """
    from datetime import timedelta
    from django.db.models import Count, Sum, Q
    from accounts.models import (
        LoginAttempt, Users, PointsTransaction, Redemption
    )
    import time
    
    # Get time periods
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # === KEY METRICS ===
    total_users = Users.objects.filter(is_active=True).count()
    new_users_today = Users.objects.filter(created_at__gte=today_start).count()
    
    # Login attempts
    login_attempts_24h = LoginAttempt.objects.filter(timestamp__gte=last_24h).count()
    failed_logins_24h = LoginAttempt.objects.filter(
        timestamp__gte=last_24h, success=False
    ).count()
    failed_login_rate = round(
        (failed_logins_24h / max(login_attempts_24h, 1)) * 100, 1
    )
    
    # Redemptions
    redemptions_today = Redemption.objects.filter(
        redemption_date__gte=today_start
    ).count()
    pending_redemptions = Redemption.objects.filter(claim_date__isnull=True).count()
    
    # Admin actions
    admin_actions_today = AdminActionHistory.objects.filter(
        timestamp__gte=today_start
    ).count()
    
    # === SECURITY LOGS TAB ===
    # Recent login attempts (last 50)
    login_attempts = LoginAttempt.objects.select_related().order_by('-timestamp')[:50]
    
    # Recent admin actions (last 30)
    admin_actions = AdminActionHistory.objects.select_related(
        'admin_user', 'target_admin'
    ).order_by('-timestamp')[:30]
    
    # === USER ACTIVITY TAB ===
    # Recent user registrations (last 20)
    recent_users = Users.objects.select_related('family').filter(
        is_active=True
    ).order_by('-created_at')[:20]
    
    # Recent points transactions (last 30)
    recent_transactions = PointsTransaction.objects.select_related(
        'user'
    ).order_by('-transaction_date')[:30]
    
    # === REDEMPTIONS TAB ===
    # Recent redemptions (last 30)
    redemptions = Redemption.objects.select_related(
        'user', 'reward', 'approved_by'
    ).order_by('-redemption_date')[:30]
    
    # Redemption statistics
    total_redemptions = Redemption.objects.count()
    total_points_redeemed = Redemption.objects.aggregate(
        total=Sum('points_used')
    )['total'] or 0
    
    # Most popular reward
    most_popular = Redemption.objects.values('reward__name').annotate(
        count=Count('id')
    ).order_by('-count').first()
    most_popular_reward = most_popular['reward__name'] if most_popular else '-'
    
    # === REPORTS TAB ===
    # Additional statistics for reports
    failed_logins_week = LoginAttempt.objects.filter(
        timestamp__gte=last_7d, success=False
    ).count()
    redemptions_month = Redemption.objects.filter(
        redemption_date__gte=last_30d
    ).count()
    admin_actions_week = AdminActionHistory.objects.filter(
        timestamp__gte=last_7d
    ).count()
    
    # Default date range for reports
    start_date = (now - timedelta(days=7)).strftime('%Y-%m-%d')
    end_date = now.strftime('%Y-%m-%d')
    
    # === SECURITY ALERTS ===
    security_alerts = []
    
    # High failure rate alert
    if failed_login_rate > 30:
        security_alerts.append({
            'severity': 'danger',
            'title': 'Critical',
            'message': f'Login failure rate is {failed_login_rate}% in the last 24 hours'
        })
    elif failed_login_rate > 15:
        security_alerts.append({
            'severity': 'warning',
            'title': 'Warning',
            'message': f'Elevated login failure rate: {failed_login_rate}%'
        })
    
    # Suspicious IP activity
    suspicious_ips = LoginAttempt.objects.filter(
        timestamp__gte=last_24h, success=False
    ).values('ip_address').annotate(
        failures=Count('id')
    ).filter(failures__gte=5).count()
    
    if suspicious_ips > 0:
        security_alerts.append({
            'severity': 'warning',
            'title': 'Suspicious Activity',
            'message': f'{suspicious_ips} IP address(es) with 5+ failed login attempts'
        })
    
    # Compile context
    context = {
        'admin_user': request.admin_user,
        'timestamp': int(time.time()),
        
        # Key Metrics
        'total_users': total_users,
        'new_users_today': new_users_today,
        'login_attempts_24h': login_attempts_24h,
        'failed_login_rate': failed_login_rate,
        'redemptions_today': redemptions_today,
        'pending_redemptions': pending_redemptions,
        'admin_actions_today': admin_actions_today,
        
        # Security Logs Tab
        'login_attempts': login_attempts,
        'admin_actions': admin_actions,
        
        # User Activity Tab
        'recent_users': recent_users,
        'recent_transactions': recent_transactions,
        
        # Redemptions Tab
        'redemptions': redemptions,
        'total_redemptions': total_redemptions,
        'total_points_redeemed': total_points_redeemed,
        'most_popular_reward': most_popular_reward,
        
        # Reports Tab
        'failed_logins_week': failed_logins_week,
        'redemptions_month': redemptions_month,
        'admin_actions_week': admin_actions_week,
        'start_date': start_date,
        'end_date': end_date,
        
        # Alerts
        'security_alerts': security_alerts,
    }
    
    # Render Security Analyst Dashboard
    return render(request, 'sec_analyst_dashboard.html', context)

@admin_required 
def get_admin_barangays(request, admin_id):
    """Get assigned barangays for an admin (AJAX endpoint)"""
    try:
        admin_user = AdminUser.objects.get(id=admin_id)
        assigned_barangays = list(admin_user.assigned_barangays.values_list('id', flat=True))
        assigned_barangays = [str(barangay_id) for barangay_id in assigned_barangays]  # Convert to strings
        
        return JsonResponse({
            'assigned_barangays': assigned_barangays,
            'admin_username': admin_user.username,
        })
        
    except AdminUser.DoesNotExist:
        return JsonResponse({'error': 'Admin not found'}, status=404)
    except Exception as e:
        logger.error(f"Error getting admin barangays: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@csrf_protect
@admin_required
def check_admin_email_availability(request):
    """Check if an email is available for admin registration (AJAX endpoint)"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'available': False,
                'message': 'Email address is required'
            }, status=400)
        
        # Check if email already exists
        email_exists = AdminUser.objects.filter(email__iexact=email).exists()
        
        if email_exists:
            return JsonResponse({
                'available': False,
                'message': 'This email address is already registered to another admin account'
            })
        else:
            return JsonResponse({
                'available': True,
                'message': 'Email address is available'
            })
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_protect
def bootstrap_superadmin(request):
    """
    Bootstrap view to create the FIRST superadmin when no admins exist.
    This is the EASIEST way - just visit /cenro/admin/bootstrap/ in your browser!
    
    Security: This view only works if NO admin users exist in the database.
    Once an admin is created, this view is permanently disabled.
    """
    # Check if any admin already exists
    if AdminUser.objects.exists():
        messages.error(request, 'Bootstrap mode is disabled - admin accounts already exist. Please login normally.')
        return redirect('cenro:admin_login')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        if not email or '@' not in email:
            errors.append('Valid email is required')
        if not full_name:
            errors.append('Full name is required')
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'bootstrap_superadmin.html', {
                'username': username,
                'email': email,
                'full_name': full_name
            })
        
        try:
            with transaction.atomic():
                # Create the first superadmin
                admin = AdminUser.objects.create(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role='super_admin',
                    status='approved',
                    is_active=True,
                    # All permissions enabled
                    can_manage_users=True,
                    can_manage_points=True,
                    can_manage_rewards=True,
                    can_manage_schedules=True,
                    can_manage_learning=True,
                    can_manage_games=True,
                    can_manage_security=True,
                    can_manage_controls=True,
                )
                admin.set_password(password)
                admin.save()
                
                # Assign all barangays
                all_barangays = Barangay.objects.all()
                if all_barangays.exists():
                    admin.barangays.set(all_barangays)
                
                logger.info(f"Bootstrap superadmin created: {username}")
                
                messages.success(request, f'✅ Superadmin "{username}" created successfully! You can now login.')
                return redirect('cenro:admin_login')
                
        except Exception as e:
            logger.error(f"Bootstrap superadmin creation error: {str(e)}")
            messages.error(request, f'Error creating superadmin: {str(e)}')
    
    # GET request - show form
    return render(request, 'bootstrap_superadmin.html')
