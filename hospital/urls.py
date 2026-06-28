from django.urls import path
from . import views

urlpatterns = [
    path("", views.login_view, name="login"),
    path("painel/", views.dashboard, name="dashboard"),
    path("diagrama/", views.diagrama, name="diagrama"),
    path("sql/", views.sql_view, name="sql_view"),
    path("sobre/", views.sobre, name="sobre"),
    path("popular-mock/", views.popular_mock, name="popular_mock"),
    path("dashboard/diretor/", views.dashboard_diretor, name="dashboard_diretor"),
    path("dashboard/chefe/", views.dashboard_chefe, name="dashboard_chefe"),
    path("dashboard/farmaceutico/", views.dashboard_farmaceutico, name="dashboard_farmaceutico"),
    path("<str:model_slug>/", views.list_view, name="list_view"),
    path("<str:model_slug>/novo/", views.create_view, name="create_view"),
]