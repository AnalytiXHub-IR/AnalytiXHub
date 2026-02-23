from app import app, db
from flask import session

with app.test_client() as client:
    with app.app_context():
        # First login
        response = client.post('/login', data={'username': 'admin', 'password': 'password'}, follow_redirects=True)
        print("Login status:", response.status_code)
        
        # Then create a case
        response = client.post('/cases/new', data={
            'case_name': 'Test Case',
            'investigator': 'Admin',
            'description': 'Test',
            'jurisdiction': 'US',
            'case_type': 'fraud'
        }, follow_redirects=True)
        print("Create case:", response.status_code)
        
        # Then set active case (assume ID 1 exists)
        response = client.get('/cases/1', follow_redirects=True)
        
        # Then investigate address
        response = client.post('/investigation', data={
            'address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            'chain': 'ethereum'
        }, follow_redirects=True)
        
        html = response.data.decode('utf-8')
        
        import re
        script_block = re.search(r'<script>(.*?flowChart.*?)</script>', html, re.DOTALL)
        if script_block:
            with open("render_test.html", "w") as f:
                f.write(script_block.group(1))
            print("Wrote render_test.html")
        else:
            print("Script block not found.")
