from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('books/', views.books, name='books'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'), # book detail page opens based on the book id being picked.
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('register/', views.register, name='register'),
]