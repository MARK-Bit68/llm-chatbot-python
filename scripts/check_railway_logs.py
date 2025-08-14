#!/usr/bin/env python3
"""
Railway Logs Checker
Uses Railway API to check deployment logs and status
"""

import os
import requests
import json
from datetime import datetime

# Get Railway token from secrets file
def load_railway_token():
    secrets_file = ".streamlit/secrets.toml"
    try:
        with open(secrets_file, 'r') as f:
            for line in f:
                if line.strip().startswith("RAILWAY_API_KEY"):
                    return line.split("=")[1].strip()
    except FileNotFoundError:
        print("❌ Secrets file not found")
    return None

def get_railway_projects(token):
    """Get all Railway projects"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = """
    query {
        projects {
            edges {
                node {
                    id
                    name
                    description
                    services {
                        edges {
                            node {
                                id
                                name
                                deployments(first: 5) {
                                    edges {
                                        node {
                                            id
                                            status
                                            createdAt
                                            url
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    """
    
    response = requests.post(
        "https://railway.app/api/graphql",
        headers=headers,
        json={"query": query}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error fetching projects: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_deployment_logs(token, deployment_id):
    """Get logs for a specific deployment"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = f"""
    query {{
        deployment(id: "{deployment_id}") {{
            id
            status
            createdAt
            staticUrl
            buildLogs
            deployLogs
        }}
    }}
    """
    
    response = requests.post(
        "https://railway.app/api/graphql",
        headers=headers,
        json={"query": query}
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Error fetching deployment logs: {response.status_code}")
        return None

def main():
    print("🚂 Railway Deployment Status Checker")
    print("===================================")
    
    # Load token
    token = load_railway_token()
    if not token:
        print("❌ Could not load Railway API token")
        return
    
    print(f"✅ Railway token loaded")
    
    # Get projects
    projects_data = get_railway_projects(token)
    if not projects_data:
        return
    
    print(f"\n📊 Found {len(projects_data['data']['projects']['edges'])} projects")
    
    # Find the FMCG/Supply Chain project
    for project_edge in projects_data['data']['projects']['edges']:
        project = project_edge['node']
        print(f"\n🏗️  Project: {project['name']}")
        print(f"   ID: {project['id']}")
        
        # Check services
        for service_edge in project['services']['edges']:
            service = service_edge['node']
            print(f"\n   📦 Service: {service['name']}")
            print(f"      ID: {service['id']}")
            
            # Check recent deployments
            deployments = service['deployments']['edges']
            if deployments:
                print(f"      📋 Recent Deployments:")
                
                for dep_edge in deployments:
                    dep = dep_edge['node']
                    created = datetime.fromisoformat(dep['createdAt'].replace('Z', '+00:00'))
                    print(f"         • {dep['status']} - {created.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                    if dep['url']:
                        print(f"           URL: {dep['url']}")
                    
                    # Get detailed logs for the latest deployment
                    if dep_edge == deployments[0]:  # Most recent
                        print(f"\n📋 Getting detailed logs for latest deployment...")
                        logs_data = get_deployment_logs(token, dep['id'])
                        
                        if logs_data and 'data' in logs_data:
                            deployment_data = logs_data['data']['deployment']
                            
                            print(f"\n🔍 Deployment Status: {deployment_data['status']}")
                            if deployment_data['staticUrl']:
                                print(f"🌐 URL: {deployment_data['staticUrl']}")
                            
                            # Show deploy logs if available
                            if deployment_data['deployLogs']:
                                print(f"\n📝 Deploy Logs (last 1000 chars):")
                                print("=" * 50)
                                print(deployment_data['deployLogs'][-1000:])
                                print("=" * 50)

if __name__ == "__main__":
    main()