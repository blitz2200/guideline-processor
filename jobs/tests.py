from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json
from .models import Job
from .tasks import process_guideline_job


class JobModelTest(TestCase):
    def test_job_creation(self):
        """Test job model creation"""
        job = Job.objects.create(input_data="Test guideline text")
        self.assertEqual(job.status, 'pending')
        self.assertIsNotNone(job.event_id)
        self.assertEqual(job.input_data, "Test guideline text")

    def test_job_str(self):
        """Test job string representation"""
        job = Job.objects.create(input_data="Test")
        expected = f"Job {job.event_id} - pending"
        self.assertEqual(str(job), expected)


class JobAPITest(APITestCase):
    def test_create_job_success(self):
        """Test successful job creation"""
        url = reverse('create_job')
        data = {'guideline_text': 'Sample guideline for testing'}

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('event_id', response.data)
        self.assertEqual(response.data['status'], 'pending')

        # Verify job was created in database
        job = Job.objects.get(event_id=response.data['event_id'])
        self.assertEqual(job.input_data, 'Sample guideline for testing')

    def test_create_job_invalid_data(self):
        """Test job creation with invalid data"""
        url = reverse('create_job')
        data = {}  # Missing required field

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_job_success(self):
        """Test successful job retrieval"""
        job = Job.objects.create(
            input_data="Test guideline",
            status='completed',
            summary="Test summary",
            checklist=["Item 1", "Item 2"]
        )

        url = reverse('get_job', kwargs={'event_id': job.event_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['event_id'], str(job.event_id))
        self.assertEqual(response.data['status'], 'completed')
        self.assertIsNotNone(response.data['result'])
        self.assertEqual(response.data['result']['summary'], 'Test summary')

    def test_get_job_not_found(self):
        """Test job retrieval with invalid ID"""
        from uuid import uuid4

        url = reverse('get_job', kwargs={'event_id': uuid4()})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_job_pending_status(self):
        """Test job retrieval with pending status"""
        job = Job.objects.create(input_data="Test guideline")

        url = reverse('get_job', kwargs={'event_id': job.event_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIsNone(response.data['result'])


class JobTaskTest(TestCase):
    @patch('jobs.tasks.openai.OpenAI')
    def test_process_guideline_job_success(self, mock_openai):
        """Test successful job processing"""
        # Create test job
        job = Job.objects.create(input_data="Test guideline content")

        # Mock OpenAI responses
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock summary response
        mock_summary_response = MagicMock()
        mock_summary_response.choices[0].message.content = "This is a test summary"

        # Mock checklist response
        mock_checklist_response = MagicMock()
        mock_checklist_response.choices[0].message.content = '["Check item 1", "Check item 2"]'

        mock_client.chat.completions.create.side_effect = [
            mock_summary_response,
            mock_checklist_response
        ]

        # Run the task
        result = process_guideline_job(str(job.event_id))

        # Verify result
        job.refresh_from_db()
        self.assertEqual(job.status, 'completed')
        self.assertEqual(job.summary, "This is a test summary")
        self.assertEqual(job.checklist, ["Check item 1", "Check item 2"])
        self.assertIn("completed successfully", result)

    @patch('jobs.tasks.openai.OpenAI')
    def test_process_guideline_job_failure(self, mock_openai):
        """Test job processing failure"""
        job = Job.objects.create(input_data="Test guideline content")

        # Mock OpenAI to raise exception
        mock_openai.side_effect = Exception("API Error")

        # Run the task
        result = process_guideline_job(str(job.event_id))

        # Verify failure handling
        job.refresh_from_db()
        self.assertEqual(job.status, 'failed')
        self.assertIsNotNone(job.error_message)
        self.assertIn("failed", result)

    def test_process_nonexistent_job(self):
        """Test processing non-existent job"""
        from uuid import uuid4

        result = process_guideline_job(str(uuid4()))
        self.assertIn("not found", result)