#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Authentication configuration for SwanLab-Server
"""

import os


class AuthConfig:
    """Authentication configuration settings"""

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800))  # 7 days

    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

    # GitHub OAuth Configuration
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:22224/api/v1/auth/github/callback')

    # Google OAuth Configuration (for future use)
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:22224/api/v1/auth/google/callback')

    # Session Configuration
    SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'session-secret-key-change-this')

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Password Policy
    MIN_PASSWORD_LENGTH = int(os.getenv('MIN_PASSWORD_LENGTH', 8))
    REQUIRE_SPECIAL_CHAR = os.getenv('REQUIRE_SPECIAL_CHAR', 'false').lower() == 'true'

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if cls.JWT_SECRET_KEY == 'your-secret-key-change-this-in-production':
            print("WARNING: Using default JWT_SECRET_KEY. Please set a secure key in production!")

        if cls.GITHUB_CLIENT_ID and not cls.GITHUB_CLIENT_SECRET:
            raise ValueError("GITHUB_CLIENT_SECRET must be set if GITHUB_CLIENT_ID is provided")

        return True
