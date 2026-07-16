from bson import ObjectId


def serialize_doc(doc):
    """Convert a MongoDB document into a JSON-serializable dict.

    - Converts ObjectId values to strings.
    - Converts nested dicts and lists recursively.
    - Renames `_id` to `id`.
    """
    if isinstance(doc, dict):
        serialized = {}
        for key, value in doc.items():
            if key == "_id":
                serialized["id"] = str(value)
            elif isinstance(value, ObjectId):
                serialized[key] = str(value)
            elif isinstance(value, dict):
                serialized[key] = serialize_doc(value)
            elif isinstance(value, list):
                serialized[key] = [serialize_doc(item) if isinstance(item, dict) else str(item) if isinstance(item, ObjectId) else item for item in value]
            else:
                serialized[key] = value
        return serialized
    return doc


def success_response(data=None, message="Success"):
    """Standardized success response format."""
    return {"success": True, "message": message, "data": data}