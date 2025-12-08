"""
User registration views (family and member registration)
"""

from django.shortcuts import render, redirect
from django.contrib import messages
import logging

from accounts.models import Barangay, Users
from cenro.models import TermsAndConditions
from accounts.models import UserConsent
from accounts.forms import FamilyRegistrationForm, FamilyMemberRegistrationForm

logger = logging.getLogger(__name__)


def register(request):
    """Show registration selection page"""
    return render(request, 'register_select.html')


def register_family(request):
    """Para sa family registration (new family)"""
    if request.method == 'POST':
        form = FamilyRegistrationForm(request.POST)
        
        # Check if OTP has been verified for both phone and email
        otp_verified = request.POST.get('otp_verified') == 'true'
        verified_phone = request.session.get('verified_phone')
        form_phone = request.POST.get('phone')
        
        email_otp_verified = request.POST.get('email_otp_verified') == 'true'
        verified_email = request.session.get('verified_email')
        form_email = request.POST.get('email')
        
        if not otp_verified or verified_phone != form_phone:
            messages.error(request, "Please verify your phone number first.")
            barangays = Barangay.objects.all()
            return render(request, 'register.html', {
                'form': form,
                'barangays': barangays,
                'registration_type': 'family'
            })
        
        if not email_otp_verified or verified_email != form_email:
            messages.error(request, "Please verify your email address first.")
            barangays = Barangay.objects.all()
            return render(request, 'register.html', {
                'form': form,
                'barangays': barangays,
                'registration_type': 'family'
            })
        
        if form.is_valid():
            # Check terms acceptance
            if not form.cleaned_data.get('accept_terms'):
                messages.error(request, "You must accept the Terms and Conditions to register.")
                barangays = Barangay.objects.all()
                return render(request, 'register.html', {
                    'form': form,
                    'barangays': barangays,
                    'registration_type': 'family'
                })
            
            # Both OTP verified, proceed with registration
            family = form.save()
            
            # Get the representative user (the one with is_family_representative=True)
            representative = family.members.filter(is_family_representative=True).first()
            
            # Create consent records for both English and Tagalog terms
            if representative:
                try:
                    english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                    tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                    
                    if english_terms:
                        UserConsent.create_consent(representative, english_terms, request)
                    if tagalog_terms:
                        UserConsent.create_consent(representative, tagalog_terms, request)
                except Exception as e:
                    logger.error(f"Error creating user consent: {e}")
            
            # Clear OTP session data
            request.session.pop('otp_verified', None)
            request.session.pop('verified_phone', None)
            request.session.pop('email_otp_verified', None)
            request.session.pop('verified_email', None)
            
            # Set session flag for successful registration instead of message
            # This prevents the message from bleeding into login page
            request.session['registration_success'] = True
            request.session['registration_type'] = 'family'
            
            return redirect('login_page')
        else:
            # Don't add a generic error message - the form will display specific field errors
            logger.debug(f"Form validation errors: {form.errors}")
            pass
    else:
        form = FamilyRegistrationForm()

    # Get all barangays for the dropdown
    barangays = Barangay.objects.all()
    
    return render(request, 'register.html', {
        'form': form,
        'barangays': barangays,
        'registration_type': 'family'
    })


def register_member(request):
    """Para sa family member registration (join existing family)"""
    if request.method == 'POST':
        form = FamilyMemberRegistrationForm(request.POST)
        
        # Check if OTP has been verified for both phone and email
        otp_verified = request.POST.get('otp_verified') == 'true'
        verified_phone = request.session.get('verified_phone')
        form_phone = request.POST.get('phone')
        
        email_otp_verified = request.POST.get('email_otp_verified') == 'true'
        verified_email = request.session.get('verified_email')
        form_email = request.POST.get('email')
        
        if not otp_verified or verified_phone != form_phone:
            messages.error(request, "Please verify your phone number first.")
            return render(request, 'register_member.html', {
                'form': form,
                'registration_type': 'member'
            })
        
        if not email_otp_verified or verified_email != form_email:
            messages.error(request, "Please verify your email address first.")
            return render(request, 'register_member.html', {
                'form': form,
                'registration_type': 'member'
            })
        
        if form.is_valid():
            # Check terms acceptance
            if not form.cleaned_data.get('accept_terms'):
                messages.error(request, "You must accept the Terms and Conditions to register.")
                return render(request, 'register_member.html', {
                    'form': form,
                    'registration_type': 'member'
                })
            
            # Both OTP verified, proceed with registration
            user = form.save()
            
            # Create consent records for both English and Tagalog terms
            try:
                english_terms = TermsAndConditions.objects.filter(language='english', is_active=True).first()
                tagalog_terms = TermsAndConditions.objects.filter(language='tagalog', is_active=True).first()
                
                if english_terms:
                    UserConsent.create_consent(user, english_terms, request)
                if tagalog_terms:
                    UserConsent.create_consent(user, tagalog_terms, request)
            except Exception as e:
                logger.error(f"Error creating user consent: {e}")
            
            # Clear OTP session data
            request.session.pop('otp_verified', None)
            request.session.pop('verified_phone', None)
            request.session.pop('email_otp_verified', None)
            request.session.pop('verified_email', None)
            
            # Set session flag for successful registration instead of message
            request.session['registration_success'] = True
            request.session['registration_type'] = 'member'
            
            return redirect('login_page')
        else:
            # Don't add a generic error message - the form will display specific field errors
            pass
    else:
        form = FamilyMemberRegistrationForm()

    return render(request, 'register_member.html', {
        'form': form,
        'registration_type': 'member'
    })
