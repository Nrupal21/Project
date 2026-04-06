"""
Test cases for the reviews app.

This module contains comprehensive test cases for all functionality
in the reviews app, including models, views, forms, and utilities.
Every test function is thoroughly documented to make understanding
the tests easier for programmers.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile

from reviews.models import Review, ReviewImage, ReviewComment, ReviewHelpful
from tests.base import TravelGuideBaseTestCase

User = get_user_model()

class ReviewModelTests(TravelGuideBaseTestCase):
    """
    Tests for the Review model in the reviews app.
    
    These tests verify that Review objects can be created correctly,
    and that their methods work as expected. Each test focuses on a 
    specific aspect of the Review model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for Review tests.
        
        Extends the base setUp method to include a review for testing.
        Creates a review for a destination to use in tests.
        """
        super().setUp()
        
        # Create a review for the destination
        self.review = self.create_review(
            user=self.test_user,
            content_object=self.destination,
            rating=5
        )
    
    def test_review_creation(self):
        """
        Test that a Review can be created with the expected attributes.
        
        Verifies that the Review model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        content_type = ContentType.objects.get_for_model(self.tour)
        
        review = Review.objects.create(
            user=self.test_user,
            content_type=content_type,
            object_id=self.tour.id,
            title='Great Tour Experience',
            content='This was an amazing tour with excellent guides.',
            rating=4,
            status='approved'
        )
        
        # Verify the review was created with the correct attributes
        self.assertEqual(review.title, 'Great Tour Experience')
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.content_object, self.tour)
        self.assertEqual(review.user, self.test_user)
        
    def test_review_str_method(self):
        """
        Test the string representation of a Review object.
        
        Verifies that the __str__ method returns the expected string
        containing the review title and rating display.
        """
        expected_str = f"{self.review.title} ({self.review.get_rating_display()})"
        self.assertEqual(str(self.review), expected_str)
        
    def test_review_get_absolute_url(self):
        """
        Test the get_absolute_url method of the Review model.
        
        Verifies that the URL generated for a review detail page is correct
        and matches the expected URL pattern.
        """
        expected_url = reverse('reviews:review_detail', kwargs={'review_id': self.review.id})
        self.assertEqual(self.review.get_absolute_url(), expected_url)
        
    def test_review_helpful_count(self):
        """
        Test the helpful_count property of the Review model.
        
        Verifies that the helpful_count property correctly returns the
        number of users who found the review helpful.
        """
        # Initially, there should be no helpful votes
        self.assertEqual(self.review.helpful_count, 0)
        
        # Add a helpful vote
        ReviewHelpful.objects.create(
            review=self.review,
            user=self.admin_user,
            vote_type='helpful'
        )
        
        # Now there should be one helpful vote
        self.assertEqual(self.review.helpful_count, 1)
        
    def test_review_comments_count(self):
        """
        Test the comments_count property of the Review model.
        
        Verifies that the comments_count property correctly returns the
        number of comments on the review.
        """
        # Initially, there should be no comments
        self.assertEqual(self.review.comments_count, 0)
        
        # Add a comment
        ReviewComment.objects.create(
            review=self.review,
            user=self.admin_user,
            content='This is a test comment.'
        )
        
        # Now there should be one comment
        self.assertEqual(self.review.comments_count, 1)


