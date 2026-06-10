import json
import logging
from django.utils import timezone
from .models import KYBDocument, ClientApplication
from agents.utils import agent_chat

logger = logging.getLogger(__name__)

def verify_kyb_document(document: KYBDocument):
    """
    Simulates OCR extraction and verification via AI.
    In Phase 1, we use agent_chat to extract structured data from a simulated context,
    as direct file attachments require google-cloud-vision or Gemini Vision endpoints.
    """
    app = document.application
    
    # In a full implementation, we would extract text from document.file.path
    # using Google Cloud Vision or send it to Gemini Vision.
    # For Phase 1, we simulate the extraction prompt.
    
    prompt = f"""
    You are an expert KYC/KYB compliance officer (Veritas).
    Your task is to review a {document.get_document_type_display()} for the company:
    Name: {app.company_legal_name}
    Registration: {app.registration_number}
    Director: {app.director_name}
    
    Analyze the document for authenticity and match the extracted data against the company profile.
    
    Return a JSON response strictly in this format:
    {{
        "verified": true/false,
        "extracted_data": {{"key": "value"}},
        "reason": "Explanation if rejected, or empty if verified"
    }}
    """
    
    try:
        # We use a coder model because it's good at JSON output
        response_text = agent_chat(
            messages=[{"role": "user", "content": prompt}],
            model="qwen2.5-coder" 
        )
        
        # Clean up possible markdown formatting
        if response_text.startswith("```json"):
            response_text = response_text.strip("`").replace("json\n", "", 1)
        
        result = json.loads(response_text)
        
        document.ai_verification = result.get('verified', False)
        document.ocr_extracted_data = result.get('extracted_data', {})
        
        if document.ai_verification:
            document.status = 'verified'
            document.verified_at = timezone.now()
        else:
            document.status = 'rejected'
            document.rejection_reason = result.get('reason', 'AI Verification failed')
            
        document.save()
        return True
    
    except Exception as e:
        logger.error(f"Error in KYB document verification for doc {document.id}: {e}")
        document.status = 'pending'
        document.save()
        return False
