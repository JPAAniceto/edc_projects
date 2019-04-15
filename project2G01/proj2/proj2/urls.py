"""proj1 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from bolsa import views
from bolsa import repmanager
from django.contrib.auth import views as authViews

try:
    repmanager.start_db()
except:
    print("Please open GraphDB for the system to work properly".upper())
    print("")

adminPatterns = [
    path('main/', views.adminMain, name="admin Main page"),
    path('addCompany/', views.adminAddCompany, name="admin add company"),
    path('editCompany/', views.adminEditCompany, name="admin edit company"),
    path('deleteCompany/', views.adminDeleteCompany, name="admin delete company"),
    path('addCEO/', views.adminAddCEO, name="admin add CEO"),
    path('editCEO/', views.adminEditCEO, name="admin edit CEO"),
    path('deleteCEO/', views.adminDeleteCEO, name="admin delete CEO"),
    path('addCoin/', views.adminAddCoin, name="admin add Coin"),
    path('deleteCoin/', views.adminDeleteCoin, name="admin delete Coin"),
    path('exportDB/', views.adminExportDB, name="admin exportDB"),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="Home"),
    path('values/', views.valuesHome, name="valuesHome"),
    path('companies/', views.companies, name="companies"),
    path('companies/<str:symbol>', views.companiesInfo, name="companiesInfo"),
    path('ceos/', views.ceos, name="ceos"),
    path('ceos/<str:name>', views.ceosinfo, name="ceosinfo"),
    path('profile/', views.profile, name="profile"),
    path('seefull/<str:type>', views.seefull, name="seefull"),


    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.register, name="register"),
    path('accounts/logout_view/', views.logout_view, name="logout_view"),


    path('selectCoin/<str:code>/', views.selectCoin, name='selectCoin'),

    path('admin/', include(adminPatterns), name='admin URLs'),

    path('favorite/company/<str:code>/', views.favoriteCompany, name='Favorite company'),
    path('unfavorite/company/<str:code>/', views.unfavoriteCompany, name='Unfavorite company'),
    path('favorite/ceo/<str:name>/', views.favoriteCeo, name='Favorite ceo'),
    path('unfavorite/ceo/<str:name>/', views.unfavoriteCeo, name='Unfavorite ceo'),


]


