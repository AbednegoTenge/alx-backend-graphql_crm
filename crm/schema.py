import re
import graphene
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from graphene_django import DjangoObjectType
from .models import Customer


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class BulkCustomerInputType(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class BulkCustomerError(graphene.ObjectType):
    index = graphene.Int()
    email = graphene.String()
    messages = graphene.String()


# Single Customer Mutation
class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    @staticmethod
    def validate_phone(phone):
        """ Valid formats: +1234567890, 123-456-7890 """
        pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
        if not re.match(pattern, phone):
            raise ValidationError("Invalid phone number format. Use +1234567890 or 123-456-7890.")

    @classmethod
    def mutate(cls, root, info, **kwargs):
        name = kwargs.get("name")
        email = kwargs.get("email")
        phone = kwargs.get("phone", None)
        errors = []

        # Validate email uniqueness
        if Customer.objects.filter(email=email).exists():
            errors.append("This email already exists.")

        # Validate phone if provided
        if phone:
            try:
                cls.validate_phone(phone)
            except ValidationError as ve:
                errors.append(str(ve))

        if errors:
            return CreateCustomer(
                success=False,
                message="Customer creation failed due to validation errors.",
                errors=errors
            )

        try:
            customer = Customer.objects.create(name=name, email=email, phone=phone)
            return CreateCustomer(
                customer=customer,
                success=True,
                message="Customer created successfully.",
                errors=None
            )
        except IntegrityError as ie:
            return CreateCustomer(
                success=False,
                message="Customer creation failed due to database error.",
                errors=[str(ie)]
            )


# Bulk Customer Mutation
class CreateBulkCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(BulkCustomerInputType, required=True)

    created_customers = graphene.List(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(BulkCustomerError)

    @staticmethod
    def validate_phone(phone):
        pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
        if not re.match(pattern, phone):
            raise ValidationError("Invalid phone number format. Use +1234567890 or 123-456-7890.")

    @classmethod
    def mutate(cls, root, info, customers):
        errors = []
        valid_objects = []
        created_customers = []

        # Collect existing emails to prevent duplicates
        existing_emails = set(Customer.objects.filter(
            email__in=[c.email for c in customers]
        ).values_list("email", flat=True))

        for index, data in enumerate(customers):
            try:
                if data.email in existing_emails:
                    raise ValidationError("This email already exists.")
                if data.phone:
                    cls.validate_phone(data.phone)
                customer = Customer(
                    name=data.name,
                    email=data.email,
                    phone=data.phone
                )
                valid_objects.append(customer)
                existing_emails.add(data.email)
            except ValidationError as ve:
                errors.append(BulkCustomerError(
                    index=index,
                    email=data.email,
                    messages=str(ve)
                ))

        # Bulk create valid customers
        if valid_objects:
            with transaction.atomic():
                created_customers = Customer.objects.bulk_create(valid_objects)

        return CreateBulkCustomers(
            created_customers=created_customers,
            success=len(errors) == 0,
            message=f"Created {len(created_customers)} customers.",
            errors=errors if errors else None
        )


# GraphQL Query
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)

    def resolve_customers(root, info):
        return Customer.objects.all()


# GraphQL Mutation
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = CreateBulkCustomers.Field()


# GraphQL Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
