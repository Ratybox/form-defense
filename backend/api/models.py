from django.db import models
import hashlib


class FormEntry(models.Model):
    """Modèle simple pour stocker les données du formulaire"""
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    password_hash = models.CharField(max_length=64)  # SHA-256 produit 64 caractères hex
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"
    
    @staticmethod
    def hash_password(password):
        """Hash un mot de passe en SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
