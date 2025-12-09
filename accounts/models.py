from django.db import models
import uuid
import string
import random
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.conf import settings
from django.core.files.storage import default_storage

# Import Google Drive storage if enabled
if getattr(settings, 'USE_GOOGLE_DRIVE', False):
    from eko.google_drive_storage import GoogleDriveStorage
    google_drive_storage = GoogleDriveStorage()
else:
    google_drive_storage = None

# ---------- UTILS ----------
def generate_family_code(length=12):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=length))


# ---------- LOGIN SECURITY ----------
class LoginAttempt(models.Model):
    """Track login attempts for security monitoring"""
    username = models.CharField(max_length=150, blank=True)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField()
    user_agent = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['username', 'timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt for {self.username} at {self.timestamp}"


# ---------- BARANGAY ----------
class Barangay(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ---------- FAMILY ----------
class Family(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family_code = models.CharField(max_length=12, unique=True, default=generate_family_code)
    family_name = models.CharField(max_length=100, help_text="Family surname or family identifier")
    
    # Address and location information
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, help_text="House No. and Street")
    city = models.CharField(max_length=100, default="San Pedro City")
    
    # Family representative (the one who registered the family)
    representative_name = models.CharField(max_length=100, help_text="Name of family member who registered")
    representative_phone = models.CharField(max_length=20, unique=True)
    
    # Status and approval workflow
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Family statistics
    total_members = models.IntegerField(default=0)
    total_family_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Families"
        ordering = ['-total_family_points', 'family_name']
    
    def __str__(self):
        return f"{self.family_name} Family ({self.family_code})"
    
    def update_member_count(self):
        """Update the total members count"""
        self.total_members = self.members.filter(is_active=True).count()
        self.save(update_fields=['total_members'])
    
    def update_family_points(self):
        """Update total family points from all active members"""
        total = self.members.filter(is_active=True).aggregate(
            total=models.Sum('total_points')
        )['total'] or 0
        self.total_family_points = total
        self.save(update_fields=['total_family_points'])
    
    def get_family_members(self):
        """Get all active family members"""
        return self.members.filter(is_active=True).order_by('created_at')
    
    def can_add_members(self):
        """Check if family is approved and can add new members"""
        return self.status == 'approved'



# ---------- CUSTOM USER MANAGER ----------
class CustomUserManager(BaseUserManager):
    def create_user(self, username, first_name=None, last_name=None, full_name=None, phone=None, email=None, family=None, family_code=None, password=None, referred_by_code=None, **extra_fields):
        """
        Create a regular user. Must be linked to an approved family.
        Either provide family object or family_code to link to existing family.
        Supports both new first_name/last_name fields and legacy full_name field.
        """
        if not phone:
            raise ValueError("Users must have a phone number")
        if not username:
            raise ValueError("Users must have a username")
        
        # Normalize email if provided
        if email:
            email = self.normalize_email(email)
        
        # Handle name fields - support both old and new formats
        if first_name and last_name:
            pass  # Use provided first_name and last_name
        elif full_name:
            # Split full_name into first_name and last_name for backward compatibility
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
        else:
            raise ValueError("Users must have either first_name and last_name, or full_name")
        
        # Handle family linking
        if family:
            family_obj = family
        elif family_code:
            try:
                family_obj = Family.objects.get(family_code=family_code, status='approved')
            except Family.DoesNotExist:
                raise ValueError("Invalid family code or family not approved")
        else:
            raise ValueError("Must provide either family object or family_code")

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            family=family_obj,
            referred_by_code=referred_by_code,  # Set the referral code
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        # Update family member count
        family_obj.update_member_count()
        
        return user

    def create_family_representative(self, username, first_name=None, last_name=None, full_name=None, phone=None, email=None, family_name=None, barangay=None, address=None, city=None, password=None, referred_by_code=None, **extra_fields):
        """
        Create a family and its first representative user.
        This is used when registering a new family.
        Supports both new first_name/last_name fields and legacy full_name field.
        """
        if not phone:
            raise ValueError("Representative must have a phone number")
        if not email:
            raise ValueError("Representative must have an email address")
        if not username:
            raise ValueError("Representative must have a username")
        if not family_name:
            raise ValueError("Family name is required")
        if not barangay:
            raise ValueError("Barangay is required")
        if not address:
            raise ValueError("Address is required")

        # Handle name fields - support both old and new formats
        if first_name and last_name:
            full_name_for_family = f"{first_name} {last_name}"
        elif full_name:
            # Split full_name into first_name and last_name for backward compatibility
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            full_name_for_family = full_name
        else:
            raise ValueError("Representative must have either first_name and last_name, or full_name")

        # Create or get barangay
        if isinstance(barangay, str):
            barangay_obj, _ = Barangay.objects.get_or_create(name=barangay)
        else:
            barangay_obj = barangay

        # Create the family first
        family = Family.objects.create(
            family_name=family_name,
            barangay=barangay_obj,
            address=address,
            city=city or "San Pedro City",
            representative_name=full_name_for_family,
            representative_phone=phone,
            status='pending'  # Family starts as pending approval
        )

        # Create the representative user
        extra_fields.setdefault('is_family_representative', True)
        
        # Normalize email if provided
        if email:
            email = self.normalize_email(email)
        
        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            family=family,
            referred_by_code=referred_by_code,  # Set the referral code
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        # Update family member count
        family.update_member_count()
        
        return user

    def create_superuser(self, username, first_name=None, last_name=None, full_name=None, phone=None, email=None, password=None, **extra_fields):
        """
        Create a superuser without family requirement.
        Supports both new first_name/last_name fields and legacy full_name field.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 'approved')

        # Set default email if not provided
        if not email:
            email = f"{username}@admin.local"
        
        # Normalize email
        email = self.normalize_email(email)

        # Handle name fields - support both old and new formats
        if first_name and last_name:
            full_name_for_family = f"{first_name} {last_name}"
        elif full_name:
            # Split full_name into first_name and last_name for backward compatibility
            name_parts = full_name.strip().split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ''
            full_name_for_family = full_name
        else:
            raise ValueError("Superuser must have either first_name and last_name, or full_name")

        # Create a special admin family for superusers
        admin_family, created = Family.objects.get_or_create(
            family_code='ADMIN000000',
            defaults={
                'family_name': 'System Administrators',
                'barangay': Barangay.objects.get_or_create(name='Admin')[0],
                'address': 'System Address',
                'city': 'System',
                'representative_name': full_name_for_family,
                'representative_phone': phone,
                'status': 'approved'
            }
        )

        user = self.model(
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            family=admin_family,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        
        return user


# ---------- USERS ----------
class Users(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    ROLE_CHOICES = [
        ('member', 'Family Member'),
        ('representative', 'Family Representative'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    
    # Separate first and last name fields
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    
    # Keep full_name for backward compatibility (will be auto-populated)
    full_name = models.CharField(max_length=100, blank=True)
    
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True, help_text="Email address for verification and notifications")
    
    # Link to family (replaces individual family_code, barangay, address)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    
    # User-specific information
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    
    # Role within the family
    is_family_representative = models.BooleanField(default=False, help_text="Is this user the family representative?")
    
    # Referral system
    referral_code = models.CharField(max_length=8, unique=True, blank=True, null=True, help_text="Unique code that others can use to get referral bonus")
    referred_by_code = models.CharField(max_length=8, blank=True, null=True, help_text="Code of the user who referred this user")
    referral_bonus_awarded = models.BooleanField(default=False, help_text="Whether referral bonus has been awarded")
    
    # Points and activity
    total_points = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Approval workflow
    approved_by = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']  # email is optional for backward compatibility

    class Meta:
        ordering = ['-total_points', 'full_name']
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.full_name} ({self.family.family_name} Family)"
    
    def save(self, *args, **kwargs):
        """Override save to update full_name, generate referral code, and update family points"""
        # Auto-populate full_name from first_name and last_name
        if self.first_name and self.last_name:
            self.full_name = f"{self.first_name} {self.last_name}"
        
        # Generate referral code if not set
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        
        is_new = self.pk is None
        old_points = 0
        
        if not is_new:
            try:
                old_user = Users.objects.get(pk=self.pk)
                old_points = old_user.total_points
            except Users.DoesNotExist:
                old_points = 0
        
        super().save(*args, **kwargs)
        
        # Award referral bonus if this is a new user with a referral code
        if is_new and self.referred_by_code and not self.referral_bonus_awarded:
            self.award_referral_bonus()
        
        # Update family points if points changed
        if is_new or old_points != self.total_points:
            self.family.update_family_points()
    
    def generate_referral_code(self):
        """Generate a unique referral code for this user"""
        import string
        import random
        
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Users.objects.filter(referral_code=code).exists():
                return code
    
    def award_referral_bonus(self):
        """Award referral bonus to both the new user and the referrer"""
        if self.referred_by_code and not self.referral_bonus_awarded:
            try:
                # Find the user who referred this user
                referrer = Users.objects.get(referral_code=self.referred_by_code, status='approved')
                
                # Award 10 points to the new user
                self.total_points += 10
                self.referral_bonus_awarded = True
                
                # Award 10 points to the referrer
                referrer.total_points += 10
                referrer.save()
                
                # Create point transactions for tracking
                # Import PointsTransaction here to avoid circular import
                from accounts.models import PointsTransaction
                
                # Transaction for new user
                PointsTransaction.objects.create(
                    user=self,
                    transaction_type='earned',
                    points_amount=10,
                    description=f'Referral bonus for using code: {self.referred_by_code}',
                    reference_id=referrer.id
                )
                
                # Transaction for referrer
                PointsTransaction.objects.create(
                    user=referrer,
                    transaction_type='earned',
                    points_amount=10,
                    description=f'Referral bonus for referring: {self.full_name}',
                    reference_id=self.id
                )
                
                self.save(update_fields=['total_points', 'referral_bonus_awarded'])
                
            except Users.DoesNotExist:
                # Invalid referral code, but don't raise error
                pass
    
    def get_family_code(self):
        """Get the family code (convenience method)"""
        return self.family.family_code
    
    def get_barangay(self):
        """Get the barangay (convenience method)"""
        return self.family.barangay
    
    def get_address(self):
        """Get the full address (convenience method)"""
        return f"{self.family.address}, {self.family.city}"
    
    def can_access_system(self):
        """Check if user can access the system (both user and family must be approved)"""
        return self.status == 'approved' and self.family.status == 'approved' and self.is_active
    
    def get_family_members(self):
        """Get other family members"""
        return self.family.members.exclude(id=self.id).filter(is_active=True)
    
    def get_family_rank(self):
        """Get user's rank within the family by points"""
        return self.family.members.filter(
            total_points__gt=self.total_points,
            is_active=True
        ).count() + 1


# ---------- POINTS TRANSACTION ----------
class PointsTransaction(models.Model):
    TRANSACTION_CHOICES = (
        ('earned', 'Earned'),
        ('redeemed', 'Redeemed'),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    points_amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    reference_id = models.UUIDField(null=True, blank=True)
    processed_by = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)


# ---------- REWARD CATEGORY ----------
class RewardCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ---------- REWARD ----------
class Reward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(RewardCategory, on_delete=models.SET_NULL, null=True, blank=True)
    points_required = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    description = models.TextField(null=True, blank=True)
    
    # Image field - storage backend will be determined by settings
    image = models.ImageField(upload_to='reward_images/', null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def image_url(self):
        """Get the image URL for WEB DISPLAY (dashboard) - uses CDN with better CORS"""
        if self.image:
            if getattr(settings, 'USE_GOOGLE_DRIVE', False):
                # Check if this is a Google Drive file ID or a local file path
                if self.image.name.startswith('reward_images/'):
                    # This is a local file path
                    try:
                        from django.conf import settings as django_settings
                        return f"{django_settings.MEDIA_URL}{self.image.name}"
                    except:
                        return None
                else:
                    # This is a Google Drive file ID
                    try:
                        # Simple check: if it's a long alphanumeric string, treat as Google Drive ID
                        if len(self.image.name) > 15 and self.image.name.replace('_', '').replace('-', '').isalnum():
                            # Use Google CDN URL - has Access-Control-Allow-Origin: * header
                            # Works best for web embedding in dashboards
                            return f"https://lh3.googleusercontent.com/d/{self.image.name}"
                        else:
                            # Local file path
                            from django.conf import settings as django_settings
                            return f"{django_settings.MEDIA_URL}{self.image.name}"
                    except Exception as e:
                        return None
            else:
                # For local storage, use the normal URL
                try:
                    return self.image.url
                except:
                    return None
        return None
    
    @property
    def image_url_for_email(self):
        """Get the image URL for EMAIL DISPLAY - uses CDN format with better CORS support"""
        if self.image:
            if getattr(settings, 'USE_GOOGLE_DRIVE', False):
                # Check if this is a Google Drive file ID or a local file path
                if self.image.name.startswith('reward_images/'):
                    # This is a local file path
                    try:
                        from django.conf import settings as django_settings
                        return f"{django_settings.MEDIA_URL}{self.image.name}"
                    except:
                        return None
                else:
                    # This is a Google Drive file ID
                    try:
                        # Simple check: if it's a long alphanumeric string, treat as Google Drive ID
                        if len(self.image.name) > 15 and self.image.name.replace('_', '').replace('-', '').isalnum():
                            # Use CDN URL - has Access-Control-Allow-Origin: * header
                            # Testing: CDN might work better than direct view for emails
                            return f"https://lh3.googleusercontent.com/d/{self.image.name}"
                        else:
                            # Local file path
                            from django.conf import settings as django_settings
                            return f"{django_settings.MEDIA_URL}{self.image.name}"
                    except Exception as e:
                        return None
            else:
                # For local storage, use the normal URL
                try:
                    return self.image.url
                except:
                    return None
        return None
    
    def __str__(self):
        return self.name
    
    def add_stock(self, quantity, admin_user=None, notes=""):
        """Add stock and record history"""
        previous_stock = self.stock
        self.stock += quantity
        self.save()
        
        # Create history record
        RewardHistory.objects.create(
            reward=self,
            action='stock_added',
            stock_change=quantity,
            previous_stock=previous_stock,
            new_stock=self.stock,
            admin_user=admin_user,
            notes=notes
        )
        
        return self.stock
    
    def remove_stock(self, quantity, admin_user=None, notes="", user=None, redemption=None):
        """Remove stock and record history"""
        if quantity > self.stock:
            raise ValueError(f"Cannot remove {quantity} items. Only {self.stock} available.")
        
        previous_stock = self.stock
        self.stock -= quantity
        self.save()
        
        # Determine action type and who performed it
        if redemption:
            action = 'stock_redeemed'
            actor_user = user
            admin_actor = None
        else:
            action = 'stock_removed'
            actor_user = None
            admin_actor = admin_user
        
        # Create history record
        RewardHistory.objects.create(
            reward=self,
            action=action,
            stock_change=-quantity,
            previous_stock=previous_stock,
            new_stock=self.stock,
            admin_user=admin_actor,
            user=actor_user,
            redemption=redemption,
            notes=notes
        )
        
        return self.stock
    
    def create_history(self, action, admin_user=None, notes=""):
        """Create a general history record for non-stock actions"""
        RewardHistory.objects.create(
            reward=self,
            action=action,
            admin_user=admin_user,
            notes=notes,
            previous_stock=self.stock,
            new_stock=self.stock
        )


# ---------- REWARD HISTORY ----------
class RewardHistory(models.Model):
    ACTION_CHOICES = [
        ('created', 'Reward Created'),
        ('updated', 'Reward Updated'),
        ('deleted', 'Reward Deleted'),
        ('stock_added', 'Stock Added'),
        ('stock_removed', 'Stock Removed'),
        ('stock_redeemed', 'Stock Redeemed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Stock changes
    stock_change = models.IntegerField(default=0, help_text="Positive for additions, negative for reductions")
    previous_stock = models.IntegerField(default=0)
    new_stock = models.IntegerField(default=0)
    
    # Who performed the action
    admin_user = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='reward_actions')
    user = models.ForeignKey('Users', on_delete=models.SET_NULL, null=True, blank=True, related_name='reward_interactions')
    
    # Additional details
    notes = models.TextField(blank=True, help_text="Additional notes about the action")
    redemption = models.ForeignKey('Redemption', on_delete=models.CASCADE, null=True, blank=True)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Reward History"
        verbose_name_plural = "Reward Histories"
    
    def __str__(self):
        if self.action == 'stock_redeemed':
            return f"{self.reward.name} - {self.get_action_display()} by {self.user.full_name if self.user else 'Unknown'}"
        return f"{self.reward.name} - {self.get_action_display()} by {self.admin_user.full_name if self.admin_user else 'System'}"


# ---------- REDEMPTION ----------
class Redemption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, help_text="Number of items redeemed")
    points_used = models.DecimalField(max_digits=10, decimal_places=2)
    requested_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='requested_redemptions')
    approved_by = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True)
    redemption_date = models.DateTimeField(default=timezone.now)
    claim_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        """Override save to reduce stock when redemption is created"""
        # For UUID fields, we need to check if the object exists in database
        is_new = self._state.adding
        
        if is_new:
            # Check if enough stock is available
            if self.quantity > self.reward.stock:
                raise ValueError(f"Insufficient stock. Requested: {self.quantity}, Available: {self.reward.stock}")
            
            # Save first to get the redemption ID
            super().save(*args, **kwargs)
            
            # Reduce stock and create history
            self.reward.remove_stock(
                quantity=self.quantity,
                user=self.user,
                redemption=self,
                notes=f"Redeemed by {self.user.full_name}"
            )
        else:
            super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.reward.name} (x{self.quantity})"


