from django.urls import path
from . import views

# Application URL patterns — keep names stable for templates and redirects
urlpatterns = [
    path('', views.home, name='home'),  # Homepage listing
    path('books/', views.books, name='books'),  # Books listing and search
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),  # book detail by id
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),  # AJAX suggestions
    path('aboutus/', views.aboutus, name='aboutus'),  # about & contact form
    path('login/', views.login, name='login'),  # student login
    path('logout/', views.logout_view, name='logout'),  # logout clears session
    path('account/', views.account, name='account'),  # student dashboard
    path('request-return/', views.request_return, name='request_return'),  # POST endpoint to request returns
    path('register/', views.register, name='register'),  # registration form
    path('issue/', views.issue_book, name='issue'),  # request to issue a book
]