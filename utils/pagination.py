def paginate(request, items, default_limit=10):
    """
    Paginate a list of items using query parameters: 'page' and 'limit'.

    Args:
        request (Flask Request): The incoming HTTP request with query parameters.
        items (list): The list of items to paginate.
        default_limit (int): Default number of items per page if not specified.

    Returns:
        dict: Contains paginated data and metadata.
    """
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", default_limit))
        if page < 1 or limit < 1:
            raise ValueError
    except ValueError:
        page = 1
        limit = default_limit

    start = (page - 1) * limit
    end = start + limit
    total_items = len(items)
    total_pages = (total_items + limit - 1) // limit

    return {
        "data": items[start:end],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total_items,
            "total_pages": total_pages,
        },
    }
