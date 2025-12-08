"""
Security monitoring and reporting views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
import logging

from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule, RewardCategory,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from cenro.models import AdminActionHistory
from game.models import Question, Choice, WasteCategory, WasteItem
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required

logger = logging.getLogger(__name__)

import time
import csv
from datetime import datetime, timedelta
from django.http import HttpResponse
from accounts.models import LoginAttempt
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.db.models import Count


# Security Dashboard - Admin Security Management
@admin_required
@permission_required('can_manage_security')
def adminsecurity(request):
    """Security monitoring dashboard for admin users"""
    from datetime import timedelta
    from django.db.models import Count
    from accounts.models import LoginAttempt
    
    # Get time periods
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)
    
    # Basic statistics
    stats = {
        'total_attempts_24h': LoginAttempt.objects.filter(timestamp__gte=last_24h).count(),
        'failed_attempts_24h': LoginAttempt.objects.filter(
            timestamp__gte=last_24h, success=False
        ).count(),
        'successful_logins_24h': LoginAttempt.objects.filter(
            timestamp__gte=last_24h, success=True
        ).count(),
        'unique_ips_24h': LoginAttempt.objects.filter(
            timestamp__gte=last_24h
        ).values('ip_address').distinct().count(),
    }
    
    # Calculate failure rate
    if stats['total_attempts_24h'] > 0:
        stats['failure_rate_24h'] = round(
            (stats['failed_attempts_24h'] / stats['total_attempts_24h']) * 100, 2
        )
    else:
        stats['failure_rate_24h'] = 0
    
    # Top failed usernames (last 24h)
    top_failed_users = (
        LoginAttempt.objects
        .filter(timestamp__gte=last_24h, success=False)
        .values('username')
        .annotate(failures=Count('id'))
        .order_by('-failures')[:10]
    )
    
    # Suspicious IPs (IPs with multiple failures)
    suspicious_ips = (
        LoginAttempt.objects
        .filter(timestamp__gte=last_24h, success=False)
        .values('ip_address')
        .annotate(failures=Count('id'))
        .filter(failures__gte=3)  # 3+ failures considered suspicious
        .order_by('-failures')[:10]
    )
    
    # Recent failed attempts
    recent_failures = (
        LoginAttempt.objects
        .filter(timestamp__gte=last_24h, success=False)
        .order_by('-timestamp')[:20]
    )
    
    # Hourly login activity (last 24h)
    hourly_activity = []
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        
        total = LoginAttempt.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        ).count()
        
        failed = LoginAttempt.objects.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end,
            success=False
        ).count()
        
        hourly_activity.append({
            'hour': hour_start.strftime('%H:00'),
            'total': total,
            'failed': failed,
            'success': total - failed
        })
    
    hourly_activity.reverse()  # Show oldest to newest
    
    context = {
        'stats': stats,
        'top_failed_users': top_failed_users,
        'suspicious_ips': suspicious_ips,
        'recent_failures': recent_failures,
        'hourly_activity': hourly_activity,
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,  # Add admin user context
        'page_name': 'adminsecurity',  # Add page name for active menu
    }
    
    return render(request, 'adminsecurity.html', context)

# ===============================
# QUIZ MANAGEMENT VIEWS
# ===============================


# ===============================
# SECURITY DASHBOARD API VIEWS
# ===============================

@admin_required
@permission_required('can_manage_security')
def generate_security_report(request):
    """
    Generate security reports in CSV and PDF formats
    For Security Analyst role
    Handles GET requests from the report form
    """
    import csv
    from datetime import datetime, timedelta
    from django.http import HttpResponse
    from accounts.models import LoginAttempt, Users, Redemption, PointsTransaction
    from cenro.models import AdminActionHistory
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    
    # Accept GET request (from form submission)
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get parameters from GET request
        report_type = request.GET.get('report_type', 'security')
        format_type = request.GET.get('format', 'csv')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # Validate required parameters
        if not start_date_str or not end_date_str:
            return JsonResponse({'error': 'Start date and end date are required'}, status=400)
        
        # Parse dates
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)  # Include end date
        
        # ===================================
        # SECURITY OVERVIEW REPORT
        # ===================================
        if report_type == 'security':
            queryset = LoginAttempt.objects.filter(
                timestamp__gte=start_date,
                timestamp__lt=end_date
            ).order_by('-timestamp')
            
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="security_report_{start_date.strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Timestamp', 'Username', 'IP Address', 'Status', 'Failure Reason', 'User Agent'])
                
                for attempt in queryset:
                    writer.writerow([
                        attempt.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        attempt.username or 'Unknown',
                        attempt.ip_address,
                        'Success' if attempt.success else 'Failed',
                        attempt.failure_reason or '-',
                        (attempt.user_agent[:50] + '...') if len(attempt.user_agent) > 50 else attempt.user_agent
                    ])
                
                return response
            
            elif format_type == 'pdf':
                # Create PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30, alignment=TA_CENTER)
                elements.append(Paragraph("Security Overview Report", title_style))
                elements.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Summary statistics
                total_attempts = queryset.count()
                successful = queryset.filter(success=True).count()
                failed = queryset.filter(success=False).count()
                failure_rate = round((failed / max(total_attempts, 1)) * 100, 1)
                
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Login Attempts', str(total_attempts)],
                    ['Successful Logins', str(successful)],
                    ['Failed Logins', str(failed)],
                    ['Failure Rate', f'{failure_rate}%'],
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 0.5*inch))
                
                # Login attempts table (limit to 50 most recent)
                elements.append(Paragraph("Recent Login Attempts (Latest 50)", styles['Heading2']))
                elements.append(Spacer(1, 0.2*inch))
                
                data = [['Date/Time', 'Username', 'IP Address', 'Status']]
                for attempt in queryset[:50]:
                    data.append([
                        attempt.timestamp.strftime('%Y-%m-%d %H:%M'),
                        (attempt.username or 'Unknown')[:20],
                        attempt.ip_address,
                        'Success' if attempt.success else 'FAILED'
                    ])
                
                table = Table(data, colWidths=[1.8*inch, 1.8*inch, 1.5*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(table)
                
                # Build PDF
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="security_report_{start_date.strftime("%Y%m%d")}.pdf"'
                return response
        
        # ===================================
        # USER ACTIVITY REPORT
        # ===================================
        elif report_type == 'users':
            queryset = Users.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).select_related('family').order_by('-created_at')
            
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="users_report_{start_date.strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Registration Date', 'Username', 'Full Name', 'Phone', 'Email', 'Family', 'Total Points', 'Status'])
                
                for user in queryset:
                    writer.writerow([
                        user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        user.username,
                        user.full_name,
                        user.phone,
                        user.email or '-',
                        user.family.family_name if user.family else '-',
                        user.total_points,
                        'Active' if user.is_active else 'Inactive'
                    ])
                
                return response
            
            elif format_type == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30, alignment=TA_CENTER)
                elements.append(Paragraph("User Activity Report", title_style))
                elements.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Summary
                total_users = queryset.count()
                active_users = queryset.filter(is_active=True).count()
                total_points = sum([user.total_points for user in queryset])
                
                summary_data = [
                    ['Metric', 'Value'],
                    ['New Users (Period)', str(total_users)],
                    ['Active Users', str(active_users)],
                    ['Total Points Accumulated', str(total_points)],
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 0.5*inch))
                
                # Users table
                elements.append(Paragraph(f"New User Registrations (Total: {total_users})", styles['Heading2']))
                elements.append(Spacer(1, 0.2*inch))
                
                data = [['Date', 'Full Name', 'Phone', 'Family', 'Points']]
                for user in queryset[:100]:  # Limit to 100
                    data.append([
                        user.created_at.strftime('%Y-%m-%d'),
                        user.full_name[:25],
                        user.phone,
                        (user.family.family_name[:15] if user.family else '-'),
                        str(user.total_points)
                    ])
                
                table = Table(data, colWidths=[1.2*inch, 2*inch, 1.3*inch, 1.5*inch, 0.8*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(table)
                
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="users_report_{start_date.strftime("%Y%m%d")}.pdf"'
                return response
        
        # ===================================
        # REDEMPTION SUMMARY REPORT
        # ===================================
        elif report_type == 'redemptions':
            queryset = Redemption.objects.filter(
                redemption_date__gte=start_date,
                redemption_date__lt=end_date
            ).select_related('user', 'reward', 'approved_by').order_by('-redemption_date')
            
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="redemptions_report_{start_date.strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Redemption Date', 'User', 'Reward', 'Quantity', 'Points Used', 'Approved By', 'Claim Date', 'Status'])
                
                for redemption in queryset:
                    writer.writerow([
                        redemption.redemption_date.strftime('%Y-%m-%d %H:%M:%S'),
                        redemption.user.full_name,
                        redemption.reward.name,
                        redemption.quantity,
                        redemption.points_used,
                        redemption.approved_by.username if redemption.approved_by else 'Pending',
                        redemption.claim_date.strftime('%Y-%m-%d') if redemption.claim_date else '-',
                        'Claimed' if redemption.claim_date else ('Approved' if redemption.approved_by else 'Pending')
                    ])
                
                return response
            
            elif format_type == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30, alignment=TA_CENTER)
                elements.append(Paragraph("Redemption Summary Report", title_style))
                elements.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Summary
                total_redemptions = queryset.count()
                total_points = sum([r.points_used for r in queryset])
                claimed = queryset.filter(claim_date__isnull=False).count()
                pending = queryset.filter(claim_date__isnull=True).count()
                
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Redemptions', str(total_redemptions)],
                    ['Total Points Redeemed', str(total_points)],
                    ['Claimed', str(claimed)],
                    ['Pending', str(pending)],
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 0.5*inch))
                
                # Redemptions table
                elements.append(Paragraph(f"Redemption Details (Latest 100)", styles['Heading2']))
                elements.append(Spacer(1, 0.2*inch))
                
                data = [['Date', 'User', 'Reward', 'Qty', 'Points', 'Status']]
                for redemption in queryset[:100]:
                    status = 'Claimed' if redemption.claim_date else ('Approved' if redemption.approved_by else 'Pending')
                    data.append([
                        redemption.redemption_date.strftime('%Y-%m-%d'),
                        redemption.user.full_name[:20],
                        redemption.reward.name[:25],
                        str(redemption.quantity),
                        str(redemption.points_used),
                        status
                    ])
                
                table = Table(data, colWidths=[1*inch, 1.8*inch, 2*inch, 0.5*inch, 0.8*inch, 0.9*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(table)
                
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="redemptions_report_{start_date.strftime("%Y%m%d")}.pdf"'
                return response
        
        # ===================================
        # ADMIN ACTIONS REPORT
        # ===================================
        elif report_type == 'admin_actions':
            queryset = AdminActionHistory.objects.filter(
                timestamp__gte=start_date,
                timestamp__lt=end_date
            ).select_related('admin_user', 'target_admin').order_by('-timestamp')
            
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="admin_actions_report_{start_date.strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                writer.writerow(['Timestamp', 'Admin User', 'Action', 'Target', 'IP Address', 'Description'])
                
                for action in queryset:
                    writer.writerow([
                        action.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        action.admin_user.full_name,
                        action.get_action_display(),
                        action.target_admin.full_name if action.target_admin else '-',
                        action.ip_address,
                        action.description
                    ])
                
                return response
            
            elif format_type == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30, alignment=TA_CENTER)
                elements.append(Paragraph("Admin Actions Report", title_style))
                elements.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Spacer(1, 0.3*inch))
                
                # Summary
                total_actions = queryset.count()
                
                summary_data = [
                    ['Metric', 'Value'],
                    ['Total Admin Actions', str(total_actions)],
                ]
                
                summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(summary_table)
                elements.append(Spacer(1, 0.5*inch))
                
                # Actions table
                elements.append(Paragraph(f"Admin Action History (Latest 100)", styles['Heading2']))
                elements.append(Spacer(1, 0.2*inch))
                
                data = [['Date/Time', 'Admin', 'Action', 'Description']]
                for action in queryset[:100]:
                    data.append([
                        action.timestamp.strftime('%Y-%m-%d %H:%M'),
                        action.admin_user.full_name[:20],
                        action.get_action_display()[:20],
                        action.description[:40]
                    ])
                
                table = Table(data, colWidths=[1.5*inch, 1.8*inch, 1.5*inch, 2.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(table)
                
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="admin_actions_report_{start_date.strftime("%Y%m%d")}.pdf"'
                return response
        
        # ===================================
        # COMPREHENSIVE REPORT
        # ===================================
        elif report_type == 'comprehensive':
            if format_type == 'csv':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="comprehensive_report_{start_date.strftime("%Y%m%d")}.csv"'
                
                writer = csv.writer(response)
                
                # Header
                writer.writerow(['COMPREHENSIVE SECURITY & ACTIVITY REPORT'])
                writer.writerow(['Report Period:', f'{start_date.strftime("%Y-%m-%d")} to {(end_date - timedelta(days=1)).strftime("%Y-%m-%d")}'])
                writer.writerow(['Generated:', timezone.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                
                # Security Summary
                writer.writerow(['=== SECURITY SUMMARY ==='])
                login_attempts = LoginAttempt.objects.filter(timestamp__gte=start_date, timestamp__lt=end_date)
                writer.writerow(['Total Login Attempts:', login_attempts.count()])
                writer.writerow(['Successful Logins:', login_attempts.filter(success=True).count()])
                writer.writerow(['Failed Logins:', login_attempts.filter(success=False).count()])
                failure_rate = round((login_attempts.filter(success=False).count() / max(login_attempts.count(), 1)) * 100, 1)
                writer.writerow(['Failure Rate:', f'{failure_rate}%'])
                writer.writerow([])
                
                # User Summary
                writer.writerow(['=== USER SUMMARY ==='])
                new_users = Users.objects.filter(created_at__gte=start_date, created_at__lt=end_date)
                writer.writerow(['New Users (Period):', new_users.count()])
                writer.writerow(['Total Active Users:', Users.objects.filter(is_active=True).count()])
                writer.writerow(['Total Points Distributed:', sum([u.total_points for u in new_users])])
                writer.writerow([])
                
                # Redemption Summary
                writer.writerow(['=== REDEMPTION SUMMARY ==='])
                redemptions = Redemption.objects.filter(redemption_date__gte=start_date, redemption_date__lt=end_date)
                writer.writerow(['Total Redemptions:', redemptions.count()])
                writer.writerow(['Total Points Redeemed:', sum([r.points_used for r in redemptions])])
                writer.writerow(['Claimed:', redemptions.filter(claim_date__isnull=False).count()])
                writer.writerow(['Pending:', redemptions.filter(claim_date__isnull=True).count()])
                writer.writerow([])
                
                # Admin Activity Summary
                writer.writerow(['=== ADMIN ACTIVITY SUMMARY ==='])
                admin_actions = AdminActionHistory.objects.filter(timestamp__gte=start_date, timestamp__lt=end_date)
                writer.writerow(['Total Admin Actions:', admin_actions.count()])
                writer.writerow([])
                
                # Points Transactions Summary
                writer.writerow(['=== POINTS TRANSACTIONS SUMMARY ==='])
                transactions = PointsTransaction.objects.filter(transaction_date__gte=start_date, transaction_date__lt=end_date)
                writer.writerow(['Total Transactions:', transactions.count()])
                points_earned = sum([t.points_amount for t in transactions if t.points_amount > 0])
                points_spent = sum([abs(t.points_amount) for t in transactions if t.points_amount < 0])
                writer.writerow(['Total Points Earned:', points_earned])
                writer.writerow(['Total Points Spent:', points_spent])
                writer.writerow([])
                
                return response
            
            elif format_type == 'pdf':
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
                elements = []
                styles = getSampleStyleSheet()
                
                # Title
                title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#667eea'), spaceAfter=30, alignment=TA_CENTER)
                elements.append(Paragraph("Comprehensive Security Report", title_style))
                elements.append(Paragraph(f"Period: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}", styles['Normal']))
                elements.append(Paragraph(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                elements.append(Spacer(1, 0.5*inch))
                
                # Security Summary
                elements.append(Paragraph("Security Summary", styles['Heading2']))
                login_attempts = LoginAttempt.objects.filter(timestamp__gte=start_date, timestamp__lt=end_date)
                total_attempts = login_attempts.count()
                successful = login_attempts.filter(success=True).count()
                failed = login_attempts.filter(success=False).count()
                failure_rate = round((failed / max(total_attempts, 1)) * 100, 1)
                
                security_data = [
                    ['Metric', 'Value'],
                    ['Total Login Attempts', str(total_attempts)],
                    ['Successful Logins', str(successful)],
                    ['Failed Logins', str(failed)],
                    ['Failure Rate', f'{failure_rate}%'],
                ]
                
                security_table = Table(security_data, colWidths=[3.5*inch, 2*inch])
                security_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(security_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # User Summary
                elements.append(Paragraph("User Activity Summary", styles['Heading2']))
                new_users = Users.objects.filter(created_at__gte=start_date, created_at__lt=end_date)
                total_new = new_users.count()
                total_active = Users.objects.filter(is_active=True).count()
                
                user_data = [
                    ['Metric', 'Value'],
                    ['New Users (Period)', str(total_new)],
                    ['Total Active Users', str(total_active)],
                    ['Total Points Distributed', str(sum([u.total_points for u in new_users]))],
                ]
                
                user_table = Table(user_data, colWidths=[3.5*inch, 2*inch])
                user_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(user_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Redemption Summary
                elements.append(Paragraph("Redemption Summary", styles['Heading2']))
                redemptions = Redemption.objects.filter(redemption_date__gte=start_date, redemption_date__lt=end_date)
                total_redemptions = redemptions.count()
                total_points = sum([r.points_used for r in redemptions])
                claimed = redemptions.filter(claim_date__isnull=False).count()
                pending = redemptions.filter(claim_date__isnull=True).count()
                
                redemption_data = [
                    ['Metric', 'Value'],
                    ['Total Redemptions', str(total_redemptions)],
                    ['Total Points Redeemed', str(total_points)],
                    ['Claimed', str(claimed)],
                    ['Pending', str(pending)],
                ]
                
                redemption_table = Table(redemption_data, colWidths=[3.5*inch, 2*inch])
                redemption_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(redemption_table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Admin Activity Summary
                elements.append(Paragraph("Admin Activity Summary", styles['Heading2']))
                admin_actions = AdminActionHistory.objects.filter(timestamp__gte=start_date, timestamp__lt=end_date)
                
                admin_data = [
                    ['Metric', 'Value'],
                    ['Total Admin Actions', str(admin_actions.count())],
                ]
                
                admin_table = Table(admin_data, colWidths=[3.5*inch, 2*inch])
                admin_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(admin_table)
                
                doc.build(elements)
                buffer.seek(0)
                
                response = HttpResponse(buffer, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="comprehensive_report_{start_date.strftime("%Y%m%d")}.pdf"'
                return response
        
        return JsonResponse({'error': 'Invalid report type'}, status=400)
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Report generation failed: {str(e)}'}, status=500)


