"""
Schedule Notification Service for E-KOLEK System
Handles sending email notifications to users when schedules are updated
"""
import logging
import threading
from django.conf import settings

logger = logging.getLogger(__name__)

# Check if Celery is available
try:
    from accounts.tasks import send_bulk_schedule_notifications
    CELERY_AVAILABLE = True
    logger.info("✅ Celery available for schedule notifications")
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("⚠️ Celery not available - notifications will be sent synchronously")


def check_celery_worker_running():
    """Check if Celery worker is actually running"""
    if not CELERY_AVAILABLE:
        return False
    
    try:
        from eko.celery import app
        inspect = app.control.inspect()
        stats = inspect.stats()
        if stats:
            return True
    except Exception as e:
        logger.debug(f"Celery worker check failed: {str(e)}")
    
    return False


def get_users_with_email_by_barangay(barangay):
    """
    Get all approved users with email addresses from a specific barangay
    
    Args:
        barangay: Barangay model instance
    
    Returns:
        QuerySet of Users with email addresses
    """
    from accounts.models import Users
    
    # Get all approved users from the barangay who have email addresses
    users = Users.objects.filter(
        family__barangay=barangay,
        status='approved',
        is_active=True,
        email__isnull=False
    ).exclude(email='').select_related('family')
    
    return users


