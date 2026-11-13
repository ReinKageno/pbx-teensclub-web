from fastapi import HTTPException


async def common_id_limit_parameters(id: int | None = None, limit: int | None = 1):
    if 1 <= limit <= 100:
        _limit = limit
    else:
        raise HTTPException(
            status_code=422,
            detail=[{"msg":"'limit' out of range", "input":limit}]
        )
    
    return {"target_id": id, "limit": _limit}