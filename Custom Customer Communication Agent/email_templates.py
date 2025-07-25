"""
Email Templates Module for Customer Communication Agent

This module contains all email templates used for different stages of the loan process.
Each template is organized by stage and includes both subject and body content with 
proper HTML formatting and responsive design.

Stages:
1. Application - Initial application submission confirmation
2. Document Submission - Document upload instructions
3. Verification - Document verification in progress
4. Document Approval - Documents successfully verified
5. Approval - Loan confirmation and approval
6. Loan Letter - Loan letter ready for collection
"""

def get_email_templates():
    """
    Returns a dictionary containing all email templates organized by stage.
    
    Each template includes:
    - subject: Email subject line with dynamic content
    - body: Full HTML email body with styling and dynamic content
    
    Returns:
        dict: Email templates organized by stage name
    """
    
    email_templates = {
        "application": {
            "subject": "Your Home Loan Application Has Been Submitted – Welcome to Global Trust Bank",
            "description": "Welcome email confirming successful application submission with AI assistant introduction",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Loan Application Submitted</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #2c5530;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 20px;
        }
        .highlight {
            background-color: #e8f4fd;
            padding: 15px;
            border-left: 4px solid #1f4e79;
            margin: 20px 0;
        }
        .contact-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
        .button {
            display: inline-block;
            background-color: #1f4e79;
            color: white;
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="title">Home Loan Application Submitted Successfully</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>Kala Divan</strong>,</p>
            
            <p>We're happy to let you know that your Home Loan application has been <strong>successfully submitted</strong> to Global Trust Bank.</p>
            
            <div class="highlight">
                <p><strong>🤖 AI-Powered Assistance</strong></p>
                <p>To make your journey smoother, we've introduced an AI-powered Home Loan Assistant that will guide you through the remaining steps of your application — completely online and at your convenience.</p>
            </div>
            
            <p><strong>What's next?</strong> Our AI assistant will ask you to upload the necessary documents and complete the verification process.</p>
            
            <div class="contact-info">
                <p><strong>📋 Your Registered Contact Details:</strong></p>
                <p>📧 <strong>Email ID:</strong> mallickindali@example.net</p>
                <p>📱 <strong>Contact No:</strong> 5634216073</p>
                
            </div>
            
            <p>Please keep an eye out for the next email with the document upload instructions.</p>
            
            <p>We're committed to helping you move one step closer to your dream home. 🏠</p>
        </div>
        
        <div class="footer">
            <p>Warm regards,<br>
            <strong>Global Trust Bank – Home Loans Team</strong></p>
            <p>📞 Customer Service: 1800-XXX-XXXX | 📧 support@globaltrustbank.com</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        },
        
        "document_submission": {
            "subject": "Next Step: Document Upload Required – Global Trust Bank Home Loan",
            "description": "Document upload instructions with checklist and requirements",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Upload Required</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #d68910;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 20px;
        }
        .highlight {
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #d68910;
            margin: 20px 0;
        }
        .document-list {
            background-color: #e8f4fd;
            padding: 20px;
            border-left: 4px solid #1f4e79;
            margin: 20px 0;
        }
        .document-list ul {
            margin: 0;
            padding-left: 20px;
        }
        .document-list li {
            margin: 8px 0;
        }
        .contact-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .important {
            background-color: #f8d7da;
            padding: 15px;
            border-left: 4px solid #dc3545;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
        .button {
            display: inline-block;
            background-color: #d68910;
            color: white;
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="title">📄 Document Upload Required</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>Kala Divan</strong>,</p>
            
            <p>Great news! Your home loan application is moving forward to the <strong>document upload stage</strong>.</p>
            
            <div class="highlight">
                <p><strong>📋 Current Status:</strong></p>
                
                <p>📊 <strong>Stage:</strong> Document Upload & Verification</p>
                <p>⏱️ <strong>Action Required:</strong> Please upload the required documents</p>
            </div>
            
            <p>To proceed with your application, we need you to upload the following documents through our secure online portal:</p>
            
            <div class="document-list">
                <p><strong>📁 Required Documents Checklist:</strong></p>
                <ul>
                    <li>📄 <strong>Identity Proof:</strong> Aadhaar Card (front & back) or Passport</li>
                    <li>📄 <strong>Address Proof:</strong> Utility bill, Bank statement, or Rental agreement</li>
                    <li>📄 <strong>Income Proof:</strong> Last 3 months' salary slips</li>
                    <li>📄 <strong>Bank Statements:</strong> Last 6 months (salary account)</li>
                    <li>📄 <strong>PAN Card:</strong> Clear photo/scan</li>
                    <li>📄 <strong>Employment Certificate:</strong> From current employer</li>
                    <li>📄 <strong>Property Documents:</strong> Sale deed/Agreement (if applicable)</li>
                </ul>
            </div>
            
            <div class="contact-info">
                <p><strong>📞 Your Registered Contact Details:</strong></p>
                <p>📧 <strong>Email ID:</strong> mallickindali@example.net</p>
                <p>📱 <strong>Contact No:</strong> 5634216073</p>
            </div>
            
            <div class="important">
                <p><strong>⚠️ Important Instructions:</strong></p>
                <ul>
                    <li>📸 Ensure all documents are clear, legible, and in high resolution</li>
                    <li>🔒 Upload documents only through our official secure portal</li>
                    <li>📋 Double-check that all required documents are included</li>
                    <li>⏰ Complete the upload within <strong>7 days</strong> to avoid delays</li>
                    <li>📁 Accepted formats: PDF, JPG, PNG (max 5MB per file)</li>
                </ul>
            </div>
            
            <p><strong>What's Next?</strong></p>
            <p>Once you've uploaded all required documents, our verification team will review them within <strong>2-3 business days</strong>. You'll receive a confirmation email once the review is complete.</p>
            
            <p>If you have any questions or need assistance with document upload, please don't hesitate to contact our support team.</p>
            
            <p>We're here to make your home loan journey as smooth as possible! 🏠</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>
            <strong>Document Processing Team</strong><br>
            Global Trust Bank – Home Loans Division</p>
            <p>📞 Customer Service: 1800-XXX-XXXX | 📧 homeloan.support@globaltrustbank.com</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        },
        
        "verification": {
            "subject": "Thank You for Submitting Your Documents – Verification in Progress",
            "description": "Acknowledgment of document submission with verification status update",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Verification in Progress</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #17a2b8;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 20px;
        }
        .highlight {
            background-color: #d1ecf1;
            padding: 20px;
            border-left: 4px solid #17a2b8;
            margin: 20px 0;
        }
        .next-steps {
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
        .contact-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="title">🔍 Document Verification in Progress</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>Kala Divan</strong>,</p>
            
            <p>Thank you for submitting your documents for your Home Loan application with Global Trust Bank.</p>
            
            <p>We've successfully received all the files and have initiated the verification process. Our team is currently reviewing the documents to ensure everything is in order and meets the required criteria.</p>
            
            <div class="highlight">
                <p><strong>📋 What Happens Next?</strong></p>
                <ul>
                    <li>Our system will verify the authenticity and completeness of the documents submitted</li>
                    <li>If anything additional is required, our AI assistant or support team will reach out to you</li>
                    <li>Once verification is completed, you'll be notified about the approval status and next steps</li>
                </ul>
            </div>
            
            <div class="contact-info">
                <p><strong>📞 Your Registered Contact Details:</strong></p>
                
                <p>📧 <strong>Email ID:</strong> mallickindali@example.net</p>
                <p>📱 <strong>Contact No:</strong> 5634216073</p>
            </div>
            
            <p>We appreciate your prompt response and cooperation throughout this process.</p>
            
            <p>If you have any questions in the meantime, feel free to continue interacting with the AI assistant or get in touch with our loan support team.</p>
        </div>
        
        <div class="footer">
            <p>Warm regards,<br>
            <strong>Global Trust Bank – Home Loans Team</strong></p>
            <p>📞 Customer Service: 1800-XXX-XXXX | 📧 support@globaltrustbank.com</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        },
        
        "document_approval": {
            "subject": "Your Documents Have Been Successfully Verified",
            "description": "Confirmation that all documents have been verified and approved",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Documents Successfully Verified</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #28a745;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 20px;
        }
        .highlight {
            background-color: #d4edda;
            padding: 20px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
        }
        .contact-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="title">✅ Documents Successfully Verified</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>{customer_name}</strong>,</p>
            
            <p>We're pleased to inform you that all the documents you submitted for your Home Loan application with Global Trust Bank have been successfully verified.</p>
            
            <div class="highlight">
                <p><strong>📈 Application Progress Update:</strong></p>
                <p>Your application is now moving to the next stage in the approval process. Our credit and risk assessment teams will now review your eligibility and finalize the loan offer based on the verified details.</p>
            </div>
            
            <div class="contact-info">
                <p><strong>📋 Your Application Details:</strong></p>
                <p>🆔 <strong>Customer ID:</strong> {customer_id}</p>
                <p>📧 <strong>Email ID:</strong> {customer_email}</p>
                <p>📱 <strong>Contact No:</strong> {customer_mobile}</p>
            </div>
            
            <p>We appreciate your continued cooperation and are excited to help you move closer to your new home.</p>
        </div>
        
        <div class="footer">
            <p>Warm regards,<br>
            <strong>Global Trust Bank – Home Loans Team</strong></p>
            <p>📞 Customer Service: 1800-XXX-XXXX | 📧 support@globaltrustbank.com</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        },
        
        "approval": {
            "subject": "Great News – Your Home Loan is Confirmed!",
            "description": "Final loan approval confirmation with celebration and next steps",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Home Loan Confirmed</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #28a745;
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .content {
            margin-bottom: 20px;
        }
        .celebration {
            text-align: center;
            font-size: 48px;
            margin: 20px 0;
        }
        .highlight {
            background-color: #d4edda;
            padding: 20px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
        }
        .next-steps {
            background-color: #fff3cd;
            padding: 20px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
        .contact-info {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="celebration">🎉🏠🎉</div>
            <div class="title">Great News – Your Home Loan is Confirmed!</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>{customer_name}</strong>,</p>
            
            <p>We're delighted to inform you that your Home Loan application with Global Trust Bank has been <strong>successfully confirmed</strong> after a thorough review of your documents and eligibility.</p>
            
            <div class="highlight">
                <p><strong>🎯 Loan Confirmation Details:</strong></p>
                <p>Your loan is now moving to the final processing stages, and we will soon share your sanction details, EMI schedule, and disbursement information.</p>
                <p><strong>This is a major milestone — you're just a few steps away from owning your dream home!</strong></p>
            </div>
            
            <div class="next-steps">
                <p><strong>📋 What's Next:</strong></p>
                <ul>
                    <li>✅ We will send you a detailed sanction letter</li>
                    <li>✅ You'll receive your loan offer summary, including approved amount, tenure, and interest rate</li>
                    <li>✅ You'll be guided to sign the loan agreement</li>
                    <li>✅ Post-signing, your loan will be disbursed as per the agreed schedule</li>
                </ul>
            </div>
            
            <div class="contact-info">
                <p><strong>📞 Your Application Details:</strong></p>
                <p>🆔 <strong>Customer ID:</strong> {customer_id}</p>
                <p>📧 <strong>Email ID:</strong> {customer_email}</p>
                <p>📱 <strong>Contact No:</strong> {customer_mobile}</p>
            </div>
            
            <p>For any questions in the meantime, feel free to connect with our AI assistant or reach out to our Home Loan Support Team.</p>
            
            <p><strong>We truly appreciate your trust in us.</strong></p>
        </div>
        
        <div class="footer">
            <p>Warm regards,<br>
            <strong>Global Trust Bank – Home Loans Team</strong></p>
            <p>📞 Customer Service: 1800-XXX-XXXX | 📧 support@globaltrustbank.com</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        },
        
        "loan_application_number": {
            "subject": "Your Loan Application Has Been Successfully Submitted – Global Trust Bank",
            "description": "Confirmation email with loan application number after successful submission",
            "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loan Application Submitted</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .title {
            color: #28a745;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .application-number {
            background-color: #e8f5e8;
            padding: 20px;
            border-left: 4px solid #28a745;
            margin: 20px 0;
            text-align: center;
        }
        .application-number h3 {
            margin: 0;
            color: #1f4e79;
            font-size: 18px;
        }
        .application-number .number {
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
            margin: 10px 0;
        }
        .next-steps {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .support-section {
            background-color: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
            <div class="title">✅ Application Successfully Submitted</div>
        </div>
        
        <div class="content">
            <p>Dear Kala Divan,</p>
            
            <p>We're pleased to inform you that your loan application has been successfully submitted to Global Trust Bank.</p>
            
            <div class="application-number">
                <h3>📌 Loan Application Number</h3>
                <div class="number">GTB-8475-9821-6643-1023</div>
                <p><small>(Please keep this number safe for your records and future reference.)</small></p>
            </div>
            
            <p>All the documents you submitted have been successfully verified. Our team will now proceed to evaluate your loan eligibility based on the information provided.</p>
            
            <div class="next-steps">
                <p><strong>📋 Next Steps:</strong></p>
                <ul>
                    <li>✅ Document verification completed</li>
                    <li>🔄 Loan eligibility evaluation in progress</li>
                    <li>📧 You will receive further communication shortly</li>
                    <li>📞 Our team may contact you if additional information is needed</li>
                </ul>
            </div>
            
            <p>You will receive further communication from us shortly with the outcome of your eligibility check and the next steps.</p>
            
            <div class="support-section">
                <p><strong>🔒 Need Help?</strong></p>
                <p>For any assistance or to track your application, you can contact us at <strong>support@globaltrustbank.in</strong> or call us at <strong>1800-123-4567</strong>.</p>
            </div>
            
            <p>Thank you for choosing Global Trust Bank as your trusted loan partner. We're committed to making your journey smooth and transparent.</p>
            
            <p>Warm regards,<br>
            <strong>Global Trust Bank – Loan Services Team</strong></p>
        </div>
        
        <div class="footer">
            <p>📞 Customer Service: 1800-123-4567 | 📧 support@globaltrustbank.in</p>
            <p><strong>Disclaimer:</strong> Loans are subject to approval at the sole discretion of Global Trust Bank. Please read the terms & conditions in the application form carefully.</p>
            <p><small>This is an automated message. Please do not reply to this email.</small></p>
        </div>
    </div>
</body>
</html>"""
        }
    }
    
    return email_templates

def get_stage_template(stage: str) -> dict:
    """
    Get email template for a specific stage.
    
    Args:
        stage (str): The stage name (application, document_submission, etc.)
    
    Returns:
        dict: Template with subject and body, or default template if stage not found
    """
    templates = get_email_templates()
    
    if stage in templates:
        return templates[stage]
    
    # Default template for unknown stages
    return {
        "subject": "Update from Global Trust Bank",
        "description": "Generic update template for unrecognized stages",
        "body": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Loan Update</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            color: #1f4e79;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🏛️ Global Trust Bank</div>
        </div>
        
        <div class="content">
            <p>Dear <strong>{customer_name}</strong>,</p>
            <p>We have an update regarding your loan application (Customer ID: <strong>{customer_id}</strong>).</p>
            <p>Please contact us for more details.</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>
            <strong>Global Trust Bank</strong></p>
            <p>📞 1800-XXX-XXXX | 📧 support@globaltrustbank.com</p>
        </div>
    </div>
</body>
</html>"""
    }

def format_template(template: dict, customer_data: dict) -> dict:
    """
    Format email template with customer data.
    
    Args:
        template (dict): Email template with subject and body
        customer_data (dict): Customer information including name, email, mobile, customer_id
    
    Returns:
        dict: Formatted template with customer data inserted
    """
    try:
        # Extract customer data with fallbacks
        customer_name = customer_data.get("name", f"Customer {customer_data.get('customer_id', 'N/A')}")
        customer_email = customer_data.get("email", "your-email@example.com")
        customer_mobile = customer_data.get("mobile", "Your registered mobile number")
        customer_id = customer_data.get("customer_id", "N/A")
        
        # Format subject and body with customer data
        formatted_subject = template["subject"].format(
            customer_name=customer_name,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_mobile=customer_mobile
        )
        
        formatted_body = template["body"].format(
            customer_name=customer_name,
            customer_id=customer_id,
            customer_email=customer_email,
            customer_mobile=customer_mobile
        )
        
        return {
            "subject": formatted_subject,
            "body": formatted_body,
            "description": template.get("description", "")
        }
        
    except KeyError as e:
        print(f"❌ Error formatting template: Missing key {e}")
        return template
    except Exception as e:
        print(f"❌ Error formatting template: {str(e)}")
        return template

def get_all_stage_names() -> list:
    """
    Get list of all available stage names.
    
    Returns:
        list: List of stage names
    """
    return list(get_email_templates().keys())

def get_template_summary() -> dict:
    """
    Get summary of all templates with their descriptions.
    
    Returns:
        dict: Summary of all templates with stage names and descriptions
    """
    templates = get_email_templates()
    summary = {}
    
    for stage, template in templates.items():
        summary[stage] = {
            "subject": template["subject"],
            "description": template.get("description", "No description available")
        }
    
    return summary

def get_stage_mapping():
    """
    Returns a dictionary mapping various stage inputs to template names.
    
    This makes it easy for agents to convert user input (like "1", "stage 1", "application")
    to the correct template name.
    
    Returns:
        dict: Mapping of stage inputs to template names
    """
    return {
        # Stage numbers
        "1": "application",
        "2": "document_submission",
        "3": "verification", 
        "4": "document_approval",
        "5": "approval",
        "6": "loan_application_number",
        # Stage names
        "application": "application",
        "document_submission": "document_submission", 
        "verification": "verification",
        "document_approval": "document_approval",
        "approval": "approval",
        "loan_application_number": "loan_application_number",
        # Stage with word "stage"
        "stage 1": "application",
        "stage 2": "document_submission",
        "stage 3": "verification", 
        "stage 4": "document_approval",
        "stage 5": "approval",
        "stage 6": "loan_application_number",
        # Alternative names
        "application stage": "application",
        "document submission stage": "document_submission",
        "verification stage": "verification",
        "document approval stage": "document_approval",
        "approval stage": "approval",
        "loan application number stage": "loan_application_number"
    }

def map_stage_to_template(stage: str) -> str:
    """
    Maps a stage input to the correct template name.
    
    Args:
        stage (str): User input for stage (e.g., "1", "stage 1", "application")
    
    Returns:
        str: Template name or the original stage if no mapping found
    """
    if not stage:
        return None
    
    stage_mapping = get_stage_mapping()
    stage_key = str(stage).lower().strip()
    
    return stage_mapping.get(stage_key, stage_key)

if __name__ == "__main__":
    print("📧 Email Templates Module")
    print("=" * 50)
    
    # Display template summary
    summary = get_template_summary()
    for stage, info in summary.items():
        print(f"\n📄 Stage: {stage.upper()}")
        print(f"   Subject: {info['subject']}")
        print(f"   Description: {info['description']}")
    
    print(f"\n✅ Total templates available: {len(summary)}")
    print("📋 Available stages:", ", ".join(get_all_stage_names()))
