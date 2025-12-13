import re
import graphene
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order


# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")


class BulkCustomerInputType(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

# Input type for bulk orders
class BulkOrderInputType(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_id = graphene.ID(required=True)


class ProductType(DjangoObjectType):
    class Meta: 
        model = Product
        fields = ("id", "name", "price", "stock")


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "product", "order_date")

class BulkCustomerError(graphene.ObjectType):
    index = graphene.Int()
    email = graphene.String()
    messages = graphene.String()

# Error object for bulk orders
class BulkOrderError(graphene.ObjectType):
    index = graphene.Int()
    customer_id = graphene.ID()
    product_id = graphene.ID()
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

# Product Mutation
class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False)
    
    product = graphene.Field(ProductType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    @staticmethod
    def validate_price_stock(stock, price):
        if price < 0:
            raise ValidationError("Price cannot be negative.")
        if stock is not None and stock < 0:
            raise ValidationError("Stock cannot be negative.")

    @classmethod
    def mutate(cls, root, info, name, price, stock=None):
        errors = []

        # Validate price and stock
        try:
            cls.validate_price_stock(stock, price)
        except ValidationError as ve:
            errors.append(str(ve))

        if errors:
            return CreateProduct(
                success=False,
                message="Product creation failed due to validation errors.",
                errors=errors
            )

        try:
            product = Product.objects.create(name=name, price=price, stock=stock)
            return CreateProduct(
                product=product,
                success=True,
                message="Product created successfully.",
                errors=None
            )
        except IntegrityError as ie:
            return CreateProduct(
                success=False,
                message="Product creation failed due to database error.",
                errors=[str(ie)]
            )


# Order Mutation
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_id = graphene.ID(required=True)

    order = graphene.Field(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(graphene.String)

    @classmethod
    def mutate(cls, root, info, customer_id, product_id):
        errors = []
        if not product_id:
            errors.append("At least one product must be specified.")

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            errors.append("Customer does not exist.")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            errors.append("Product does not exist.")

        if errors:
            return CreateOrder(
                success=False,
                message="Order creation failed due to validation errors.",
                errors=errors
            )

        try:
            order = Order.objects.create(customer=customer, product=product)
            total_amount = product.price  # Assuming quantity is always 1 for simplicity
            return CreateOrder(
                order=order,
                success=True,
                message="Order created successfully.",
                errors=None
            )
        except IntegrityError as ie:
            return CreateOrder(
                success=False,
                message="Order creation failed due to database error.",
                errors=[str(ie)]
            )


# Bulk order mutation
class CreateBulkOrders(graphene.Mutation):
    class Arguments:
        orders = graphene.List(BulkOrderInputType, required=True)

    created_orders = graphene.List(OrderType)
    success = graphene.Boolean()
    message = graphene.String()
    errors = graphene.List(BulkOrderError)

    @classmethod
    def mutate(cls, root, info, orders):
        created_orders = []
        errors = []

        valid_orders = []

        for index, data in enumerate(orders):
            try:
                customer = Customer.objects.get(id=data.customer_id)
            except Customer.DoesNotExist:
                errors.append(BulkOrderError(
                    index=index,
                    customer_id=data.customer_id,
                    product_id=data.product_id,
                    messages="Customer does not exist."
                ))
                continue

            try:
                product = Product.objects.get(id=data.product_id)
            except Product.DoesNotExist:
                errors.append(BulkOrderError(
                    index=index,
                    customer_id=data.customer_id,
                    product_id=data.product_id,
                    messages="Product does not exist."
                ))
                continue

            # If both exist, prepare for creation
            valid_orders.append(Order(customer=customer, product=product))

        # Bulk create valid orders
        if valid_orders:
            try:
                with transaction.atomic():
                    created_orders = Order.objects.bulk_create(valid_orders)
            except IntegrityError as ie:
                # If DB error occurs, mark all valid orders as failed
                for idx, o in enumerate(valid_orders):
                    errors.append(BulkOrderError(
                        index=idx,
                        customer_id=o.customer.id,
                        product_id=o.product.id,
                        messages=f"Database error: {str(ie)}"
                    ))
                created_orders = []

        return cls(
            created_orders=created_orders,
            success=len(errors) == 0,
            message=f"Created {len(created_orders)} orders.",
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
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    bulk_create_orders = CreateBulkOrders.Field()


# GraphQL Schema
schema = graphene.Schema(query=Query, mutation=Mutation)
