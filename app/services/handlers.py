
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse

from app.services.exceptions import AppError, ResourceNotFoundError, ResourceUnderConstructionError


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AppError)
    async def app_error_handler(
        request: Request,
        exc: AppError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )


    @app.exception_handler(ResourceUnderConstructionError)
    async def app_error_501_handler(
        request: Request,
        exc: ResourceUnderConstructionError,
    ) -> HTMLResponse:
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TeensClub - Home</title>
  <link rel="stylesheet" href="/static/css/default.css">
  <link rel="stylesheet" href="/static/css/addition.css">
  <script src="/static/js/script.js"></script>
</head>
<body>
  <main class="container">
    <div class="error-page d-flex justify-content-center flex-column">
      <h1>Oops, something is wrong!</h1>
      <h4>ErrCode: {exc.status_code} &mdash; {exc.msg}.</h4>
    </div>
  </main>
</body>
</html>
""",
            status_code=exc.status_code
        )


    @app.exception_handler(ResourceNotFoundError)
    async def app_error_404_handler(
        request: Request,
        exc: ResourceNotFoundError,
    ) -> HTMLResponse:
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TeensClub - Home</title>
  <link rel="stylesheet" href="/static/css/default.css">
  <link rel="stylesheet" href="/static/css/addition.css">
  <script src="/static/js/script.js"></script>
</head>
<body>
  <main class="container">
    <div class="error-page d-flex justify-content-center flex-column">
      <h1>Oops, something is wrong!</h1>
      <h4>ErrCode: {exc.status_code} &mdash; {exc.msg}.</h4>
    </div>
  </main>
</body>
</html>
"""
        )