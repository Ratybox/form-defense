from django.db import models
import hashlib


class FormEntry(models.Model):
    """Simple model to store form entry data"""
    name = models.CharField(max_length=255, verbose_name="Name")
    email = models.EmailField(verbose_name="Email")
    message = models.TextField(verbose_name="Message")
    password_hash = models.CharField(max_length=64, verbose_name="Password Hash (SHA-256)")  # SHA-256 produces 64 hex characters
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Form Entry"
        verbose_name_plural = "Form Entries"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.email} ({self.created_at.strftime('%m/%d/%Y')})"
    
    @staticmethod
    def hash_password(password):
        """Hash a password using SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def get_message_length(self):
        """Returns the message length"""
        return len(self.message) if self.message else 0
    
    def get_word_count(self):
        """Returns the word count in the message"""
        return len(self.message.split()) if self.message else 0
    
    def get_password_hash_preview(self, length=8):
        """Returns a preview of the hash (first and last characters)"""
        if self.password_hash and len(self.password_hash) > length * 2:
            return f"{self.password_hash[:length]}...{self.password_hash[-length:]}"
        return self.password_hash or ""
    
    def is_recent(self, hours=24):
        """Checks if the entry is recent (within the last X hours)"""
        from django.utils import timezone
        from datetime import timedelta
        if self.created_at:
            return timezone.now() - self.created_at < timedelta(hours=hours)
        return False
