from django.test import TestCase
from django.urls import reverse
from .models import Book, Genre


class BooksSearchTests(TestCase):
    def test_search_filters_books_by_title_author_or_genre(self):
        genre = Genre.objects.create(genre_name='Fantasy')
        Book.objects.create(
            genre_id=genre,
            book_title='The Hobbit',
            book_author='J.R.R. Tolkien',
            book_description='A classic adventure story.'
        )
        Book.objects.create(
            genre_id=genre,
            book_title='Dune',
            book_author='Frank Herbert',
            book_description='A sci-fi epic.'
        )

        response = self.client.get(reverse('books'), {'q': 'hobbit'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The Hobbit')
        self.assertNotContains(response, 'Dune')
