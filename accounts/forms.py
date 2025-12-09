from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import date
from .models import Users, Family, Barangay

class FamilyRegistrationForm(forms.ModelForm):
    """Form for registering a new family (family representative registration)"""
    
    # Family information
    family_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter family surname'})
    )
    
    # Representative information - separated name fields
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'First name of representative'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Last name of representative'})
    )
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username'})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Phone number'})
    )
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'placeholder': 'Email address'})
    )
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'Date of Birth'}),
        required=False,
        help_text="Optional: Enter your date of birth"
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + Users.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_gender'})
    )
    
    # Referral system
    referral_code = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter referral code (optional)',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Enter a referral code to get 10 bonus points (optional)"
    )
    
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'})
    )
    
    # Address information
    barangay = forms.ModelChoiceField(
        queryset=Barangay.objects.all(),
        empty_label="Select Barangay"
    )
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'House No. and Street'})
    )
    city = forms.CharField(
        max_length=100,
        initial="San Pedro City",
        widget=forms.TextInput(attrs={'placeholder': 'City'})
    )
    
    # Terms and Conditions acceptance
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'You must accept the Terms and Conditions to register.'
        }
    )
    
    class Meta:
        model = Family
        fields = ['family_name', 'barangay', 'address', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mark required fields
        required_fields = ['family_name', 'first_name', 'last_name', 'username', 'phone', 'email', 'barangay', 'address', 'city', 'password1', 'password2', 'accept_terms']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = True

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Format validation
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 11:
            raise forms.ValidationError("Phone number must be exactly 11 digits.")
        if not phone.startswith('09'):
            raise forms.ValidationError("Phone number must start with 09.")
        
        # Check if phone is already used by any user (exclude rejected)
        if Users.objects.filter(phone=phone).exclude(status='rejected').exists():
            raise forms.ValidationError("This phone number is already registered.")
        # Check if phone is already used as a family representative phone (exclude rejected)
        if Family.objects.filter(representative_phone=phone).exclude(status='rejected').exists():
            raise forms.ValidationError("This phone number is already registered as a family representative.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            # Check if date is in the future
            if dob > today:
                raise forms.ValidationError("Date of birth cannot be in the future.")
            # Check if date is unrealistically old (before 1900)
            if dob.year < 1900:
                raise forms.ValidationError("Please enter a valid date of birth.")
            # Check if person would be older than 150 years
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age > 150:
                raise forms.ValidationError("Please enter a valid date of birth.")
        return dob

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Users.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            referral_code = referral_code.upper().strip()
            # Check if referral code exists and belongs to an approved user
            if not Users.objects.filter(referral_code=referral_code, status='approved').exists():
                raise forms.ValidationError("Invalid referral code.")
        return referral_code

    def clean(self):
        cleaned_data = super().clean()
        
        # Manually call field validation methods for non-model fields
        phone = cleaned_data.get('phone')
        email = cleaned_data.get('email')
        username = cleaned_data.get('username')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        # Validate phone number
        if phone:
            # Check if phone is already used by any user (exclude rejected)
            if Users.objects.filter(phone=phone).exclude(status='rejected').exists():
                raise forms.ValidationError("This phone number is already registered.")
            # Check if phone is already used as a family representative phone (exclude rejected)
            if Family.objects.filter(representative_phone=phone).exclude(status='rejected').exists():
                raise forms.ValidationError("This phone number is already registered as a family representative.")
        
        # Validate email
        if email:
            if Users.objects.filter(email=email).exists():
                raise forms.ValidationError("This email address is already registered.")
        
        # Validate username
        if username:
            if Users.objects.filter(username=username).exists():
                raise forms.ValidationError("This username is already taken.")
        
        # Validate passwords match
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match.")

        # Normalize gender field: convert empty or invalid values to canonical values or None
        gender = cleaned_data.get('gender')
        if gender is None:
            cleaned_data['gender'] = None
        else:
            g = str(gender).strip().lower()
            if g in ['male', 'm']:
                cleaned_data['gender'] = 'male'
            elif g in ['female', 'f']:
                cleaned_data['gender'] = 'female'
            elif g in ['other', 'o']:
                cleaned_data['gender'] = 'other'
            else:
                # Unknown input -> set to None to avoid invalid DB values
                cleaned_data['gender'] = None
        
        return cleaned_data

    def save(self, commit=True):
        """Create both family and representative user"""
        if commit:
            # Use the custom manager method to create family and representative
            user = Users.objects.create_family_representative(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                email=self.cleaned_data['email'],
                family_name=self.cleaned_data['family_name'],
                barangay=self.cleaned_data['barangay'],
                address=self.cleaned_data['address'],
                city=self.cleaned_data['city'],
                password=self.cleaned_data['password1'],
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                gender=self.cleaned_data.get('gender'),
                referred_by_code=self.cleaned_data.get('referral_code')
            )
            return user.family
        return None


class FamilyMemberRegistrationForm(UserCreationForm):
    """Form for registering additional family members"""
    
    # Terms and Conditions acceptance
    accept_terms = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'You must accept the Terms and Conditions to register.'
        }
    )
    
    family_code = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={'placeholder': 'Enter family code'})
    )
    
    # Separated name fields
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Your first name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': 'Your last name'})
    )
    
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': 'Your phone number'})
    )
    
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={'placeholder': 'Your email address'})
    )
    
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=[('', 'Select Gender')] + Users.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_gender'})
    )

    # Referral system
    referral_code = forms.CharField(
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter referral code (optional)',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Enter a referral code to get 10 bonus points (optional)"
    )

    class Meta:
        model = Users
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'family_code', 'date_of_birth', 'gender']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        required_fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'family_code']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = True

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        
        # Format validation
        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        if len(phone) != 11:
            raise forms.ValidationError("Phone number must be exactly 11 digits.")
        if not phone.startswith('09'):
            raise forms.ValidationError("Phone number must start with 09.")
        
        # Exclude rejected users from phone check
        if Users.objects.filter(phone=phone).exclude(status='rejected').exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Exclude rejected users from email check
        if Users.objects.filter(email=email).exclude(status='rejected').exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            # Check if date is in the future
            if dob > today:
                raise forms.ValidationError("Date of birth cannot be in the future.")
            # Check if date is unrealistically old (before 1900)
            if dob.year < 1900:
                raise forms.ValidationError("Please enter a valid date of birth.")
            # Check if person would be older than 150 years
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age > 150:
                raise forms.ValidationError("Please enter a valid date of birth.")
        return dob

    def clean_family_code(self):
        family_code = self.cleaned_data.get('family_code')
        try:
            family = Family.objects.get(family_code=family_code, status='approved')
            return family_code
        except Family.DoesNotExist:
            raise forms.ValidationError("Invalid family code or family not approved.")

    def clean_referral_code(self):
        referral_code = self.cleaned_data.get('referral_code')
        if referral_code:
            referral_code = referral_code.upper().strip()
            # Check if referral code exists and belongs to an approved user
            if not Users.objects.filter(referral_code=referral_code, status='approved').exists():
                raise forms.ValidationError("Invalid referral code.")
        return referral_code

    def save(self, commit=True):
        if commit:
            user = Users.objects.create_user(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                phone=self.cleaned_data['phone'],
                email=self.cleaned_data['email'],
                family_code=self.cleaned_data['family_code'],
                password=self.cleaned_data['password1'],
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                gender=self.cleaned_data.get('gender'),
                referred_by_code=self.cleaned_data.get('referral_code')
            )
            return user
        return None


# Keep this for backward compatibility, but redirect to family-based forms
class UsersSignupForm(FamilyRegistrationForm):
    """Legacy form - redirects to family registration"""
    pass
