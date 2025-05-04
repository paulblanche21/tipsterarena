from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Tip, UserProfile
from rest_framework.authtoken.models import Token
import json

from django.test.utils import override_settings
from unittest.mock import patch
from django.conf import settings
from PIL import Image
import io
from django.core.files.uploadedfile import SimpleUploadedFile
import shutil
import tempfile
from core.factories import UserFactory, TipFactory

User = get_user_model()


class MediaFeaturesTest(TestCase):
    """Test suite for media features functionality."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a temporary directory for media files
        cls.temp_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = cls.temp_dir

    @classmethod
    def tearDownClass(cls):
        # Clean up the temporary directory
        shutil.rmtree(cls.temp_dir)
        super().tearDownClass()

    def setUp(self):
        """Set up test data."""
        # Create user and authentication
        self.user = UserFactory()
        self.user.set_password('testpass123')
        self.user.save()
        self.user_profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.tip = TipFactory(user=self.user)
        self.token = Token.objects.create(user=self.user)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        self.client.defaults['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        # Mock GIPHY API key for testing
        self.settings_override = override_settings(GIPHY_API_KEY='test_api_key')
        self.settings_override.enable()

        # Mock GIPHY API response
        self.giphy_patcher = patch('requests.get')
        self.mock_giphy = self.giphy_patcher.start()
        self.mock_giphy.return_value.status_code = 200
        self.mock_giphy.return_value.json.return_value = {
            'data': [
                {
                    'id': 'test1',
                    'images': {
                        'original': {
                            'url': 'https://giphy.com/test1.gif',
                            'width': '200',
                            'height': '200'
                        }
                    }
                }
            ]
        }
        
        # Create a test image
        test_image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        test_image.save(image_io, format='JPEG')
        image_io.seek(0)
        self.test_image = SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )

    def tearDown(self):
        """Clean up after each test."""
        self.settings_override.disable()
        self.giphy_patcher.stop()
        super().tearDown()

    @patch('requests.get')
    def test_gif_search(self, mock_get):
        """Test GIF search functionality."""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'data': [
                {
                    'id': 'test1',
                    'images': {
                        'original': {
                            'url': 'https://giphy.com/test1.gif',
                            'width': '200',
                            'height': '200'
                        }
                    }
                }
            ]
        }
        
        response = self.client.get('/api/search-gifs/', {'q': 'celebration'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue('gifs' in data)
        self.assertTrue(len(data['gifs']) > 0)

    def test_post_tip_with_gif(self):
        """Test posting a tip with a GIF."""
        data = {
            'tip_text': 'Test tip with GIF',
            'sport': 'football',
            'audience': 'public',
            'odds_type': 'decimal',
            'odds-input-decimal': '2.5',
            'bet_type': 'single',
            'each_way': 'no',
            'confidence': '3',
            'gif': 'https://giphy.com/test1.gif',
            'gif_width': 200,
            'gif_height': 200
        }
        response = self.client.post('/api/post-tip/', data)
        print(f"Response content: {response.content.decode()}")  # Print response content
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        tip = Tip.objects.get(id=data['tip_id'])
        self.assertEqual(tip.gif_url, 'https://giphy.com/test1.gif')
        self.assertEqual(tip.gif_width, 200)
        self.assertEqual(tip.gif_height, 200)

    def test_comment_with_gif(self):
        """Test commenting with a GIF"""
        comment_data = {
            'tip_id': self.tip.id,
            'comment_text': 'Comment with GIF',
            'gif': 'https://media.giphy.com/media/example.gif'
        }
        response = self.client.post(
            reverse('comment_tip'),
            data=comment_data
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(data['data']['gif_url'])

    def test_invalid_gif_url(self):
        """Test handling of invalid GIF URLs"""
        tip_data = {
            'tip_text': 'Test tip with invalid GIF',
            'sport': 'football',
            'audience': 'public',
            'odds_type': 'decimal',
            'odds-input-decimal': '2.5',
            'bet_type': 'single',
            'each_way': 'no',
            'confidence': '3',
            'gif': 'invalid-url'
        }
        response = self.client.post(
            reverse('api_post_tip'),
            data=tip_data
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid GIF URL', data['error'])

    def test_post_tip_with_emoji(self):
        """Test posting a tip with emojis"""
        tip_data = {
            'tip_text': 'Test tip with emoji 😊',
            'sport': 'football',
            'audience': 'public',
            'odds_type': 'decimal',
            'odds-input-decimal': '2.5',
            'bet_type': 'single',
            'each_way': 'no',
            'confidence': '3',
            'emojis': json.dumps({'😊': 1})
        }
        response = self.client.post(
            reverse('api_post_tip'),
            data=tip_data
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        tip = Tip.objects.get(text='Test tip with emoji 😊')
        self.assertIn('😊', tip.text)

    def test_comment_with_emoji(self):
        """Test commenting with emojis"""
        comment_data = {
            'tip_id': self.tip.id,
            'comment_text': 'Great tip! 👍',
            'emojis': json.dumps({'👍': 1})
        }
        response = self.client.post(
            reverse('comment_tip'),
            data=comment_data
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('👍', data['data']['content'])

    def test_emoji_validation(self):
        """Test emoji validation in text content"""
        # Test with valid emoji
        tip_data = {
            'tip_text': 'Valid emoji test 🎉',
            'sport': 'football',
            'audience': 'public',
            'odds_type': 'decimal',
            'odds-input-decimal': '2.5',
            'bet_type': 'single',
            'each_way': 'no',
            'confidence': '3',
            'emojis': json.dumps({'🎉': 1})
        }
        response = self.client.post(
            reverse('api_post_tip'),
            data=tip_data
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        # Test with invalid emoji data
        tip_data['emojis'] = 'invalid-json'
        response = self.client.post(
            reverse('api_post_tip'),
            data=tip_data
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Invalid emoji data', data['error'])

    def test_combined_media_post(self):
        """Test posting a tip with both image and GIF."""
        data = {
            'tip_text': 'Test tip with image and GIF',
            'sport': 'football',
            'audience': 'public',
            'odds_type': 'decimal',
            'odds-input-decimal': '2.5',
            'bet_type': 'single',
            'each_way': 'no',
            'confidence': '3',
            'image': self.test_image,
            'gif': 'https://giphy.com/test2.gif',
            'gif_width': 300,
            'gif_height': 300
        }
        response = self.client.post('/api/post-tip/', data)
        print(f"Response content: {response.content.decode()}")  # Print response content
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        tip = Tip.objects.get(id=data['tip_id'])
        self.assertTrue(tip.image.name.endswith('test_image.jpg'))
        self.assertEqual(tip.gif_url, 'https://giphy.com/test2.gif')
        self.assertEqual(tip.gif_width, 300)
        self.assertEqual(tip.gif_height, 300) 