"""
URL configuration for spendingtracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from main import views

urlpatterns = [
    path('', views.show_main, name='show_main'),
    path('kategori/', views.kategori_list, name='kategori_list'),
    path('kategori/create/', views.kategori_create, name='kategori_create'),
    path('kategori/delete/<str:kategori_id>/', views.kategori_delete, name='kategori_delete'),
    path('transaksi/', views.transaksi_list, name='transaksi_list'),
    path('transaksi/delete/<str:transaksi_id>/', views.transaksi_delete, name='transaksi_delete'),
    path('transaksi/create/', views.transaksi_create, name='transaksi_create'),
    path('summary/', views.summary_view, name='summary'),
    path('api/test/', views.api_test, name='api_test'),
    path('saldo/', views.saldo_view, name='saldo'),
]