class ReviewImageModelTests(TravelGuideBaseTestCase):
    """
    Tests for the ReviewImage model in the reviews app.
    
    These tests verify that ReviewImage objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the ReviewImage model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for ReviewImage tests.
        
        Extends the base setUp method to include a review and review image.
        """
        super().setUp()
        
        # Create a review for the destination
        self.review = self.create_review(
            user=self.test_user,
            content_object=self.destination,
            rating=5
        )
        
        # Create a review image
        self.review_image = ReviewImage.objects.create(
            review=self.review,
            image='reviews/test-image.jpg',
            caption='Beautiful view from the hotel',
            is_primary=True
        )
    
    def test_review_image_creation(self):
        """
        Test that a ReviewImage can be created with the expected attributes.
        
        Verifies that the ReviewImage model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        review_image = ReviewImage.objects.create(
            review=self.review,
            image='reviews/another-image.jpg',
            caption='Another great photo',
            is_primary=False
        )
        
        # Verify the review image was created with the correct attributes
        self.assertEqual(review_image.review, self.review)
        self.assertEqual(review_image.image, 'reviews/another-image.jpg')
        self.assertEqual(review_image.caption, 'Another great photo')
        self.assertFalse(review_image.is_primary)
        
    def test_review_image_str_method(self):
        """
        Test the string representation of a ReviewImage object.
        
        Verifies that the __str__ method returns the expected string,
        which should be the caption if available or a default description.
        """
        # Test with caption
        self.assertEqual(str(self.review_image), 'Beautiful view from the hotel')
        
        # Test without caption
        review_image_no_caption = ReviewImage.objects.create(
            review=self.review,
            image='reviews/no-caption.jpg',
            caption='',
            is_primary=False
        )
        expected_str = f"Image for review #{self.review.id}"
        self.assertEqual(str(review_image_no_caption), expected_str)


class ReviewCommentModelTests(TravelGuideBaseTestCase):
    """
    Tests for the ReviewComment model in the reviews app.
    
    These tests verify that ReviewComment objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the ReviewComment model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for ReviewComment tests.
        
        Extends the base setUp method to include a review and comment.
        """
        super().setUp()
        
        # Create a review for the destination
        self.review = self.create_review(
            user=self.test_user,
            content_object=self.destination,
            rating=5
        )
        
        # Create a review comment
        self.comment = ReviewComment.objects.create(
            review=self.review,
            user=self.admin_user,
            content='This is a test comment on the review.',
            is_official_response=True
        )
    
    def test_review_comment_creation(self):
        """
        Test that a ReviewComment can be created with the expected attributes.
        
        Verifies that the ReviewComment model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        comment = ReviewComment.objects.create(
            review=self.review,
            user=self.test_user,
            content='I agree with this review!',
            is_official_response=False
        )
        
        # Verify the comment was created with the correct attributes
        self.assertEqual(comment.review, self.review)
        self.assertEqual(comment.user, self.test_user)
        self.assertEqual(comment.content, 'I agree with this review!')
        self.assertFalse(comment.is_official_response)
        
    def test_review_comment_str_method(self):
        """
        Test the string representation of a ReviewComment object.
        
        Verifies that the __str__ method returns the expected string
        containing the username and comment content excerpt.
        """
        expected_str = f"Comment by {self.admin_user.username}: {self.comment.content[:30]}..."
        self.assertEqual(str(self.comment), expected_str)
        
    def test_review_comment_replies(self):
        """
        Test that ReviewComment objects can have replies.
        
        Verifies that the parent-child relationship between comments
        works correctly for threaded discussions.
        """
        # Create a reply to the comment
        reply = ReviewComment.objects.create(
            review=self.review,
            user=self.test_user,
            parent=self.comment,
            content='Thank you for your response!',
            is_official_response=False
        )
        
        # Verify the reply has the correct parent
        self.assertEqual(reply.parent, self.comment)
        
        # Verify the comment has the reply in its replies
        self.assertIn(reply, self.comment.replies.all())


class ReviewHelpfulModelTests(TravelGuideBaseTestCase):
    """
    Tests for the ReviewHelpful model in the reviews app.
    
    These tests verify that ReviewHelpful objects can be created correctly,
    and that their methods work as expected. Each test focuses on a
    specific aspect of the ReviewHelpful model's functionality.
    """
    
    def setUp(self):
        """
        Set up test data for ReviewHelpful tests.
        
        Extends the base setUp method to include a review and helpful vote.
        """
        super().setUp()
        
        # Create a review for the destination
        self.review = self.create_review(
            user=self.test_user,
            content_object=self.destination,
            rating=5
        )
        
        # Create a helpful vote
        self.helpful_vote = ReviewHelpful.objects.create(
            review=self.review,
            user=self.admin_user,
            vote_type='helpful',
            ip_address='127.0.0.1',
            user_agent='Test User Agent'
        )
    
    def test_review_helpful_creation(self):
        """
        Test that a ReviewHelpful can be created with the expected attributes.
        
        Verifies that the ReviewHelpful model can be instantiated with the required
        fields and that the values are stored correctly in the database.
        """
        # Create another user for testing
        another_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='anotherpassword123'
        )
        
        helpful_vote = ReviewHelpful.objects.create(
            review=self.review,
            user=another_user,
            vote_type='not_helpful',
            ip_address='192.168.1.1',
            user_agent='Another Test User Agent'
        )
        
        # Verify the helpful vote was created with the correct attributes
        self.assertEqual(helpful_vote.review, self.review)
        self.assertEqual(helpful_vote.user, another_user)
        self.assertEqual(helpful_vote.vote_type, 'not_helpful')
        self.assertEqual(helpful_vote.ip_address, '192.168.1.1')
        
    def test_review_helpful_str_method(self):
        """
        Test the string representation of a ReviewHelpful object.
        
        Verifies that the __str__ method returns the expected string
        describing the helpful vote.
        """
        expected_str = f"{self.admin_user.username} found review #{self.review.id} helpful"
        self.assertEqual(str(self.helpful_vote), expected_str)
        
    def test_review_helpful_unique_constraint(self):
        """
        Test that a user can only have one vote per review.
        
        Verifies that the unique_together constraint prevents duplicate
        votes from the same user on the same review.
        """
        # Attempt to create another vote from the same user on the same review
        with self.assertRaises(Exception):
            ReviewHelpful.objects.create(
                review=self.review,
                user=self.admin_user,
                vote_type='not_helpful'
            )


