"""Test HRMS manager and employee fetching."""
import asyncio
import os

# Use the actual HRMS credentials from docker-compose
os.environ['HRMS_BASE_URL'] = 'http://127.0.0.1:8000'  # Adjust if HRMS is on different port
os.environ['HRMS_INTEGRATION_EMAIL'] = 'admin@nxzen.com'
os.environ['HRMS_INTEGRATION_PASSWORD'] = '123'

from app.services.hrms_client import hrms_client

async def test():
    print('=== MANAGERS LIST ===')
    managers = await hrms_client.get_managers_list()
    print(f'Response type: {type(managers)}')
    if isinstance(managers, dict):
        print(f'Keys: {managers.keys()}')
        if 'managers' in managers:
            for m in managers['managers'][:10]:
                print(f'  Manager: {m}')
    elif isinstance(managers, list):
        for m in managers[:10]:
            print(f'  Manager: {m}')
    
    print()
    print('=== ALL EMPLOYEES ===')
    employees = await hrms_client.get_all_employees()
    print(f'Total employees: {len(employees)}')
    for emp in employees[:10]:
        name = emp.get("name")
        managers_list = emp.get("managers")
        emp_id = emp.get("company_employee_id")
        print(f'  Employee: {name} ({emp_id}), managers: {managers_list}')

async def test_manager_email(email):
    print(f'\n=== TEST get_employees_by_manager_email("{email}") ===')
    employees = await hrms_client.get_employees_by_manager_email(email)
    print(f'Found {len(employees)} employees')
    for emp in employees[:10]:
        name = emp.get("name")
        emp_id = emp.get("company_employee_id")
        print(f'  Employee: {name} ({emp_id})')

if __name__ == "__main__":
    asyncio.run(test())
    # Test with specific manager emails
    asyncio.run(test_manager_email("manager@nxzen.com"))
    asyncio.run(test_manager_email("vamsi.krishna@nxzen.com"))
    asyncio.run(test_manager_email("ganapathy.thimmaiah@nxzen.com"))
