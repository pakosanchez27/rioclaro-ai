import azure.functions as func
import json
from datetime import datetime, timezone

from database.connection import initialize_database
from repositories.invoices import (
    list_invoices,
    get_invoice,
    get_invoice_stats,
)

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

    
from security.auth_middleware import authorize


@app.route(
    route="auth/me",
    methods=["GET"],
)
def auth_me(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "invoices:read")

    if error is not None:
        return error

    return func.HttpResponse(
        json.dumps(user, ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )

@app.route(route="invoices", methods=["GET"])
def invoices_list(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "invoices:read")

    if error is not None:
        return error

    try:
        limit = int(req.params.get("limit", "50"))
        offset = int(req.params.get("offset", "0"))

        if not 1 <= limit <= 100 or offset < 0:
            raise ValueError()

    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Paginacion invalida"}),
            status_code=400,
            mimetype="application/json",
        )

    initialize_database()

    invoices = list_invoices(limit, offset)

    return func.HttpResponse(
        json.dumps({"data": invoices}, ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="invoices/stats", methods=["GET"])
def invoices_stats(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "invoices:stats")

    if error is not None:
        return error

    initialize_database()

    return func.HttpResponse(
        json.dumps(get_invoice_stats(), ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )


@app.route(
    route="invoices/{factura_id}",
    methods=["GET"],
)
def invoices_detail(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "invoices:read")

    if error is not None:
        return error

    initialize_database()

    invoice = get_invoice(req.route_params["factura_id"])

    if invoice is None:
        return func.HttpResponse(
            json.dumps({"error": "Factura no encontrada"}),
            status_code=404,
            mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(invoice, ensure_ascii=False),
        status_code=200,
        mimetype="application/json",
    )

    from services.invoice_review import (
    review_invoice,
    ReviewValidationError,
    InvoiceNotFoundError,
    InvoiceAlreadyReviewedError,
)

@app.route(route="invoices/review", methods=["POST"])
def invoices_review(req: func.HttpRequest) -> func.HttpResponse:

    user, error = authorize(req, "invoices:review")

    if error is not None:
        return error

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "JSON invalido"}),
            status_code=400,
            mimetype="application/json",
        )

    if not isinstance(body, dict):
        return func.HttpResponse(
            json.dumps({"error": "Se esperaba un objeto JSON"}),
            status_code=400,
            mimetype="application/json",
        )

    try:
        initialize_database()

        result = review_invoice(
            invoice_id=body.get("invoice_id"),
            decision=body.get("decision"),
            actor_oid=user["user_id"],
            notes=body.get("notes"),
        )

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            status_code=200,
            mimetype="application/json",
        )

    except ReviewValidationError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=400,
            mimetype="application/json",
        )

    except InvoiceNotFoundError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=404,
            mimetype="application/json",
        )

    except InvoiceAlreadyReviewedError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=409,
            mimetype="application/json",
        )