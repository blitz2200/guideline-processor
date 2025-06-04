import os
from celery import shared_task
from django.conf import settings
# from openai import OpenAI
import json
from .models import Job
import openai

@shared_task
def process_guideline_job(job_id):
    """
    Two-step GPT chain: summarize → generate checklist
    """
    try:
        job = Job.objects.get(event_id=job_id)
        job.status = 'processing'
        job.save()


        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Step 1: Summarize the guideline
        summary_prompt = f"""
        Please provide a concise summary of the following guideline document. 
        Focus on the key points, main requirements, and important procedures.

        Guideline text:
        {job.input_data}
        """

        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=500,
            temperature=0.3
        )

        summary = summary_response.choices[0].message.content.strip()
        job.summary = summary
        job.save()

        # Step 2: Generate checklist based on summary
        checklist_prompt = f"""
        Based on the following summary of a guideline document, create a practical checklist 
        that someone could use to ensure they follow all the important requirements.

        Return the response as a JSON array of strings, where each string is a checklist item.

        Summary:
        {summary}
        """

        checklist_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": checklist_prompt}],
            max_tokens=800,
            temperature=0.3
        )

        checklist_text = checklist_response.choices[0].message.content.strip()

        # Try to parse as JSON, fallback to simple list if parsing fails
        try:
            checklist = json.loads(checklist_text)
            if not isinstance(checklist, list):
                raise ValueError("Not a list")
        except (json.JSONDecodeError, ValueError):
            # Fallback: split by lines and clean up
            checklist = [
                line.strip().lstrip('- ').lstrip('* ').lstrip('• ')
                for line in checklist_text.split('\n')
                if line.strip() and not line.strip().startswith('[') and not line.strip().startswith(']')
            ]

        job.checklist = checklist
        job.status = 'completed'
        job.save()

        return f"Job {job_id} completed successfully"

    except Job.DoesNotExist:
        return f"Job {job_id} not found"
    except Exception as e:
        try:
            job = Job.objects.get(event_id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
        except Job.DoesNotExist:
            pass
        return f"Job {job_id} failed: {str(e)}"