# ---------- GARBAGE SCHEDULE ----------
class GarbageSchedule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    barangay = models.ForeignKey(Barangay, on_delete=models.CASCADE)
    day = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    waste_types = models.JSONField()
    notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


# ---------- WASTE TYPE ----------
class WasteType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    points_per_kg = models.DecimalField(max_digits=10, decimal_places=2, help_text="Equivalent points per kilogram")

    def __str__(self):
        return f"{self.name} ({self.points_per_kg} pts/kg)"


# ---------- WASTE TRANSACTION ----------
class WasteTransaction(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    waste_type = models.ForeignKey(WasteType, on_delete=models.CASCADE)
    waste_kg = models.FloatField()
    total_points = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for analytics
    processed_by = models.ForeignKey('cenro.AdminUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_transactions')
    barangay = models.ForeignKey(Barangay, on_delete=models.SET_NULL, null=True, blank=True, related_name='waste_transactions')
    transaction_date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['barangay']),
            models.Index(fields=['waste_type']),
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.waste_type.name} ({self.total_points} pts)"
    
    def save(self, *args, **kwargs):
        # Auto-populate barangay from user's family if not set
        if not self.barangay and self.user.family and self.user.family.barangay:
            self.barangay = self.user.family.barangay
        super().save(*args, **kwargs)