def send_emails_in_background(user_emails, schedule_data, action):
    """
    Send emails in a background thread so it doesn't block the schedule save
    This allows the schedule to be saved immediately while emails send in the background
    """
    success_count = 0
    failed_emails = []
    
    logger.info(f"Background email sending started for {len(user_emails)} users")
    
    # Generate email content with beautiful HTML design
    subject = f"E-KOLEK: Garbage Collection Schedule {action.title()}"
    
    # Prepare data
    waste_types_str = ', '.join(schedule_data['waste_types']) if schedule_data['waste_types'] else 'All types'
    
    # Create plain text message (fallback)
    if action == 'deleted':
        message = f"""
Hello,

The garbage collection schedule for Barangay {schedule_data['barangay_name']} on {schedule_data['day']} has been REMOVED.

Please check the E-KOLEK app for updated collection schedules.

Best regards,
E-KOLEK Team
        """
    else:
        action_text = 'has been added' if action == 'added' else 'has been updated'
        
        message = f"""
Hello,

The garbage collection schedule for Barangay {schedule_data['barangay_name']} {action_text}:

Day: {schedule_data['day']}
Time: {schedule_data['start_time']} - {schedule_data['end_time']}
Waste Types: {waste_types_str}
{f"Notes: {schedule_data['notes']}" if schedule_data['notes'] else ''}

Please prepare your segregated waste accordingly.

Best regards,
E-KOLEK Team
        """
    
    # Create beautiful HTML email
    if action == 'deleted':
        # Design for deleted schedule
        html_message = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Schedule Removed</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f3f4f6;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 40px 20px;">
                        <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header with Gradient -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 40px 30px; text-align: center;">
                                    <table role="presentation" style="margin: 0 auto 20px;">
                                        <tr>
                                            <td style="background-color: rgba(255, 255, 255, 0.2); width: 80px; height: 80px; border-radius: 50%; text-align: center; vertical-align: middle; line-height: 80px;">
                                                <span style="font-size: 48px; display: inline-block; vertical-align: middle; line-height: normal;">🗑️</span>
                                            </td>
                                        </tr>
                                    </table>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">E-KOLEK</h1>
                                    <p style="color: rgba(255, 255, 255, 0.95); margin: 10px 0 0 0; font-size: 16px;">Environmental Management System</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-left: 4px solid #ef4444; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                                        <h2 style="color: #dc2626; margin: 0 0 10px 0; font-size: 22px; font-weight: 600;">⚠️ Schedule Removed</h2>
                                        <p style="color: #333333; margin: 0; font-size: 16px; line-height: 1.6;">
                                            The garbage collection schedule for <strong>Barangay {schedule_data['barangay_name']}</strong> on <strong>{schedule_data['day']}</strong> has been removed from the system.
                                        </p>
                                    </div>
                                    
                                    <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                                        <p style="color: #666666; margin: 0; font-size: 15px; line-height: 1.6;">
                                            📱 Please check the <strong>E-KOLEK mobile app</strong> for the latest garbage collection schedules in your barangay.
                                        </p>
                                    </div>
                                    
                                    <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 20px 0;">
                                        Stay updated with your waste collection schedule to ensure proper waste management in your community.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                    <p style="color: #333333; margin: 0 0 5px 0; font-size: 14px; font-weight: 600;">Best regards,</p>
                                    <p style="color: #6366f1; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">E-KOLEK Team</p>
                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;">© 2025 E-KOLEK. Environmental Management System</p>
                                    <p style="color: #9ca3af; margin: 5px 0 0 0; font-size: 12px;">Promoting Clean and Green Communities</p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    else:
        # Design for added/updated schedule
        action_color = '#10b981' if action == 'added' else '#3b82f6'
        action_emoji = '🆕' if action == 'added' else '🔄'
        action_title = 'New Schedule Added' if action == 'added' else 'Schedule Updated'
        
        # Build waste types HTML with icons
        waste_type_icons = {
            'Biodegradable': '🌿',
            'Non-Biodegradable': '🚫',
            'Recyclable': '♻️',
            'Paper': '📄',
            'Plastic': '🥤',
            'Glass': '🍾',
            'Metal': '🔩',
            'Tin Can': '🥫',
            'Special Waste': '⚠️'
        }
        
        waste_types_html = ''
        for waste_type in schedule_data['waste_types']:
            icon = waste_type_icons.get(waste_type, '📦')
            waste_types_html += f'<span style="display: inline-block; background-color: #f3f4f6; padding: 8px 15px; border-radius: 20px; margin: 5px; font-size: 14px; color: #374151;">{icon} {waste_type}</span>'
        
        if not waste_types_html:
            waste_types_html = '<span style="display: inline-block; background-color: #f3f4f6; padding: 8px 15px; border-radius: 20px; margin: 5px; font-size: 14px; color: #374151;">📦 All waste types</span>'
        
        html_message = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Garbage Collection Schedule</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f3f4f6;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 40px 20px;">
                        <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                            
                            <!-- Header with Gradient -->
                            <tr>
                                <td style="background: linear-gradient(135deg, {action_color} 0%, {action_color}dd 100%); padding: 40px 30px; text-align: center;">
                                    <table role="presentation" style="margin: 0 auto 20px;">
                                        <tr>
                                            <td style="background-color: rgba(255, 255, 255, 0.2); width: 80px; height: 80px; border-radius: 50%; text-align: center; vertical-align: middle; line-height: 80px;">
                                                <span style="font-size: 48px; display: inline-block; vertical-align: middle; line-height: normal;">{action_emoji}</span>
                                            </td>
                                        </tr>
                                    </table>
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">E-KOLEK</h1>
                                    <p style="color: rgba(255, 255, 255, 0.95); margin: 10px 0 0 0; font-size: 16px;">Garbage Collection Schedule</p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <!-- Action Banner -->
                                    <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border-left: 4px solid {action_color}; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center;">
                                        <h2 style="color: {action_color}; margin: 0; font-size: 22px; font-weight: 600;">{action_title}</h2>
                                    </div>
                                    
                                    <!-- Barangay Info -->
                                    <div style="text-align: center; margin-bottom: 30px;">
                                        <p style="color: #6b7280; margin: 0 0 5px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">📍 BARANGAY</p>
                                        <h3 style="color: #1f2937; margin: 0; font-size: 24px; font-weight: 700;">{schedule_data['barangay_name']}</h3>
                                    </div>
                                    
                                    <!-- Schedule Details Card -->
                                    <div style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 2px solid {action_color};">
                                        
                                        <!-- Day -->
                                        <div style="margin-bottom: 20px;">
                                            <table role="presentation" style="width: 100%;">
                                                <tr>
                                                    <td style="width: 30%; vertical-align: top;">
                                                        <span style="color: #6b7280; font-size: 14px; font-weight: 600;">📅 DAY</span>
                                                    </td>
                                                    <td style="vertical-align: top;">
                                                        <span style="color: #1f2937; font-size: 18px; font-weight: 700;">{schedule_data['day']}</span>
                                                    </td>
                                                </tr>
                                            </table>
                                        </div>
                                        
                                        <!-- Time -->
                                        <div style="margin-bottom: 20px;">
                                            <table role="presentation" style="width: 100%;">
                                                <tr>
                                                    <td style="width: 30%; vertical-align: top;">
                                                        <span style="color: #6b7280; font-size: 14px; font-weight: 600;">⏰ TIME</span>
                                                    </td>
                                                    <td style="vertical-align: top;">
                                                        <span style="color: #1f2937; font-size: 18px; font-weight: 700;">{schedule_data['start_time']} - {schedule_data['end_time']}</span>
                                                    </td>
                                                </tr>
                                            </table>
                                        </div>
                                        
                                        <!-- Waste Types -->
                                        <div style="margin-bottom: {'20px' if schedule_data['notes'] else '0'};">
                                            <p style="color: #6b7280; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">♻️ WASTE TYPES</p>
                                            <div style="margin: 10px 0;">
                                                {waste_types_html}
                                            </div>
                                        </div>
                                        
                                        <!-- Notes (if any) -->
                                        {f'''<div style="background-color: #fef3c7; border-left: 3px solid #f59e0b; padding: 15px; border-radius: 6px;">
                                            <p style="color: #92400e; margin: 0; font-size: 14px;"><strong>📝 Note:</strong> {schedule_data['notes']}</p>
                                        </div>''' if schedule_data['notes'] else ''}
                                        
                                    </div>
                                    
                                    <!-- Call to Action -->
                                    <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 25px;">
                                        <p style="color: #1e40af; margin: 0; font-size: 16px; font-weight: 600; line-height: 1.6;">
                                            🌱 Please prepare your segregated waste accordingly
                                        </p>
                                    </div>
                                    
                                    <!-- Reminder -->
                                    <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px;">
                                        <p style="color: #6b7280; margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">💡 Reminder:</p>
                                        <ul style="color: #6b7280; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                            <li>Segregate your waste properly</li>
                                            <li>Place waste in appropriate containers</li>
                                            <li>Be ready before collection time</li>
                                            <li>Keep your area clean</li>
                                        </ul>
                                    </div>
                                    
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                    <p style="color: #333333; margin: 0 0 5px 0; font-size: 14px; font-weight: 600;">Best regards,</p>
                                    <p style="color: #6366f1; margin: 0 0 15px 0; font-size: 16px; font-weight: 700;">E-KOLEK Team</p>
                                    <p style="color: #9ca3af; margin: 0; font-size: 12px;">© 2025 E-KOLEK. Environmental Management System</p>
                                    <p style="color: #9ca3af; margin: 5px 0 0 0; font-size: 12px;">Promoting Clean and Green Communities 🌍</p>
                                </td>
                            </tr>
                            
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    
    from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
    
    # Send to all users
    for i, email in enumerate(user_emails, 1):
        if not email:
            continue
        
        try:
            from django.core.mail import send_mail
            
            # Send email using Django's send_mail (will use Resend backend)
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            success_count += 1
            logger.info(f"Background email sent to {email}")
            
        except Exception as e:
            logger.error(f"Failed to send background email to {email}: {str(e)}")
            failed_emails.append(email)
    
    logger.info(f"Background email sending completed | Success: {success_count}/{len(user_emails)}")


