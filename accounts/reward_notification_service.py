"""
Reward Notification Service for E-KOLEK System
Handles sending email notifications to users when new rewards are added
"""
import logging
import threading
from django.conf import settings

logger = logging.getLogger(__name__)


def get_all_users_with_email():
    """
    Get all approved users with email addresses
    
    Returns:
        QuerySet of Users with email addresses
    """
    from accounts.models import Users
    
    # Get all approved, active users who have email addresses
    users = Users.objects.filter(
        status='approved',
        is_active=True,
        email__isnull=False
    ).exclude(email='')
    
    return users


def send_emails_in_background(user_emails, reward_data, image_file_id=None):
    """
    Send emails via Django's email system (now uses Resend API backend).
    This function is called from a background thread.
    
    Args:
        user_emails: List of email addresses
        reward_data: Dictionary with reward information
        image_file_id: Google Drive file ID for the reward image (optional)
    """
    from django.core.mail import EmailMultiAlternatives
    import io
    import base64
    
    success_count = 0
    failed_emails = []
    
    print(f"\n[BACKGROUND] Sending new reward emails to {len(user_emails)} users...")
    logger.info(f"Background reward email sending started for {len(user_emails)} users")
    
    # Download image from Google Drive if available
    image_data = None
    image_filename = None
    image_content_type = None
    
    if image_file_id:
        try:
            print(f"\n[BACKGROUND] Downloading image from Google Drive...")
            print(f"  File ID: {image_file_id}")
            
            # Import Google Drive storage
            from eko.google_drive_storage import GoogleDriveStorage
            storage = GoogleDriveStorage()
            
            # Download the file
            file_content = storage.service.files().get_media(fileId=image_file_id).execute()
            
            # Get file metadata
            file_metadata = storage.service.files().get(fileId=image_file_id, fields='name,mimeType').execute()
            
            image_data = file_content
            image_filename = file_metadata.get('name', 'reward.jpg')
            image_content_type = file_metadata.get('mimeType', 'image/jpeg')
            
            print(f"  ✅ Downloaded: {image_filename} ({len(image_data)} bytes)")
            print(f"  Content-Type: {image_content_type}")
            logger.info(f"Image downloaded successfully: {image_filename} ({len(image_data)} bytes)")
            
        except Exception as e:
            print(f"  ⚠️ Failed to download image: {str(e)}")
            logger.warning(f"Failed to download image from Google Drive: {str(e)}")
            # Continue without image
    
    # Generate email content with beautiful HTML design
    subject = f"🎁 E-KOLEK: New Reward Available - {reward_data['name']}"
    
    # Create plain text message (fallback)
    message = f"""
Hello,

Great news! A new reward is now available in the E-KOLEK system!

🎁 Reward: {reward_data['name']}
📦 Category: {reward_data['category']}
⭐ Points Required: {reward_data['points']} points
📋 Description: {reward_data['description']}
📊 Stock Available: {reward_data['stock']} items

Start collecting points today and claim this amazing reward!

Open the E-KOLEK app to view the reward and start earning points.

Best regards,
E-KOLEK Team
    """
    
    # Create beautiful HTML email
    html_message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Reward Available</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f3f4f6;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                        
                        <!-- Header with Gradient -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #ec4899 0%, #d946ef 100%); padding: 40px 30px; text-align: center;">
                                <table role="presentation" style="margin: 0 auto 20px;">
                                    <tr>
                                        <td style="background-color: rgba(255, 255, 255, 0.2); width: 80px; height: 80px; border-radius: 50%; text-align: center; vertical-align: middle; line-height: 80px;">
                                            <span style="font-size: 48px; display: inline-block; vertical-align: middle; line-height: normal;">🎁</span>
                                        </td>
                                    </tr>
                                </table>
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">E-KOLEK</h1>
                                <p style="color: rgba(255, 255, 255, 0.95); margin: 10px 0 0 0; font-size: 16px;">New Reward Available!</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <!-- Announcement Banner -->
                                <div style="background: linear-gradient(135deg, #fce7f3 0%, #fbcfe8 100%); border-left: 4px solid #ec4899; padding: 20px; border-radius: 8px; margin-bottom: 30px; text-align: center;">
                                    <h2 style="color: #ec4899; margin: 0; font-size: 22px; font-weight: 600;">✨ New Reward Added</h2>
                                </div>
                                
                                <!-- Reward Image Thumbnail (if available) -->
                                {f'''<div style="text-align: center; margin-bottom: 25px;">
                                    <img src="{image_data_url}" alt="{reward_data['name']}" style="max-width: 300px; max-height: 300px; width: auto; height: auto; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); display: inline-block;">
                                </div>''' if image_data_url else ''}
                                
                                <!-- Reward Name -->
                                <div style="text-align: center; margin-bottom: 30px;">
                                    <h3 style="color: #1f2937; margin: 0; font-size: 24px; font-weight: 700;">🎁 {reward_data['name']}</h3>
                                </div>
                                
                                <!-- Reward Details Card -->
                                <div style="background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%); border-radius: 12px; padding: 25px; margin-bottom: 25px; border: 2px solid #ec4899;">
                                    
                                    <!-- Category -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">📦 CATEGORY</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #1f2937; font-size: 16px; font-weight: 600;">{reward_data['category']}</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Points Required -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">⭐ POINTS REQUIRED</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #ec4899; font-size: 20px; font-weight: 700;">{reward_data['points']} points</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Stock Available -->
                                    <div style="margin-bottom: 20px;">
                                        <table role="presentation" style="width: 100%;">
                                            <tr>
                                                <td style="width: 35%; vertical-align: top;">
                                                    <span style="color: #6b7280; font-size: 14px; font-weight: 600;">📊 STOCK AVAILABLE</span>
                                                </td>
                                                <td style="vertical-align: top;">
                                                    <span style="color: #10b981; font-size: 18px; font-weight: 700;">{reward_data['stock']} items</span>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <!-- Description -->
                                    <div style="margin-bottom: 0;">
                                        <p style="color: #6b7280; font-size: 14px; font-weight: 600; margin: 0 0 10px 0;">📋 DESCRIPTION</p>
                                        <p style="color: #374151; font-size: 15px; line-height: 1.6; margin: 0;">{reward_data['description']}</p>
                                    </div>
                                    
                                </div>
                                
                                <!-- Call to Action -->
                                <div style="background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 25px;">
                                    <p style="color: #1e40af; margin: 0 0 10px 0; font-size: 16px; font-weight: 600; line-height: 1.6;">
                                        🌟 Start earning points today!
                                    </p>
                                    <p style="color: #3b82f6; margin: 0; font-size: 14px; line-height: 1.6;">
                                        Open the E-KOLEK app to view this reward and start collecting points through waste segregation activities.
                                    </p>
                                </div>
                                
                                <!-- How to Earn Points -->
                                <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px;">
                                    <p style="color: #6b7280; margin: 0 0 10px 0; font-size: 14px; font-weight: 600;">💡 How to Earn Points:</p>
                                    <ul style="color: #6b7280; margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.8;">
                                        <li>Properly segregate your waste</li>
                                        <li>Dispose waste on collection days</li>
                                        <li>Complete educational quizzes</li>
                                        <li>Watch learning videos</li>
                                        <li>Refer family and friends</li>
                                        <li>Participate in community activities</li>
                                    </ul>
                                </div>
                                
                                <!-- Urgency Note -->
                                <div style="background-color: #fef3c7; border-left: 3px solid #f59e0b; padding: 15px; border-radius: 6px; margin-top: 20px;">
                                    <p style="color: #92400e; margin: 0; font-size: 14px;"><strong>⚡ Limited Stock:</strong> Only {reward_data['stock']} items available. Claim yours before they run out!</p>
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
    
    # Debug: Show image attachment info
    if image_data:
        print(f"\n📧 EMAIL IMAGE INFO:")
        print(f"  Method: Base64 Data URL (embedded in HTML)")
        print(f"  Filename: {image_filename}")
        print(f"  Size: {len(image_data)} bytes")
        print(f"  Content-Type: {image_content_type}")
        print(f"  ✅ Image will be embedded directly - NO attachments!")
        print()
        
        # Convert image to base64 for embedding in HTML
        import base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        image_data_url = f"data:{image_content_type};base64,{image_base64}"
    else:
        image_data_url = None
    
    # Send to all users
    for i, email in enumerate(user_emails, 1):
        if not email:
            continue
        
        try:
            # Create EmailMultiAlternatives for better control
            msg = EmailMultiAlternatives(
                subject=subject,
                body=message,
                from_email=from_email,
                to=[email]
            )
            
            # Add HTML version
            msg.attach_alternative(html_message, "text/html")
            
            # NOTE: No longer attaching image as file - it's embedded as base64 data URL in HTML
            # This prevents Gmail from showing downloadable attachment at bottom
            
            # Send email
            msg.send(fail_silently=False)
            
            success_count += 1
            print(f"  [BACKGROUND] [OK] [{i}/{len(user_emails)}] Sent to {email}")
            logger.info(f"Background reward email sent to {email}")
            
        except Exception as e:
            print(f"  [BACKGROUND] [FAIL] [{i}/{len(user_emails)}] Failed: {email} - {str(e)}")
            logger.error(f"Failed to send background reward email to {email}: {str(e)}")
            failed_emails.append(email)
    
    print(f"\n[BACKGROUND] COMPLETE:")
    print(f"   Total: {len(user_emails)}")
    print(f"   Sent: {success_count}")
    print(f"   Failed: {len(failed_emails)}")
    
    logger.info(f"Background reward email sending completed | Success: {success_count}/{len(user_emails)}")


