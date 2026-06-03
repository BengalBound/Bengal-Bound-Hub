import factory
from django.contrib.auth import get_user_model
from hub.models import BusinessInstance, BusinessEmployee
from agents.models import AgentCatalog

User = get_user_model()

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('email',)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password('testpass123')
        if create:
            self.save()


class BusinessInstanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessInstance

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Test Business {n}')
    slug = factory.Sequence(lambda n: f'test-business-{n}')
    business_type = 'business'
    installation_type = 'cloud'


class BusinessEmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BusinessEmployee

    business = factory.SubFactory(BusinessInstanceFactory)
    user = factory.SubFactory(UserFactory)
    name = factory.LazyAttribute(lambda o: o.user.username if o.user else 'Test Employee')
    role = 'ceo'


class AgentCatalogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AgentCatalog
        django_get_or_create = ('slug',)

    name = 'Crux'
    slug = 'crux'
    role = 'AI Assistant'
    description = 'Test Agent'
    system_prompt = 'You are a test agent.'
    category = 'sales'
