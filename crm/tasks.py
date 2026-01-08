from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime
#import requests

@shared_task
def generate_crm_report():
    print("Generating CRM report...")
    # Add logic to generate and save the report
    try:
        transport = RequestsHTTPTransport(
            url="http://localhost:8000/graphql/",
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)
        
        query = gql("""
            query {
                crmreport {
                    totalCustomers
                    totalOrders
                    totalRevenue
                }
            }
        """)
        
        result = client.execute(query)
        report_data = result.get("CRMReport", {})

        customer_count = report_data.get("totalCustomers", 0)
        order_count = report_data.get("totalOrders", 0)
        total_revenue = report_data.get("totalRevenue", 0)

        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/crm_report_log.txt", "a") as log_file:
            log_file.write(f"[{timestamp}] - Report: {customer_count} customers, {order_count} orders, ${total_revenue:.2f} revenue\n")  
    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as log_file:
            log_file.write(f"Error generating CRM report: {str(e)}\n")
        print(f"Error generating CRM report: {e}")
        return "Failed to generate CRM report."
    return "CRM report generated successfully."