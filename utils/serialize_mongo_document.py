from datetime import datetime

from bson import ObjectId


def serialize_mongo_document(doc):
    """
    Converts MongoDB document's ObjectId and datetime fields to strings.
    """

    def convert(value):
        if isinstance(value, ObjectId):
            return str(value)
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert(item) for item in value]
        else:
            return value

    return convert(doc)
