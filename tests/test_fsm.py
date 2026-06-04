import pytest
from django.urls import reverse
from modules.fsm.models import Job, JobQuote, CustomerSignature
from hub.models import HubPlanConfig

pytestmark = pytest.mark.django_db

def test_fsm_job_creation_and_quote(client, business_instance):
    """Test FSM job creation and quoting flow"""
    # Create the employee profile for the owner
    from hub.models import BusinessEmployee, ModuleCatalog
    employee = BusinessEmployee.objects.create(
        business=business_instance,
        user=business_instance.owner,
        name="Test Technician",
        role="owner"
    )

    client.force_login(business_instance.owner)

    # Enable FSM module for business
    fsm_module, _ = ModuleCatalog.objects.get_or_create(module_id='fsm', defaults={'name': 'Field Service Management', 'category': 'operations'})
    business_instance.modules.create(module=fsm_module, is_active=True)

    # Dashboard should load and be empty initially
    url = reverse('fsm:dashboard', kwargs={'slug': business_instance.slug})
    response = client.get(url)
    assert response.status_code == 200
    assert 'No jobs scheduled for today.' in response.content.decode()

    # Create a job manually for the test
    job = Job.objects.create(
        business=business_instance,
        title="Fix leaking pipe",
        customer_name="John Doe",
        address="123 Test St",
        technician=employee,
        status="scheduled"
    )

    # Now the dashboard should show the job
    response = client.get(url)
    assert response.status_code == 200
    assert 'Fix leaking pipe' in response.content.decode()

    # Access quote builder
    quote_url = reverse('fsm:quote_builder', kwargs={'slug': business_instance.slug, 'job_id': job.id})
    response = client.get(quote_url)
    assert response.status_code == 200
    assert 'Quote Builder: Fix leaking pipe' in response.content.decode()

def test_fsm_signature_capture(client, business_instance):
    from hub.models import BusinessEmployee, ModuleCatalog
    employee = BusinessEmployee.objects.create(
        business=business_instance,
        user=business_instance.owner,
        name="Test Tech",
        role="owner"
    )
    client.force_login(business_instance.owner)
    
    fsm_module, _ = ModuleCatalog.objects.get_or_create(module_id='fsm', defaults={'name': 'Field Service Management', 'category': 'operations'})
    business_instance.modules.create(module=fsm_module, is_active=True)
    
    job = Job.objects.create(
        business=business_instance,
        title="Install Light Fixture",
        customer_name="Jane Smith",
        address="456 Spark Ave",
        technician=employee
    )
    
    sign_url = reverse('fsm:signature_capture', kwargs={'slug': business_instance.slug, 'job_id': job.id})
    
    # Post signature data
    response = client.post(sign_url, {
        'signature_data': 'data:image/png;base64,dummy_signature_data',
        'signed_by_name': 'Jane Smith'
    })
    
    assert response.status_code == 302 # redirect to dashboard
    
    # Job should be completed
    job.refresh_from_db()
    assert job.status == 'completed'
    
    # Signature should exist
    assert hasattr(job, 'signature')
    assert job.signature.signed_by_name == 'Jane Smith'