# ---------- NOTIFICATION ----------
class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('waste', 'Waste Transaction'),
        ('redeem', 'Reward Redemption'),
        ('learning', 'Learning Video'),
        ('game', 'Game Points'),
        ('other', 'Other'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=10, choices=NOTIF_TYPE_CHOICES)
    message = models.TextField()
    points = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reward_name = models.CharField(max_length=255, null=True, blank=True)
    video_title = models.CharField(max_length=255, null=True, blank=True)  # For learning notifications
    game_score = models.IntegerField(null=True, blank=True)  # For game notifications
    is_read = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True, help_text='When the notification was viewed by the user')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'viewed_at', '-created_at'], name='notif_user_viewed_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.get_type_display()}"

    @property
    def is_viewed(self):
        """Check if notification has been viewed"""
        return self.viewed_at is not None

    def mark_as_viewed(self):
        """Mark notification as viewed"""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])

    def time_since(self):
        """Return human-readable time since notification was created"""
        from django.utils.timesince import timesince
        return timesince(self.created_at)


class AdminActionHistory(models.Model):
    """
    Model to track all admin actions for audit trail
    NOTE: This model has been moved to cenro.models to keep admin-related models together
    Keeping this placeholder for backward compatibility during migration
    """
    class Meta:
        managed = False  # This model is managed by cenro app
        db_table = 'cenro_adminactionhistory'


