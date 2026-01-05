"""
CRM Cron Jobs
Scheduled tasks for the CRM application.
"""

from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from requests.exceptions import RequestException


def log_crm_heartbeat():
    """
    Logs a heartbeat message to verify CRM is alive.
    Optionally queries the GraphQL hello field to verify endpoint responsiveness.
    """
    TIMESTAMP = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Optionally query GraphQL responsiveness
    graphql_status = ""
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Execute query and get response
        response = client.execute(gql("{hello}"))
        
        # Check if we got the expected data
        if response and response.get("hello"):
            graphql_status = " - GraphQL is responsive"
        else:
            graphql_status = " - GraphQL did not return expected data"
    
    except TransportQueryError as e:
        graphql_status = f" - GraphQL query error: {str(e)}"
    except RequestException as e:
        graphql_status = f" - GraphQL request failed: {str(e)}"
    except Exception as e:
        graphql_status = f" - Unexpected error: {str(e)}"
    
    # Log the heartbeat
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(f"{TIMESTAMP} CRM is alive{graphql_status}\n")


def update_low_stock():
    """
    Queries and updates products with low stock (stock < 10).
    Logs the updated products to a file.
    """
    TIMESTAMP = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        # Define the mutation
        mutation = gql("""
            mutation UpdateLowStockProducts {
                updateLowStockProducts {
                    success
                    message
                    count
                    updatedProducts {
                        id
                        name
                        stock
                    }
                }
            }
        """)
        
        # Execute the mutation
        result = client.execute(mutation)
        
        # Log the results
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            mutation_data = result.get("updateLowStockProducts", {})
            success = mutation_data.get("success", False)
            message = mutation_data.get("message", "No message")
            updated_products = mutation_data.get("updatedProducts", [])
            
            if success and updated_products:
                log_file.write(f"[{TIMESTAMP}] {message}\n")
                for product in updated_products:
                    log_file.write(
                        f"[{TIMESTAMP}] Updated Product ID {product['id']} - "
                        f"{product['name']} to stock {product['stock']}\n"
                    )
            else:
                log_file.write(f"[{TIMESTAMP}] {message}\n")
        
        print("Low stock update completed successfully.")
    
    except TransportQueryError as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(f"[{TIMESTAMP}] GraphQL query error: {str(e)}\n")
        print(f"Low stock update failed: {e}")
    
    except RequestException as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(f"[{TIMESTAMP}] Request failed: {str(e)}\n")
        print(f"Low stock update failed: {e}")
    
    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as log_file:
            log_file.write(f"[{TIMESTAMP}] Unexpected error: {str(e)}\n")
        print(f"Low stock update failed: {e}")