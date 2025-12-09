from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    name='accounts.send_otp_email',
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    autoretry_for=(Exception,),
    retry_backoff=True,  # Exponential backoff: 60s, 120s, 240s
    retry_jitter=True,  # Add randomness to avoid thundering herd
)
def send_otp_email_task(self, email, subject, message, html_message):
    """
    Production-ready Celery task for sending OTP emails
    
    Features:
    - Automatic retry on failure (3 attempts)
    - Exponential backoff between retries
    - Task monitoring and logging
    - Error tracking
    """
    try:
        from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
        
        logger.info(f"📧 [CELERY TASK] Sending OTP email to {email} | Task ID: {self.request.id}")
        print(f"\n{'='*80}")
        print(f"[CELERY TASK] Task ID: {self.request.id}")
        print(f"[CELERY TASK] Email: {email}")
        print(f"[CELERY TASK] Subject: {subject}")
        print(f"[CELERY TASK] Sending via: {settings.EMAIL_BACKEND}")
        print(f"{'='*80}\n")
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"✅ [CELERY TASK] Email sent successfully to {email} | Task ID: {self.request.id}")
        print(f"\n{'='*80}")
        print(f"[CELERY TASK] ✅ SUCCESS!")
        print(f"[CELERY TASK] send_mail returned: {result}")
        print(f"{'='*80}\n")
        
        return {
            'status': 'success',
            'email': email,
            'task_id': str(self.request.id),
            'result': result
        }
    
    except Exception as exc:
        logger.error(f"❌ [CELERY TASK] Failed to send email to {email}: {str(exc)} | Task ID: {self.request.id}")
        logger.error(f"   Retry #{self.request.retries + 1}/3")
        
        print(f"\n{'='*80}")
        print(f"[CELERY TASK] ❌ EXCEPTION!")
        print(f"[CELERY TASK] Error: {type(exc).__name__}: {str(exc)}")
        print(f"[CELERY TASK] Retry: {self.request.retries + 1}/3")
        print(f"{'='*80}\n")
        
        import traceback
        print(traceback.format_exc())
        
        # Celery will automatically retry based on configuration above
        raise exc


@shared_task(name='accounts.test_celery')
def test_celery_task(message):
    """Test task to verify Celery is working"""
    logger.info(f"🎉 Celery is working! Message: {message}")
    return f"Task completed: {message}"


@shared_task(
    bind=True,
    name='accounts.send_schedule_notification_email',
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def send_schedule_notification_email(self, email, subject, message, html_message):
    """
    Send schedule update notification email to a single user
    Used for batch processing to avoid overwhelming the email server
    """
    try:
        from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
        
        logger.info(f"📧 Sending schedule notification to {email} | Task ID: {self.request.id}")
        
        result = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False
        )
        
        logger.info(f"✅ Schedule notification sent to {email}")
        
        return {
            'status': 'success',
            'email': email,
            'task_id': str(self.request.id),
            'result': result
        }
    
    except Exception as exc:
        logger.error(f"❌ Failed to send schedule notification to {email}: {str(exc)}")
        raise exc


