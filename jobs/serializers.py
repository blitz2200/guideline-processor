from rest_framework import serializers
from .models import Job


class JobCreateSerializer(serializers.Serializer):
    guideline_text = serializers.CharField(max_length=10000, help_text="The guideline text to process")


class JobResponseSerializer(serializers.ModelSerializer):
    result = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ['event_id', 'status', 'result', 'created_at', 'updated_at']
        read_only_fields = ['event_id', 'status', 'created_at', 'updated_at']

    def get_result(self, obj):
        if obj.status == 'completed':
            return {
                'summary': obj.summary,
                'checklist': obj.checklist
            }
        elif obj.status == 'failed':
            return {
                'error': obj.error_message
            }
        return None


class JobCreateResponseSerializer(serializers.Serializer):
    event_id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)