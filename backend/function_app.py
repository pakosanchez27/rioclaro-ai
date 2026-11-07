import azure.functions as func
import json
from datetime import datetime, timezone

app = func.FunctionApp(
    http_auth_level=func.AuthLevel.ANONYMOUS
)


@app.route(
    route="health",
    methods=["GET"]
)
def health(req: func.HttpRequest) -> func.HttpResponse:

    response = {
        "status": "ok",
        "service": "Río Claro AI API",
        "version": "0.2.0",
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }

    return func.HttpResponse(
        body=json.dumps(response, ensure_ascii=False),
        status_code=200,
        mimetype="application/json"
    )