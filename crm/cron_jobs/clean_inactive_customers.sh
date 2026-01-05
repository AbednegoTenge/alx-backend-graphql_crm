#!/bin/bash

# This script cleans up inactive customers from the CRM database.

PROJECT_ROOT="/home/abednego-tenge/Desktop/Projects/alx_backend_graphql"
MANAGE_PY="$PROJECT_ROOT/manage.py"

cd "$PROJECT_ROOT" || { echo "Project root not found! Exiting."; exit 1; }

// activate the virtual environment
source "$PROJECT_ROOT/venv/bin/activate" || { echo "Failed to activate virtual environment! Exiting."; exit 1; }

# Define the cutoff date for inactivity
one_year_ago = timezone.now() - timedelta(days=365)

DELETED_COUNT = $(python "$MANAGE_PY" shell -c <<EOF
    from django.utils import timezone
    from crm.models import Customer
    from datetime import timedelta

    # Customers with no orders in the last year
    inactive_customers = Customer.objects.exclude(order__created_at__gte=one_year_ago).distinct()

    # customers with no orders at all
    no_order_customers = Customer.objects.filter(order__isnull=True)

    all_inactive = (inactive_customers | no_order_customers).distinct()

    count = all_inactive.count()
    all_inactive.delete()
    print(count)
EOF
)

# Log the result with timestamp
TIMESTAMP = $(date +"%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Deleted $DELETED_COUNT inactive customers(no orders since $one_year_ago)." >> "/tmp/customer_cleanup_log.txt"