def send_schedule_notification(schedule, action='added'):
    """
    Send email notifications to all users in the affected barangay
    
    Args:
        schedule: GarbageSchedule model instance
        action: 'added', 'updated', or 'deleted'
    
    Returns:
        dict: Result with success status and details
    """
    try:
        logger.info(f"=== SCHEDULE NOTIFICATION SERVICE ===")
        logger.info(f"Action: {action} | Barangay: {schedule.barangay.name} | Day: {schedule.day} | Time: {schedule.start_time} - {schedule.end_time}")
        
        # Get all users with email from this barangay
        users = get_users_with_email_by_barangay(schedule.barangay)
        user_emails = list(users.values_list('email', flat=True))
        
        logger.info(f"Found {len(user_emails)} users with email addresses")
        
        if not user_emails:
            warning_msg = f"No users with email addresses found for {schedule.barangay.name}"
            logger.warning(warning_msg)
            return {
                'success': True,
                'message': 'No users with email to notify',
                'recipients_count': 0,
                'warning': 'No users with email addresses in this barangay'
            }
        
        # Prepare schedule data - handle both time objects and strings
        def format_time(time_value):
            """Format time value whether it's a time object or string"""
            if not time_value:
                return ''
            if isinstance(time_value, str):
                # Already a string, return as-is
                return time_value
            # It's a time object, format it
            try:
                return time_value.strftime('%I:%M %p')
            except:
                return str(time_value)
        
        schedule_data = {
            'barangay_name': schedule.barangay.name,
            'day': schedule.day,
            'start_time': format_time(schedule.start_time),
            'end_time': format_time(schedule.end_time),
            'waste_types': schedule.waste_types if schedule.waste_types else [],
            'notes': schedule.notes if schedule.notes else ''
        }
        
        # ALWAYS use direct email sending for reliability
        # Send emails in BACKGROUND THREAD so schedule save is not blocked
        print(f"\nEmail Method:")
        print(f"  - Using: Background Thread (Asynchronous - Non-Blocking)")
        
        print(f"\nStarting background email thread...")
        print(f"  - Schedule will be saved IMMEDIATELY")
        print(f"  - Emails will send in the background")
        logger.info("Starting background email thread")
        
        # Start background thread for email sending
        email_thread = threading.Thread(
            target=send_emails_in_background,
            args=(user_emails, schedule_data, action),
            daemon=True  # Thread will not prevent program exit
        )
        email_thread.start()
        
        print(f"\n{'='*70}")
        print(f"SCHEDULE SAVED!")
        print(f"  - Schedule has been saved to database")
        print(f"  - {len(user_emails)} emails are being sent in background")
        print(f"  - You can continue working immediately")
        print(f"{'='*70}\n")
        
        logger.info(f"Email thread started | {len(user_emails)} emails queued for background sending")

        
        return {
            'success': True,
            'message': f'Schedule saved! Notifications are being sent to {len(user_emails)} users in the background',
            'recipients_count': len(user_emails),
            'async': True,
            'background_thread': True
        }
    
    except Exception as e:
        error_msg = f"Schedule notification service error: {str(e)}"
        print(f"\nERROR: {error_msg}")
        logger.error(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'error': str(e),
            'message': 'Failed to send notifications'
        }


def send_schedule_added_notification(schedule):
    """Send notification when a new schedule is added"""
    return send_schedule_notification(schedule, action='added')


def send_schedule_updated_notification(schedule):
    """Send notification when a schedule is updated"""
    return send_schedule_notification(schedule, action='updated')


def send_schedule_deleted_notification(schedule):
    """Send notification when a schedule is deleted"""
    return send_schedule_notification(schedule, action='deleted')
