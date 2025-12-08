"""
Custom session serializer to handle UUID objects
"""
import json
import uuid
from django.core.signing import JSONSerializer


class UUIDJSONSerializer(JSONSerializer):
    """
    Custom JSON serializer that can handle UUID objects
    """
    def dumps(self, obj):
        return json.dumps(obj, separators=(',', ':'), cls=UUIDEncoder).encode('latin-1')


class UUIDEncoder(json.JSONEncoder):
    """
    JSON encoder that converts UUID objects to strings
    """
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)
