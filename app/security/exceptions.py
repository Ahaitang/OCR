"""
Security-related exceptions
"""
class SecurityError(Exception):
    """Security violation error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

class InvalidInputError(ValidationError):
    """Invalid input data"""
    pass