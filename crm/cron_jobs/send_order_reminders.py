#!/usr/bin/env python3

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import sys
from datetime import datetime, timedelta

def send_order_reminders():

    # calculate the date 7 days ago from today
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')     

    # configure the GraphQL client
    transport = RequestsHTTPTransport(
        url= "http://localhost:8000/graphql", verify=True, retries=3,
        use_json = True
    )

    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql(
        """
        query GetRecentOrders($orderDateAfter: Date!) {
            orders(orderDate_Gte: $orderDateAfter) {
                id
                orderDate
                customer {
                    email
                }
            }
        }    
    """)

    try:
        results = client.execute(query, variable_values={"orderDateAfter": seven_days_ago})
        
        # get current timestamp
        TIMESTAMP = datetime.now().isoformat()

        # log results to file
        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            orders = results.get("orders", [])

            for order in orders:
                order_id = order.get("id")
                customer_email = order.get("customer", {}).get("email", "N/A") 
                order_date = order.get("orderDate")

                log_entry = f"{TIMESTAMP} - Order ID: {order_id}, Customer Email: {customer_email}, Order Date: {order_date}\n"
                log_file.write(log_entry)
        
        print("Order reminders processed!")
    except Exception as e:
        error_timestamp = datetime.now().isoformat()
        error_message = f"{error_timestamp} - Error occurred: {str(e)}\n"

        with open("/tmp/order_reminders_log.txt", "a") as log_file:
            log_file.write(error_message)
        
        print("An error occurred while processing order reminders.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    send_order_reminders()
    