@shared_task(
    bind=True,
    name='accounts.send_bulk_schedule_notifications',
    max_retries=2,
)
def send_bulk_schedule_notifications(self, user_emails, schedule_data, action='added'):
    """
    Send schedule update notifications to multiple users in batches
    
    Args:
        user_emails: List of email addresses to notify
        schedule_data: Dict containing schedule information
        action: 'added', 'updated', or 'deleted'
    
    Returns:
        Dict with success count and failed emails
    """
    try:
        logger.info(f"📧 Starting bulk schedule notification | Recipients: {len(user_emails)} | Action: {action}")
        
        success_count = 0
        failed_emails = []
        
        # Generate email content
        subject = f"E-KOLEK: Garbage Collection Schedule {action.title()}"
        
        # Prepare schedule details
        barangay_name = schedule_data.get('barangay_name', 'your barangay')
        day = schedule_data.get('day', '')
        start_time = schedule_data.get('start_time', '')
        end_time = schedule_data.get('end_time', '')
        waste_types = schedule_data.get('waste_types', [])
        notes = schedule_data.get('notes', '')
        
        # Create plain text message
        if action == 'deleted':
            message = f"""
Hello,

The garbage collection schedule for {barangay_name} on {day} has been REMOVED.

Please check the app for updated collection schedules.

Best regards,
E-KOLEK Team
            """
        else:
            waste_types_str = ', '.join(waste_types) if waste_types else 'All types'
            action_text = 'has been added' if action == 'added' else 'has been updated'
            
            message = f"""
Hello,

The garbage collection schedule for {barangay_name} {action_text}:

Day: {day}
Time: {start_time} - {end_time}
Waste Types: {waste_types_str}
{f'Notes: {notes}' if notes else ''}

Please prepare your segregated waste accordingly.

Best regards,
E-KOLEK Team
            """
        
        # Create HTML message
        if action == 'deleted':
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden; }}
                    .header {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 40px 20px; text-align: center; }}
                    .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; }}
                    .content {{ padding: 40px 30px; }}
                    .alert-box {{ background: #fee2e2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                    .info-box {{ background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                    .footer {{ background-color: #f9fafb; padding: 25px; text-align: center; border-top: 1px solid #e5e7eb; }}
                    .footer p {{ color: #6b7280; font-size: 14px; margin: 5px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="display: inline-block; width: 50px; height: 50px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; margin-bottom: 10px; line-height: 50px; font-size: 24px;">🗑️</div>
                        <h1>E-KOLEK</h1>
                        <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0;">Schedule Update</p>
                    </div>
                    
                    <div class="content">
                        <div class="alert-box">
                            <h2 style="color: #dc2626; margin: 0 0 10px 0;">⚠️ Schedule Removed</h2>
                            <p style="margin: 0; color: #333;">The garbage collection schedule for <strong>{barangay_name}</strong> on <strong>{day}</strong> has been removed.</p>
                        </div>
                        
                        <div class="info-box">
                            <p style="margin: 0; color: #333;">📱 Please check the E-KOLEK app for the latest collection schedules for your barangay.</p>
                        </div>
                        
                        <p style="color: #666; line-height: 1.6;">Stay updated with your waste collection schedule to ensure proper waste management in your community.</p>
                    </div>
                    
                    <div class="footer">
                        <p style="font-weight: 600; color: #333;">Best regards,</p>
                        <p style="font-weight: 600; color: #6366f1;">E-KOLEK Team</p>
                        <p style="margin-top: 15px;">© 2025 E-KOLEK. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            waste_types_html = ', '.join(waste_types) if waste_types else 'All types'
            action_color = '#10b981' if action == 'added' else '#3b82f6'
            action_icon = '🆕' if action == 'added' else '🔄'
            action_text = 'New Schedule Added' if action == 'added' else 'Schedule Updated'
            
            html_message = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden; }}
                    .header {{ background: linear-gradient(135deg, {action_color} 0%, {action_color}dd 100%); padding: 40px 20px; text-align: center; }}
                    .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; }}
                    .content {{ padding: 40px 30px; }}
                    .schedule-box {{ background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%); padding: 25px; border-radius: 10px; margin: 20px 0; border: 2px solid {action_color}; }}
                    .schedule-item {{ margin: 10px 0; padding: 10px 0; border-bottom: 1px solid #d1d5db; }}
                    .schedule-item:last-child {{ border-bottom: none; }}
                    .schedule-label {{ font-weight: 600; color: #6b7280; font-size: 14px; text-transform: uppercase; }}
                    .schedule-value {{ color: #333; font-size: 16px; margin-top: 5px; }}
                    .footer {{ background-color: #f9fafb; padding: 25px; text-align: center; border-top: 1px solid #e5e7eb; }}
                    .footer p {{ color: #6b7280; font-size: 14px; margin: 5px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div style="display: inline-block; width: 50px; height: 50px; background-color: rgba(255, 255, 255, 0.2); border-radius: 50%; margin-bottom: 10px; line-height: 50px; font-size: 24px;">🗑️</div>
                        <h1>E-KOLEK</h1>
                        <p style="color: rgba(255, 255, 255, 0.9); margin: 10px 0 0 0;">Garbage Collection Schedule</p>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: {action_color}; margin: 0 0 20px 0;">{action_icon} {action_text}</h2>
                        <p style="color: #666; line-height: 1.6;">A garbage collection schedule for <strong>{barangay_name}</strong> has been {action}. Please take note of the following details:</p>
                        
                        <div class="schedule-box">
                            <div class="schedule-item">
                                <div class="schedule-label">📍 Barangay</div>
                                <div class="schedule-value">{barangay_name}</div>
                            </div>
                            <div class="schedule-item">
                                <div class="schedule-label">📅 Day</div>
                                <div class="schedule-value">{day}</div>
                            </div>
                            <div class="schedule-item">
                                <div class="schedule-label">🕒 Collection Time</div>
                                <div class="schedule-value">{start_time} - {end_time}</div>
                            </div>
                            <div class="schedule-item">
                                <div class="schedule-label">🗑️ Waste Types</div>
                                <div class="schedule-value">{waste_types_html}</div>
                            </div>
                            {f'''<div class="schedule-item">
                                <div class="schedule-label">📝 Notes</div>
                                <div class="schedule-value">{notes}</div>
                            </div>''' if notes else ''}
                        </div>
                        
                        <div style="background-color: #dbeafe; border-left: 4px solid #3b82f6; padding: 15px; margin: 20px 0; border-radius: 4px;">
                            <p style="margin: 0; color: #1e40af; font-size: 14px;">
                                <strong>💡 Reminder:</strong> Please segregate your waste properly and prepare it before the collection time.
                            </p>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p style="font-weight: 600; color: #333;">Best regards,</p>
                        <p style="font-weight: 600; color: #6366f1;">E-KOLEK Team</p>
                        <p style="margin-top: 15px;">© 2025 E-KOLEK. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        # Send emails in batches to avoid overwhelming the email server
        # Process emails individually using Celery for better error handling
        from_email = f"E-KOLEK System <{settings.DEFAULT_FROM_EMAIL}>"
        
        for email in user_emails:
            if not email:  # Skip empty emails
                continue
                
            try:
                # Queue individual email task
                send_schedule_notification_email.delay(
                    email=email,
                    subject=subject,
                    message=message,
                    html_message=html_message
                )
                success_count += 1
                logger.info(f"✅ Queued notification for {email}")
                
            except Exception as e:
                logger.error(f"❌ Failed to queue notification for {email}: {str(e)}")
                failed_emails.append(email)
        
        result = {
            'status': 'completed',
            'total_recipients': len(user_emails),
            'success_count': success_count,
            'failed_count': len(failed_emails),
            'failed_emails': failed_emails,
            'task_id': str(self.request.id)
        }
        
        logger.info(f"✅ Bulk notification task completed | Success: {success_count}/{len(user_emails)}")
        
        return result
        
    except Exception as exc:
        logger.error(f"❌ Bulk schedule notification task failed: {str(exc)}")
        raise exc
