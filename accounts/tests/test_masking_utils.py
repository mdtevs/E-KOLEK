"""
Unit tests for masking utility functions
Tests email and phone number masking to ensure proper privacy protection
"""

import unittest
from accounts.masking_utils import mask_email, mask_phone, mask_contact


class TestMaskingUtils(unittest.TestCase):
    """Test cases for masking utility functions"""
    
    def test_mask_email_long_username(self):
        """Test masking email with long username"""
        result = mask_email("acerorenz3000@gmail.com")
        self.assertEqual(result, "ac***@gmail.com")
        
    def test_mask_email_medium_username(self):
        """Test masking email with medium length username"""
        result = mask_email("johnsmith@example.org")
        self.assertEqual(result, "joh***@example.org")
        
    def test_mask_email_short_username(self):
        """Test masking email with short username"""
        result = mask_email("ab@test.com")
        self.assertEqual(result, "ab***@test.com")
        
    def test_mask_email_very_short_username(self):
        """Test masking email with single character username"""
        result = mask_email("a@test.com")
        self.assertEqual(result, "a***@test.com")
        
    def test_mask_email_empty(self):
        """Test masking empty email"""
        result = mask_email("")
        self.assertEqual(result, "")
        
    def test_mask_email_none(self):
        """Test masking None email"""
        result = mask_email(None)
        self.assertEqual(result, "")
        
    def test_mask_email_invalid(self):
        """Test masking invalid email (no @)"""
        result = mask_email("notanemail")
        self.assertEqual(result, "notanemail")
        
    def test_mask_phone_standard(self):
        """Test masking standard Philippine phone number"""
        result = mask_phone("09056352991")
        self.assertEqual(result, "********991")
        
    def test_mask_phone_without_zero(self):
        """Test masking phone number without leading zero"""
        result = mask_phone("9056352991")
        self.assertEqual(result, "*******991")
        
    def test_mask_phone_with_country_code(self):
        """Test masking phone with country code"""
        result = mask_phone("+639056352991")
        self.assertEqual(result, "**********991")
        
    def test_mask_phone_short(self):
        """Test masking short phone number"""
        result = mask_phone("123")
        self.assertEqual(result, "**3")
        
    def test_mask_phone_very_short(self):
        """Test masking very short phone number"""
        result = mask_phone("12")
        self.assertEqual(result, "*2")
        
    def test_mask_phone_empty(self):
        """Test masking empty phone"""
        result = mask_phone("")
        self.assertEqual(result, "")
        
    def test_mask_phone_none(self):
        """Test masking None phone"""
        result = mask_phone(None)
        self.assertEqual(result, "")
        
    def test_mask_contact_email(self):
        """Test unified mask_contact with email method"""
        result = mask_contact("acerorenz3000@gmail.com", "email")
        self.assertEqual(result, "ac***@gmail.com")
        
    def test_mask_contact_sms(self):
        """Test unified mask_contact with sms method"""
        result = mask_contact("09056352991", "sms")
        self.assertEqual(result, "********991")
        
    def test_mask_contact_phone(self):
        """Test unified mask_contact with phone method"""
        result = mask_contact("09056352991", "phone")
        self.assertEqual(result, "********991")


if __name__ == '__main__':
    unittest.main()
