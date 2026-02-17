from rest_framework import serializers
from .models import FormEntry


class FormEntrySerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = FormEntry
        fields = ['id', 'name', 'email', 'message', 'password', 'password_hash', 'created_at']
        read_only_fields = ['id', 'password_hash', 'created_at']
    
    def create(self, validated_data):
        # Récupérer le mot de passe et le hasher
        password = validated_data.pop('password')
        password_hash = FormEntry.hash_password(password)
        
        # Créer l'entrée avec le hash
        validated_data['password_hash'] = password_hash
        return super().create(validated_data)
