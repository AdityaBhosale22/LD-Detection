from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserAccount


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = UserAccount
		fields = ["id", "email", "first_name", "last_name", "role"]


class RegisterSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True)

	class Meta:
		model = UserAccount
		fields = ["email", "first_name", "last_name", "role", "password"]

	def validate_password(self, password):
		validate_password(password, UserAccount(email=self.initial_data.get("email", "")))
		return password

	def create(self, validated_data):
		password = validated_data.pop("password")
		return UserAccount.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField()

	def validate(self, attrs):
		user = authenticate(username=attrs["email"], password=attrs["password"])
		if user is None:
			raise serializers.ValidationError("Invalid email or password.")
		attrs["user"] = user
		return attrs
