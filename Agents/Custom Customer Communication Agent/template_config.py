"""
Template Configuration Module

This module provides configuration and metadata for all email templates,
including stage mappings, template descriptions, and template management utilities.
"""

# Stage number to stage name mapping
STAGE_MAPPING = {
    1: "application",
    2: "document_submission",
    3: "verification",
    4: "document_approval",
    5: "approval",
    6: "loan_application_number"
}

# Stage descriptions for easy reference
STAGE_DESCRIPTIONS = {
    "application": {
        "stage_number": 1,
        "name": "Application Submission",
        "description": "Initial application submission confirmation with AI assistant introduction",
        "key_features": [
            "Welcome message",
            "AI assistant introduction", 
            "Next steps information",
            "Contact details confirmation"
        ],
        "primary_color": "#2c5530",
        "icon": "🏠"
    },
    "document_submission": {
        "stage_number": 2,
        "name": "Document Upload Required",
        "description": "Document upload instructions with checklist and requirements",
        "key_features": [
            "Document checklist",
            "Upload instructions",
            "Timeline requirements",
            "Format specifications"
        ],
        "primary_color": "#d68910",
        "icon": "📄"
    },
    "verification": {
        "stage_number": 3,
        "name": "Document Verification",
        "description": "Acknowledgment of document submission with verification status update",
        "key_features": [
            "Confirmation of receipt",
            "Verification process explanation",
            "Timeline expectations",
            "Support contact information"
        ],
        "primary_color": "#17a2b8",
        "icon": "🔍"
    },
    "document_approval": {
        "stage_number": 4,
        "name": "Documents Verified",
        "description": "Confirmation that all documents have been verified and approved",
        "key_features": [
            "Verification confirmation",
            "Progress update",
            "Next steps preview",
            "Application timeline"
        ],
        "primary_color": "#28a745",
        "icon": "✅"
    },
    "approval": {
        "stage_number": 5,
        "name": "Loan Confirmed",
        "description": "Final loan approval confirmation with celebration and next steps",
        "key_features": [
            "Loan confirmation celebration",
            "Sanction letter preview",
            "Final steps outline",
            "Support contact details"
        ],
        "primary_color": "#28a745",
        "icon": "🎉"
    },
    "loan_application_number": {
        "stage_number": 6,
        "name": "Loan Application Number Issued",
        "description": "Confirmation email with loan application number after successful submission and document verification",
        "key_features": [
            "Application number generation",
            "Submission confirmation",
            "Next steps information",
            "Support contact details"
        ],
        "primary_color": "#28a745",
        "icon": "�"
    }
}

# Template validation rules
TEMPLATE_VALIDATION_RULES = {
    "required_placeholders": [
        "{customer_name}",
        "{customer_id}",
        "{customer_email}",
        "{customer_mobile}"
    ],
    "max_subject_length": 150,
    "required_html_elements": [
        "<!DOCTYPE html>",
        "<html",
        "<head>",
        "<body>",
        "<style>"
    ],
    "required_css_classes": [
        ".container",
        ".header",
        ".logo",
        ".footer"
    ]
}

# Email formatting configurations
EMAIL_CONFIG = {
    "max_width": "600px",
    "font_family": "Arial, sans-serif",
    "line_height": "1.6",
    "background_color": "#f4f4f4",
    "container_background": "#ffffff",
    "default_padding": "20px",
    "border_radius": "10px",
    "box_shadow": "0 0 10px rgba(0,0,0,0.1)"
}

# Bank branding configuration
BANK_BRANDING = {
    "name": "Global Trust Bank",
    "logo_emoji": "🏛️",
    "primary_color": "#1f4e79",
    "secondary_color": "#2c5530",
    "customer_service_phone": "1800-XXX-XXXX",
    "support_email": "support@globaltrustbank.com",
    "home_loan_email": "homeloan.support@globaltrustbank.com"
}

def get_stage_by_number(stage_number: int) -> str:
    """
    Get stage name by stage number.
    
    Args:
        stage_number (int): Stage number (1-6)
    
    Returns:
        str: Stage name or None if invalid
    """
    return STAGE_MAPPING.get(stage_number)

def get_stage_number(stage_name: str) -> int:
    """
    Get stage number by stage name.
    
    Args:
        stage_name (str): Stage name
    
    Returns:
        int: Stage number or None if not found
    """
    for number, name in STAGE_MAPPING.items():
        if name == stage_name:
            return number
    return None

def get_stage_info(stage_name: str) -> dict:
    """
    Get detailed information about a stage.
    
    Args:
        stage_name (str): Stage name
    
    Returns:
        dict: Stage information including description, features, colors, etc.
    """
    return STAGE_DESCRIPTIONS.get(stage_name, {})

def get_all_stages() -> list:
    """
    Get list of all available stage names.
    
    Returns:
        list: List of all stage names
    """
    return list(STAGE_MAPPING.values())

def get_stages_summary() -> dict:
    """
    Get a summary of all stages with their key information.
    
    Returns:
        dict: Summary of all stages
    """
    summary = {}
    for stage_name in get_all_stages():
        info = get_stage_info(stage_name)
        summary[stage_name] = {
            "stage_number": info.get("stage_number"),
            "name": info.get("name"),
            "description": info.get("description"),
            "icon": info.get("icon")
        }
    return summary

def validate_stage(stage_name: str) -> bool:
    """
    Validate if a stage name is valid.
    
    Args:
        stage_name (str): Stage name to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    return stage_name in STAGE_DESCRIPTIONS

def get_next_stage(current_stage: str) -> str:
    """
    Get the next stage in the loan process.
    
    Args:
        current_stage (str): Current stage name
    
    Returns:
        str: Next stage name or None if current is the last stage
    """
    current_number = get_stage_number(current_stage)
    if current_number and current_number < 6:
        return get_stage_by_number(current_number + 1)
    return None

def get_previous_stage(current_stage: str) -> str:
    """
    Get the previous stage in the loan process.
    
    Args:
        current_stage (str): Current stage name
    
    Returns:
        str: Previous stage name or None if current is the first stage
    """
    current_number = get_stage_number(current_stage)
    if current_number and current_number > 1:
        return get_stage_by_number(current_number - 1)
    return None

def get_stage_progress_percentage(stage_name: str) -> float:
    """
    Calculate progress percentage for a given stage.
    
    Args:
        stage_name (str): Stage name
    
    Returns:
        float: Progress percentage (0-100)
    """
    stage_number = get_stage_number(stage_name)
    if stage_number:
        return (stage_number / 6) * 100
    return 0.0

if __name__ == "__main__":
    print("📋 Template Configuration Module")
    print("=" * 50)
    
    # Display all stages
    print("\n🎯 Available Stages:")
    stages_summary = get_stages_summary()
    for stage, info in stages_summary.items():
        progress = get_stage_progress_percentage(stage)
        print(f"\n{info['icon']} Stage {info['stage_number']}: {info['name']}")
        print(f"   Key: {stage}")
        print(f"   Description: {info['description']}")
        print(f"   Progress: {progress:.1f}%")
    
    # Display stage mappings
    print(f"\n🔢 Stage Number Mappings:")
    for number, name in STAGE_MAPPING.items():
        print(f"   {number} → {name}")
    
    # Display bank branding
    print(f"\n🏛️ Bank Branding:")
    for key, value in BANK_BRANDING.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Configuration loaded successfully!")
    print(f"📊 Total stages: {len(STAGE_MAPPING)}")
    print(f"🎨 Template validation rules configured")
    print(f"🏦 Bank branding configured")