# ---------- USER CONSENT ----------
class UserConsent(models.Model):
    """
    Model to track user acceptance of Terms and Conditions
    Required for legal compliance and audit trail
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'Users',
        on_delete=models.CASCADE,
        related_name='consents',
        help_text="User who accepted the terms"
    )
    terms_version = models.ForeignKey(
        'cenro.TermsAndConditions',
        on_delete=models.PROTECT,  # Prevent deletion of accepted terms
        related_name='user_consents',
        help_text="Version of terms that was accepted"
    )
    
    # Acceptance details
    accepted_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(
        help_text="IP address from which consent was given"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser user agent for audit trail"
    )
    
    class Meta:
        ordering = ['-accepted_at']
        verbose_name = 'User Consent'
        verbose_name_plural = 'User Consents'
        indexes = [
            models.Index(fields=['user', '-accepted_at']),
            models.Index(fields=['terms_version', '-accepted_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} accepted {self.terms_version.title} v{self.terms_version.version} on {self.accepted_at}"
    
    @classmethod
    def create_consent(cls, user, terms_version, request):
        """
        Create a new consent record
        
        Args:
            user: Users instance
            terms_version: TermsAndConditions instance
            request: HttpRequest object to extract IP and user agent
        """
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            terms_version=terms_version,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def user_has_accepted_latest(cls, user, language='english'):
        """
        Check if user has accepted the latest active terms for a language
        
        Args:
            user: Users instance
            language: 'english' or 'tagalog'
        
        Returns:
            Boolean indicating if user has accepted latest terms
        """
        from cenro.models import TermsAndConditions
        
        # Get the latest active terms for this language
        latest_terms = TermsAndConditions.get_active_terms(language)
        if not latest_terms:
            # No active terms, so no consent required
            return True
        
        # Check if user has consent for this exact version
        return cls.objects.filter(
            user=user,
            terms_version=latest_terms
        ).exists()

