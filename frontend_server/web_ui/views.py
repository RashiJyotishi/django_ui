import requests
from django.shortcuts import render, redirect
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
            "Username": username,
            "Email": email,
            "Password": password,
            "ConfirmPassword": ConfirmPassword
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

    return render(request, "web_ui/home.html", {
        "is_logged_in": bool(token)
    })
