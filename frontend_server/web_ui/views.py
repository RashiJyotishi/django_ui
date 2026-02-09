import requests
import re
import json
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # For displaying error messages
# CHANGE THIS to match your Go Backend port (e.g., :3000 or :8080)
GO_BACKEND_URL = 'http://localhost:8080'

def signup_page(request):
    if request.method == 'POST':
        # 1. Extract data from the Django Form
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        ConfirmPassword = request.POST.get('ConfirmPassword')

        # 2. Prepare JSON for Go Backend
        # These keys must match the struct fields in your Go models
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "confirm_password": ConfirmPassword
        }

        try:
            # 3. Send Request to Go
            response = requests.post(f"{GO_BACKEND_URL}/api/signup", json=payload)

            # 4. Handle Response
            if response.status_code == 201:
                # Success: Redirect to login
                messages.success(request, "Account created! Please log in.")
                return redirect('login')
            else:
                # Fail: Show error from Go backend
                error_msg = response.json().get('error', 'Signup failed')
                return render(request, 'web_ui/signup.html', {'error': error_msg})

        except requests.exceptions.ConnectionError:
            return render(request, 'web_ui/signup.html', {'error': 'Cannot connect to Backend Server'})

    return render(request, 'web_ui/signup.html')


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        payload = {
            "email": email,
            "password": password
        }

        try:
            response = requests.post(f"{GO_BACKEND_URL}/api/login", json=payload)

            print("Backend status:", response.status_code)
            print("Backend raw:", response.text)

            if response.status_code == 200:
                try:
                    data = response.json()
                except ValueError:
                    return render(request, 'web_ui/login.html', {
                        'error': 'Backend returned invalid JSON'
                    })

                token = data.get('token')

                request.session['auth_token'] = token
                request.session['user_email'] = email

                return redirect('dashboard')

            else:
                # SAFE error handling
                try:
                    err = response.json().get('error', 'Login failed')
                except ValueError:
                    err = "Backend error (no JSON returned)"

                return render(request, 'web_ui/login.html', {'error': err})

        except requests.exceptions.ConnectionError:
            return render(request, 'web_ui/login.html', {
                'error': 'Cannot connect to Backend Server'
            })

    print("Error message from backend it is here:")
    return render(request, 'web_ui/login.html')


def dashboard_page(request):
    # 1. Check if user is logged in (has token in session)
    token = request.session.get('auth_token')

    if not token:
        messages.error(request, "You must log in to view the dashboard.")
        return redirect('login')

    # 2. Prepare the Header
    headers = {
        'Authorization': f'Bearer {token}'
    }

    try:
        # 3. Request the Protected Data from Go
        # Note: We are hitting the /api/dashboard route we made above
        response = requests.get(f"{GO_BACKEND_URL}/api/dashboard", headers=headers)

        if response.status_code == 200:
            data = response.json()
            return render(request, 'web_ui/dashboard.html', {
                'data': data,
                'user_email': request.session.get('user_email')
            })
        elif response.status_code == 401:
            # Token expired or invalid
            messages.error(request, "Session expired. Please login again.")
            return redirect('login')
        else:
            return render(request, 'web_ui/dashboard.html', {'error': 'Could not fetch dashboard data'})

    except requests.exceptions.ConnectionError:
        return render(request, 'web_ui/dashboard.html', {'error': 'Backend is offline'})

# Add a logout feature while we are here
def logout_user(request):
    # Clear the session
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect('login')

def home(request):
    token = request.session.get("auth_token")

    groups = []

    if token:
        headers = {
            "Authorization": f"Bearer {token}"
        }

        try:
            res = requests.get(f"{GO_BACKEND_URL}/api/groups", headers=headers)
            if res.status_code == 200:
                groups = res.json()
        except:
            pass

    return render(request, "web_ui/home.html", {
        "is_logged_in": bool(token),
        "groups": groups
    })

def create_group(request):
    token = request.session.get("auth_token")
    if not token:
        return redirect("login")

    if request.method == "POST":
        name = request.POST.get("name")
        headers = {"Authorization": f"Bearer {token}"}

        try:
            res = requests.post(
                f"{GO_BACKEND_URL}/api/create-group",
                json={"name": name},
                headers=headers
            )
            
            # Debugging logs
            print("STATUS:", res.status_code)
            print("RAW RESPONSE:", res.text)

            if res.status_code == 200:
                data = res.json()
                return render(request, "web_ui/group_created.html", {
                    "code": data["join_code"]
                })
            else:
                # Try to get a specific error message from the backend JSON
                try:
                    error_msg = res.json().get('error', f'Error {res.status_code}')
                except:
                    error_msg = f"Backend failed with status {res.status_code}"
                
                return render(request, "web_ui/create_group.html", {
                    "error": error_msg
                })

        except requests.exceptions.ConnectionError:
            return render(request, "web_ui/create_group.html", {
                "error": "Cannot connect to Backend Server (Is it running?)"
            })

    return render(request, "web_ui/create_group.html")

