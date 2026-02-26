# PII Data Masking Utilities
from config import settings


def mask_cnic(cnic: str) -> str:
    """Mask CNIC number: 1234567890123 -> 12*********23"""
    if not cnic or len(cnic) < 4:
        return cnic
    return f"{cnic[:2]}{'*' * 9}{cnic[-2:]}"


def mask_phone(phone: str) -> str:
    """Mask phone number: 03123456789 -> 03*******89"""
    if not phone or len(phone) < 4:
        return phone
    return f"{phone[:2]}{'*' * 7}{phone[-2:]}"


def should_mask_for_role(role: str) -> bool:
    """Check if data should be masked for this role"""
    if not settings.ENABLE_PII_MASKING:
        return False
    if role == "admin":
        return False
    return role in settings.PII_MASKING_ROLES


def apply_pii_masking(data: dict, role: str) -> dict:
    """Apply PII masking to dictionary"""
    if not should_mask_for_role(role):
        return data
    
    masked = data.copy()
    
    # Mask CNIC fields
    if 'cnic' in masked:
        masked['cnic'] = mask_cnic(str(masked['cnic']))
    if 'cnic_number' in masked:
        masked['cnic_number'] = mask_cnic(str(masked['cnic_number']))
    if 'user_cnic' in masked:
        masked['user_cnic'] = mask_cnic(str(masked['user_cnic']))
    
    # Mask phone fields
    if 'phone' in masked:
        masked['phone'] = mask_phone(str(masked['phone']))
    if 'contact_number' in masked:
        masked['contact_number'] = mask_phone(str(masked['contact_number']))
    
    return masked
