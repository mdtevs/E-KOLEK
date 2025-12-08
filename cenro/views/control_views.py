"""
Control management views (waste types, barangays, reward categories)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, IntegrityError
import logging
import time

from accounts.models import (
    Users, Family, Barangay, PointsTransaction, Reward, GarbageSchedule, RewardCategory,
    WasteType, WasteTransaction, Redemption, Notification, RewardHistory
)
from cenro.models import AdminActionHistory, TermsAndConditions
from game.models import Question, Choice, WasteCategory, WasteItem
from learn.models import LearningVideo, VideoWatchHistory

from ..admin_auth import admin_required, role_required, permission_required

logger = logging.getLogger(__name__)


# admincontrol - view for admin control management
@admin_required
@permission_required('can_manage_controls')
def admincontrol(request):
    waste_types = WasteType.objects.all()
    barangays = Barangay.objects.all()
    reward_categories = RewardCategory.objects.all()
    terms_and_conditions = TermsAndConditions.objects.all().order_by('language', '-created_at')
    
    return render(request, 'admincontrol.html', {
        'waste_types': waste_types,
        'barangays': barangays,
        'reward_categories': reward_categories,
        'terms_and_conditions': terms_and_conditions,
        'timestamp': int(time.time()),
        'admin_user': request.admin_user,  # Add admin user context
    })

# adminpints - views for admin points


@require_POST
def add_waste_type(request):
    from django.db import IntegrityError
    from django.contrib import messages
    
    name = request.POST.get('name')
    points_per_kg = request.POST.get('points_per_kg')
    if name and points_per_kg:
        try:
            WasteType.objects.create(name=name, points_per_kg=points_per_kg)
        except IntegrityError:
            messages.error(request, f'A waste type with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


@require_POST
def edit_waste_type(request, waste_id):
    from django.db import IntegrityError
    from django.contrib import messages
    
    waste = get_object_or_404(WasteType, id=waste_id)
    name = request.POST.get('name')
    points_per_kg = request.POST.get('points_per_kg')
    if name and points_per_kg:
        try:
            waste.name = name
            waste.points_per_kg = points_per_kg
            waste.save()
        except IntegrityError:
            messages.error(request, f'A waste type with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


@require_POST
def delete_waste_type(request, waste_id):
    waste = get_object_or_404(WasteType, id=waste_id)
    waste.delete()
    return redirect('cenro:admincontrol')


@require_POST
def add_barangay(request):
    from django.db import IntegrityError
    from django.contrib import messages
    
    name = request.POST.get('name')
    if name:
        try:
            Barangay.objects.create(name=name)
        except IntegrityError:
            messages.error(request, f'A barangay with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


@require_POST
def edit_barangay(request, barangay_id):
    from django.db import IntegrityError
    from django.contrib import messages
    
    barangay = get_object_or_404(Barangay, id=barangay_id)
    name = request.POST.get('name')
    if name:
        try:
            barangay.name = name
            barangay.save()
        except IntegrityError:
            messages.error(request, f'A barangay with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


@require_POST
def delete_barangay(request, barangay_id):
    barangay = get_object_or_404(Barangay, id=barangay_id)
    barangay.delete()
    return redirect('cenro:admincontrol')


def add_reward_category(request):
    from django.db import IntegrityError
    from django.contrib import messages
    
    if request.method == "POST":
        name = request.POST.get("name")
        description = request.POST.get("description")
        try:
            RewardCategory.objects.create(name=name, description=description)
        except IntegrityError:
            messages.error(request, f'A reward category with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


# Edit Reward Category View
@require_POST
def edit_reward_category(request, category_id):
    from django.db import IntegrityError
    from django.contrib import messages
    
    category = get_object_or_404(RewardCategory, id=category_id)
    name = request.POST.get('name')
    description = request.POST.get('description')
    if name:
        category.name = name
    category.description = description
    try:
        category.save()
    except IntegrityError:
        messages.error(request, f'A reward category with the name "{name}" already exists. Please use a different name.')
    return redirect('cenro:admincontrol')


# Redeem Reward API


def delete_reward_category(request, category_id):
    if request.method == "POST":
        RewardCategory.objects.filter(id=category_id).delete()
    return redirect('cenro:admincontrol')


# ========================================
# TERMS AND CONDITIONS MANAGEMENT
# ========================================

@admin_required
@permission_required('can_manage_controls')
@admin_required
@permission_required('can_manage_controls')
@require_POST
def add_terms(request):
    """Add new Terms and Conditions"""
    try:
        language = request.POST.get('language')
        title = request.POST.get('title')
        version = request.POST.get('version')
        content = request.POST.get('content')
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
        uploaded_file = request.FILES.get('file')
        
        # Validate required fields
        if not language or not title or not version:
            messages.error(request, 'Language, Title, and Version are required fields.')
            return redirect('cenro:admincontrol')
        
        # Create new terms instance
        terms = TermsAndConditions(
            language=language,
            title=title,
            version=version,
            content=content or '',  # Ensure content is never None
            is_active=is_active,
            created_by=request.admin_user,
            updated_by=request.admin_user
        )
        
        # Handle file upload if provided
        if uploaded_file:
            terms.file = uploaded_file
            terms.save()  # Save first to get file path
            
            # Try to extract content from file if content is empty
            if not content or content.strip() == '':
                extracted_content = terms.extract_content_from_file()
                if extracted_content:
                    terms.content = extracted_content
                    terms.save()
        else:
            # Ensure content is provided if no file uploaded
            if not content or content.strip() == '':
                messages.error(request, 'Please provide content or upload a file.')
                return redirect('cenro:admincontrol')
            terms.save()
        
        # Success - no message needed
        
    except Exception as e:
        logger.error(f"Error adding terms: {str(e)}")
        messages.error(request, f'Error adding terms: {str(e)}')
    
    return redirect('cenro:admincontrol')


@admin_required
@permission_required('can_manage_controls')
@require_POST
def edit_terms(request, terms_id):
    """Edit existing Terms and Conditions"""
    try:
        terms = get_object_or_404(TermsAndConditions, id=terms_id)
        
        terms.language = request.POST.get('language', terms.language)
        terms.title = request.POST.get('title', terms.title)
        terms.version = request.POST.get('version', terms.version)
        terms.content = request.POST.get('content', terms.content)
        terms.is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'
        terms.updated_by = request.admin_user
        
        # Handle file upload if provided
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            # Delete old file if exists
            if terms.file:
                terms.file.delete(save=False)
            
            terms.file = uploaded_file
            terms.save()
            
            # Try to extract content from file if content is empty
            new_content = request.POST.get('content', '')
            if not new_content or new_content.strip() == '':
                extracted_content = terms.extract_content_from_file()
                if extracted_content:
                    terms.content = extracted_content
                    terms.save()
        else:
            terms.save()
        
        # Success - no message needed
        
    except Exception as e:
        logger.error(f"Error editing terms: {str(e)}")
        messages.error(request, f'Error editing terms: {str(e)}')
    
    return redirect('cenro:admincontrol')


@admin_required
@permission_required('can_manage_controls')
@require_POST
def delete_terms(request, terms_id):
    """Delete Terms and Conditions"""
    try:
        terms = get_object_or_404(TermsAndConditions, id=terms_id)
        
        # Check if this terms version has user consents
        from accounts.models import UserConsent
        consent_count = UserConsent.objects.filter(terms_version=terms).count()
        
        if consent_count > 0:
            messages.error(request, 
                f'Cannot delete this terms version as {consent_count} users have accepted it. '
                f'You can deactivate it instead.')
            return redirect('cenro:admincontrol')
        
        title = terms.title
        version = terms.version
        
        # Delete associated file if exists
        if terms.file:
            terms.file.delete(save=False)
        
        terms.delete()
        # Success - no message needed
        
    except Exception as e:
        logger.error(f"Error deleting terms: {str(e)}")
        messages.error(request, f'Error deleting terms: {str(e)}')
    
    return redirect('cenro:admincontrol')


@admin_required
@permission_required('can_manage_controls')
@require_POST
def toggle_active_terms(request, terms_id):
    """Toggle active status of Terms and Conditions"""
    try:
        terms = get_object_or_404(TermsAndConditions, id=terms_id)
        terms.is_active = not terms.is_active
        terms.updated_by = request.admin_user
        terms.save()
        
        # Success - no message needed
        
    except Exception as e:
        logger.error(f"Error toggling terms status: {str(e)}")
        messages.error(request, f'Error toggling terms status: {str(e)}')
    
    return redirect('cenro:admincontrol')


@admin_required
@permission_required('can_manage_controls')
def get_terms_data(request, terms_id):
    """
    API endpoint to get terms data by ID for edit modal
    """
    try:
        terms = get_object_or_404(TermsAndConditions, id=terms_id)
        
        data = {
            'success': True,
            'terms': {
                'id': str(terms.id),
                'language': terms.language,
                'title': terms.title,
                'version': terms.version,
                'content': terms.content,
                'is_active': terms.is_active,
                'file_url': terms.file.url if terms.file else None,
                'file_name': terms.file.name.split('/')[-1] if terms.file else None,
            }
        }
        return JsonResponse(data)
    except Exception as e:
        logger.error(f"Error fetching terms data: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
def extract_file_content(request):
    """
    API endpoint to extract content from uploaded file
    Returns JSON with extracted text
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            uploaded_file = request.FILES['file']
            file_ext = uploaded_file.name.lower().split('.')[-1]
            
            extracted_content = None
            
            # Extract based on file type
            if file_ext == 'pdf':
                try:
                    import PyPDF2
                    import io
                    
                    # Read file content into memory
                    file_content = uploaded_file.read()
                    pdf_file = io.BytesIO(file_content)
                    
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    text_content = []
                    
                    for page in pdf_reader.pages:
                        text_content.append(page.extract_text())
                    
                    extracted_content = '\n\n'.join(text_content)
                except ImportError:
                    return JsonResponse({
                        'success': False,
                        'error': 'PyPDF2 not installed. Please install it to extract PDF content.'
                    })
                    
            elif file_ext in ['doc', 'docx']:
                try:
                    import docx
                    import io
                    
                    # Read file content into memory
                    file_content = uploaded_file.read()
                    doc_file = io.BytesIO(file_content)
                    
                    doc = docx.Document(doc_file)
                    text_content = []
                    
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            text_content.append(paragraph.text)
                    
                    extracted_content = '\n\n'.join(text_content)
                except ImportError:
                    return JsonResponse({
                        'success': False,
                        'error': 'python-docx not installed. Please install it to extract DOCX content.'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Unsupported file type: {file_ext}. Please upload PDF or DOCX files.'
                })
            
            if extracted_content:
                # Try to extract title and version from content
                lines = [line.strip() for line in extracted_content.split('\n') if line.strip()]
                title = lines[0][:255] if lines else 'Terms and Conditions'
                version = '1.0'  # Default version
                
                # Look for version in first few lines
                for line in lines[:10]:
                    if 'version' in line.lower():
                        import re
                        version_match = re.search(r'(\d+\.?\d*)', line)
                        if version_match:
                            version = version_match.group(1)
                        break
                
                return JsonResponse({
                    'success': True,
                    'content': extracted_content,
                    'suggested_title': title,
                    'suggested_version': version
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Could not extract content from file. File may be empty or corrupted.'
                })
                
        except Exception as e:
            logger.error(f"Error extracting file content: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Error processing file: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'No file provided'
    })