def join_group(request):
    token = request.session.get("auth_token")

    if request.method=="POST":
        code = request.POST.get("code")

        headers = {"Authorization": f"Bearer {token}"}

        requests.post(
            f"{GO_BACKEND_URL}/api/join-group",
            json={"code":code},
            headers=headers
        )

        return redirect("home")

    return render(request,"web_ui/join_group.html")


def add_expense(request, group_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect("login")

    if request.method == "POST":
        amount = request.POST.get("amount")
        description = request.POST.get("description")

        headers = {"Authorization": f"Bearer {token}"}

        try:
            # Added basic validation to prevent crash on empty strings
            amt_float = float(amount) if amount else 0.0
        except ValueError:
            amt_float = 0.0

        res = requests.post(
            f"{GO_BACKEND_URL}/api/expenses",
            json={
                "group_id": group_id,
                "amount": float(amount),
                "description": description
            },
            headers=headers
        )

        return redirect("home")

    return render(request, "web_ui/add_expense.html", {"group_id": group_id})

def get_current_user_id(request):
    token = request.session.get("auth_token")
    if not token:
        return None
    try:
        
        parts = token.split('.')
        if len(parts) < 2: return None
        
        payload = parts[1]
        # Fix Base64 padding if necessary
        payload += '=' * (-len(payload) % 4)
        
        decoded_bytes = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded_bytes)
        
        # 'user_id' matches the key used in your auth.go
        return int(data.get('user_id'))
    except Exception as e:
        print(f"Token decode error: {e}")
        return None

def simplify_group(request, group_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect('login')
    
    headers = {"Authorization": f"Bearer {token}"}
    txns = []
    my_id = get_current_user_id(request) # Get logged-in user's ID

    try:
        # 1. Fetch ALL group debts from backend
        res = requests.get(f"{GO_BACKEND_URL}/api/groups/{group_id}/simplify", headers=headers)
        if res.status_code == 200:
            all_txns = res.json()
            
            # 2. FILTER: Only keep debts involving the current user
            # structure: {'from': 1, 'to': 2, ...}
            if my_id:
                txns = [
                    t for t in all_txns 
                    if t.get('from') == my_id or t.get('to') == my_id
                ]
            else:
                txns = all_txns # Fallback if token decode fails
    except:
        print(f"Error fetching debts: {e}")
        txns = []

    return render(request, "web_ui/simplify.html", {
        "txns": txns,
        "group_id": group_id
    })


def settle_debt(request, group_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect('login')

    if request.method == "POST":
        payee_id = request.POST.get('payee_id')
        payee_name = request.POST.get('payee_name') # Optional, for description
        amount = request.POST.get('amount')

        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "group_id": int(group_id),
            "amount": float(amount),
            "description": f"Settlement: Paid to {payee_name}", 
            "splits": [
                {
                    "user_id": int(payee_id), # Assign 100% of the cost to the receiver
                    "amount": float(amount)
                }
            ]
        }

        try:
            response = requests.post(
                f"{GO_BACKEND_URL}/api/expenses",
                json=payload,
                headers=headers
            )

            if response.status_code in [200, 201]:
                messages.success(request, "Payment recorded! Debt settled.")
            else:
                messages.error(request, f"Error: {response.text}")

        except requests.exceptions.ConnectionError:
            messages.error(request, "Backend unavailable.")

    return redirect('simplify', group_id=group_id)

# New View for History
def group_expenses(request, group_id):
    token = request.session.get("auth_token")
    if not token:
        return redirect('login')
    
    headers = {"Authorization": f"Bearer {token}"}
    expenses = []

    try:

        res = requests.get(f"{GO_BACKEND_URL}/api/groups/{group_id}/expenses", headers=headers)
        if res.status_code == 200:
            expenses = res.json()
    except:
        pass

    return render(request, "web_ui/group_expenses.html", {
        "expenses": expenses,
        "group_id": group_id
    })