class ReviewViewTests(TravelGuideBaseTestCase):
    """
    Tests for the views in the reviews app.
    
    These tests verify that the views render the correct templates,
    contain the expected context data, and handle form submissions correctly.
    Each test focuses on a specific view or aspect of view functionality.
    """
    
    def setUp(self):
        """
        Set up test data for review view tests.
        
        Extends the base setUp method to include reviews and login the test user.
        """
        super().setUp()
        
        # Create a review for the destination
        self.review = self.create_review(
            user=self.test_user,
            content_object=self.destination,
            rating=5
        )
        
        # Create a review for the tour
        self.tour_review = self.create_review(
            user=self.test_user,
            content_object=self.tour,
            rating=4
        )
        
        # Log in the test user
        self.login_test_user()
    
    def test_review_list_view(self):
        """
        Test the review list view.
        
        Verifies that the review list view returns a 200 status code,
        uses the correct template, and includes the reviews in the context.
        """
        response = self.client.get(reverse('reviews:review_list'))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'reviews/review_list.html')
        
        # Check that the reviews are in the context
        self.assertIn('reviews', response.context)
        self.assertIn(self.review, response.context['reviews'])
        self.assertIn(self.tour_review, response.context['reviews'])
        
    def test_review_detail_view(self):
        """
        Test the review detail view.
        
        Verifies that the review detail view returns a 200 status code,
        uses the correct template, and includes the review in the context.
        """
        response = self.client.get(reverse('reviews:review_detail', kwargs={'review_id': self.review.id}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'reviews/review_detail.html')
        
        # Check that the review is in the context
        self.assertEqual(response.context['review'], self.review)
        
    def test_create_review_view(self):
        """
        Test the create review view.
        
        Verifies that the create review view returns a 200 status code,
        uses the correct template, and allows submission of a new review.
        """
        # Get the content type for destinations
        content_type = ContentType.objects.get_for_model(self.destination)
        
        # Get the create review page
        response = self.client.get(reverse('reviews:create_review', kwargs={
            'content_type_id': content_type.id,
            'object_id': self.destination.id
        }))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'reviews/create_review.html')
        
        # Submit a new review
        response = self.client.post(reverse('reviews:create_review', kwargs={
            'content_type_id': content_type.id,
            'object_id': self.destination.id
        }), {
            'title': 'New Test Review',
            'content': 'This is a new test review content.',
            'rating': 3
        })
        
        # Check that the review was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the review exists in the database
        self.assertTrue(Review.objects.filter(
            title='New Test Review',
            rating=3,
            content_type=content_type,
            object_id=self.destination.id
        ).exists())
        
    def test_edit_review_view(self):
        """
        Test the edit review view.
        
        Verifies that the edit review view returns a 200 status code,
        uses the correct template, and allows editing of an existing review.
        """
        # Get the edit review page
        response = self.client.get(reverse('reviews:edit_review', kwargs={'review_id': self.review.id}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'reviews/edit_review.html')
        
        # Submit edited review
        response = self.client.post(reverse('reviews:edit_review', kwargs={'review_id': self.review.id}), {
            'title': 'Updated Review Title',
            'content': 'This is the updated content for the review.',
            'rating': 4
        })
        
        # Check that the review was updated and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Refresh the review from the database
        self.review.refresh_from_db()
        
        # Check that the review was updated
        self.assertEqual(self.review.title, 'Updated Review Title')
        self.assertEqual(self.review.content, 'This is the updated content for the review.')
        self.assertEqual(self.review.rating, 4)
        
    def test_delete_review_view(self):
        """
        Test the delete review view.
        
        Verifies that the delete review view allows deletion of a review
        and redirects appropriately.
        """
        # Get the delete review page
        response = self.client.get(reverse('reviews:delete_review', kwargs={'review_id': self.review.id}))
        
        # Check that the response is 200 OK
        self.assertEqual(response.status_code, 200)
        
        # Check that the correct template is used
        self.assertTemplateUsed(response, 'reviews/delete_review.html')
        
        # Submit delete request
        response = self.client.post(reverse('reviews:delete_review', kwargs={'review_id': self.review.id}))
        
        # Check that the review was deleted and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the review no longer exists in the database
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())
        
    def test_add_comment_view(self):
        """
        Test the add comment view.
        
        Verifies that the add comment view allows adding a comment to a review
        and redirects appropriately.
        """
        # Submit a new comment
        response = self.client.post(reverse('reviews:add_comment', kwargs={'review_id': self.review.id}), {
            'content': 'This is a test comment on the review.'
        })
        
        # Check that the comment was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the comment exists in the database
        self.assertTrue(ReviewComment.objects.filter(
            review=self.review,
            user=self.test_user,
            content='This is a test comment on the review.'
        ).exists())
        
    def test_mark_helpful_view(self):
        """
        Test the mark helpful view.
        
        Verifies that the mark helpful view allows marking a review as helpful
        and redirects appropriately.
        """
        # Submit a helpful vote
        response = self.client.post(reverse('reviews:mark_helpful', kwargs={'review_id': self.tour_review.id}))
        
        # Check that the vote was created and redirected
        self.assertEqual(response.status_code, 302)  # Redirect status code
        
        # Check that the vote exists in the database
        self.assertTrue(ReviewHelpful.objects.filter(
            review=self.tour_review,
            user=self.test_user
        ).exists())
