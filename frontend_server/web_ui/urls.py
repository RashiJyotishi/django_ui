from django.urls import path
from . import views

#app_name="web_ui"
urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("signup/", views.signup_page, name="signup"),
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("logout/", views.logout_user, name="logout"),
    path("create-group/", views.create_group, name="create_group"),
    path("join-group/", views.join_group, name="join_group"),
    path("add-expense/<int:group_id>/", views.add_expense, name="add_expense"),
    path("groups/<int:group_id>/simplify/", views.simplify_group, name="simplify"),
    path('groups/<int:group_id>/settle/', views.settle_debt, name='settle_debt'),
    path('groups/<int:group_id>/history/', views.group_expenses, name='group_expenses'),
]
