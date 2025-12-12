"""
Shared constants used across the application.
"""

# Regex pattern for validating course codes
# Course codes should be 2-20 characters, containing only uppercase letters, numbers, and hyphens
COURSE_CODE_PATTERN = r"^[A-Z0-9\-]{2,20}$"