def send_new_reward_notification(reward):
    """
    Send email notifications to all users about a new reward
    
    Args:
        reward: Reward model instance
    
    Returns:
        dict: Result with success status and details
    """
    try:
        print(f"\n{'='*70}")
        print(f"REWARD NOTIFICATION SERVICE")
        print(f"{'='*70}")
        print(f"New Reward: {reward.name}")
        print(f"Category: {reward.category.name if reward.category else 'N/A'}")
        print(f"Points: {reward.points_required}")
        print(f"Stock: {reward.stock}")
        
        logger.info(f"=== REWARD NOTIFICATION SERVICE ===")
        logger.info(f"New Reward: {reward.name} | Points: {reward.points_required}")
        
        # Get all users with email
        users = get_all_users_with_email()
        user_emails = list(users.values_list('email', flat=True))
        
        print(f"\nUser Check:")
        print(f"  - Found {len(user_emails)} users with email addresses")
        
        logger.info(f"Found {len(user_emails)} users with email addresses")
        
        if not user_emails:
            warning_msg = "WARNING: No users with email addresses found"
            print(f"\n{warning_msg}")
            logger.warning("No users with email found")
            return {
                'success': True,
                'message': 'No users with email to notify',
                'recipients_count': 0,
                'warning': 'No users with email addresses'
            }
        
        # Show sample of recipients
        print(f"\nRecipients (showing first 5):")
        for i, email in enumerate(user_emails[:5]):
            print(f"  {i+1}. {email}")
        if len(user_emails) > 5:
            print(f"  ... and {len(user_emails) - 5} more")
        
        # Prepare reward data
        reward_data = {
            'name': reward.name,
            'category': reward.category.name if reward.category else 'General',
            'points': reward.points_required,
            'description': reward.description,
            'stock': reward.stock,
            'image_url': reward.image_url_for_email if reward.image else None  # Use email-optimized URL
        }
        
        # Debug logging for image URL
        if reward.image:
            print(f"\n📸 IMAGE DEBUG:")
            print(f"  - reward.image: {reward.image}")
            print(f"  - reward.image.name: {reward.image.name}")
            print(f"  - reward.image_url (web/dashboard): {reward.image_url}")
            print(f"  - reward.image_url_for_email (email): {reward.image_url_for_email}")
            logger.info(f"Image debug | name: {reward.image.name} | web_url: {reward.image_url} | email_url: {reward.image_url_for_email}")
        else:
            print(f"\n⚠️  No image attached to reward")
            logger.warning("No image attached to reward")
        
        # Send emails in BACKGROUND THREAD so reward save is not blocked
        print(f"\nEmail Method:")
        print(f"  - Using: Background Thread (Asynchronous - Non-Blocking)")
        print(f"  - Image: Inline attachment (bypasses ad blockers!)")
        
        print(f"\nStarting background email thread...")
        print(f"  - Reward will be saved IMMEDIATELY")
        print(f"  - Emails will send in the background")
        logger.info("Starting background email thread")
        
        # Get image file ID if available
        image_file_id = reward.image.name if reward.image else None
        
        # Start background thread for email sending
        email_thread = threading.Thread(
            target=send_emails_in_background,
            args=(user_emails, reward_data, image_file_id),
            daemon=True  # Thread will not prevent program exit
        )
        email_thread.start()
        
        print(f"\n{'='*70}")
        print(f"REWARD SAVED!")
        print(f"  - Reward has been saved to database")
        print(f"  - {len(user_emails)} emails are being sent in background")
        print(f"  - Admin can continue working immediately")
        print(f"{'='*70}\n")
        
        logger.info(f"Email thread started | {len(user_emails)} emails queued for background sending")
        
        return {
            'success': True,
            'message': f'Reward saved! Notifications are being sent to {len(user_emails)} users in the background',
            'recipients_count': len(user_emails),
            'async': True,
            'background_thread': True
        }
    
    except Exception as e:
        error_msg = f"Reward notification service error: {str(e)}"
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
