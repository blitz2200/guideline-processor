from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes
from .models import Job
from .serializers import JobCreateSerializer, JobResponseSerializer, JobCreateResponseSerializer
from .tasks import process_guideline_job


@extend_schema(
    operation_id='create_job',
    request=JobCreateSerializer,
    responses={200: JobCreateResponseSerializer},
    description='Create a new guideline processing job'
)
@api_view(['POST'])
def create_job(request):
    """
    POST /jobs - Create a new guideline processing job
    Returns event_id in <200ms
    """
    serializer = JobCreateSerializer(data=request.data)
    if serializer.is_valid():
        # Create job record
        job = Job.objects.create(
            input_data=serializer.validated_data['guideline_text']
        )

        # Queue the processing task
        process_guideline_job.delay(str(job.event_id))

        response_data = {
            'event_id': job.event_id,
            'status': job.status
        }

        return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id='get_job',
    parameters=[
        OpenApiParameter(
            name='event_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='Job event ID'
        )
    ],
    responses={200: JobResponseSerializer, 404: None},
    description='Get job status and result by event_id'
)
@api_view(['GET'])
def get_job(request, event_id):
    """
    GET /jobs/{event_id} - Get job status and result
    """
    try:
        job = Job.objects.get(event_id=event_id)
        serializer = JobResponseSerializer(job)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Job.DoesNotExist:
        return Response(
            {'error': 'Job not found'},
            status=status.HTTP_404_NOT_FOUND
        )