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
from bolsa import baseX_db
from django.contrib.auth import views as authViews

baseX_db.start_db()

adminXMLpatterns = [
    path('main/', views.adminXmlMain, name="admin xml main page"),
    path('export/<str:target>', views.adminXmlExport, name="admin xml export files"),
    path('submit/update', views.adminXmlSubmitUpdate, name="admin xml submit update"),
    path('submit/company', views.adminXmlSubmitCompany, name="admin xml submit company")
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name="Home"),
    path('values/', views.valuesHome, name="valuesHome"),
    path('values/today', views.valuesToday, name="valuesToday"),
    path('values/filter', views.valuesFilter, name="valuesFilter"),
    path('values/coins', views.valuesCoins, name="valuesCoins"),
    path('companies/', views.companies, name="companies"),
    path('companies/<str:symbol>', views.companiesInfo, name="companiesInfo"),
    path('portfolio/', views.portfolio, name="portfolio"),
    path('sell/', views.sell, name="sell"),

    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/register/', views.register, name="register"),
    path('accounts/logout_view/', views.logout_view, name="logout_view"),

    path('rssfeed/<str:symbol>/', views.rssFeed, name='rssFeed'),

    path('seefull/<str:type>/', views.seeFull, name='seeFull'),

    path('selectCoin/<str:code>/', views.selectCoin, name='selectCoin'),

    path('adminxml/', include(adminXMLpatterns), name='admin xml patters')
]


