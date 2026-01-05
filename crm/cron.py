from datetime import datetime
import requests

def log_crm_heartbeat():
    TIMESTAMP = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # optionally query GraphQL reponsiveness
    graphql_status = ""
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            params={"query": "{hello}"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("data", {}).get("hello"):
                graphql_status = "GraphQL is responsive"
            else:
                graphql_status = "GraphQL did not return expected data"
        else:
            graphql_status = f"GraphQL returned status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        graphql_status = f"GraphQL request failed: {e}"
    except Exception as e:
        graphql_status = f"Unexpected error: {e}"
    
    with open("/tmp/crm_heartbeat_log.txt", "a") as log_file:
        log_file.write(f"{TIMESTAMP} CRM is alive{graphql_status}\n")