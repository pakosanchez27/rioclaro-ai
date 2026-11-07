import azure.functions as func
import json
from datetime import datetime, timezone

from database.connection import initialize_database
from repositories.invoices import (
    list_invoices,
    get_invoice,
    get_invoice_stats,
)

from repositories.invoice_reviews import list_invoice_reviews
from repositories.invoice_analyses import get_saved_invoice_analysis
from repositories.business_data import get_demo_options, get_branch_report
from repositories.complaints import create_complaint, get_complaint, ComplaintInputError
import logging

from azure.core.exceptions import HttpResponseError
from openai import APIError

from services.document_intelligence import (
    DocumentValidationError,
    InvoiceExtractionError,
    MAX_DOCUMENT_BYTES,
)
from services.invoice_pipeline import (
    analyze_and_save_invoice,
    IncompleteInvoiceError,
)
from services.invoice_duplicates import (
    DuplicateDocumentError,
    DuplicateBusinessError,
)
from services.ai_quota import QuotaExceededError, AiOperationDisabledError, get_quota_status
from services.business_assistant import ask_assistant, AssistantInputError
from services.invoice_review import (
    review_invoice,
    ReviewValidationError,
    InvoiceNotFoundError,
    InvoiceAlreadyReviewedError,
)
from security.evaluator_auth import login as evaluator_login, logout as evaluator_logout, validate_session, EvaluatorAuthError

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


@app.route(route="auth/evaluator/login", methods=["POST"])
def auth_evaluator_login(req: func.HttpRequest) -> func.HttpResponse:
    try:
        payload = req.get_json()
        code = payload.get("code") if isinstance(payload, dict) else None
        token, expires_at = evaluator_login(code)
        return func.HttpResponse(
            json.dumps({"access_token": f"ev_{token}", "expires_at": expires_at}),
            status_code=200, mimetype="application/json",
            headers={"Cache-Control": "no-store"},
        )
    except ValueError:
        return func.HttpResponse(json.dumps({"error": "Credencial incorrecta"}), status_code=400, mimetype="application/json")
    except EvaluatorAuthError as exc:
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=exc.status_code, mimetype="application/json")


@app.route(route="auth/evaluator/logout", methods=["POST"])
def auth_evaluator_logout(req: func.HttpRequest) -> func.HttpResponse:
    authorization = req.headers.get("Authorization", "")
    if not authorization.startswith("Bearer ev_"):
        return func.HttpResponse(json.dumps({"error": "Sesion expirada"}), status_code=401, mimetype="application/json")
    token = authorization[len("Bearer ev_"):]
    try:
        validate_session(token)
        evaluator_logout(token)
    except EvaluatorAuthError as exc:
        return func.HttpResponse(json.dumps({"error": str(exc)}), status_code=exc.status_code, mimetype="application/json")
    return func.HttpResponse(status_code=204)


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


@app.route(route="assistant/ask", methods=["POST"])
def assistant_ask(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "assistant:ask")
    if error is not None:
        return error

    try:
        body = req.get_json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        return func.HttpResponse(
            json.dumps({"error": "Se esperaba un objeto JSON"}),
            status_code=400, mimetype="application/json",
        )

    try:
        result = ask_assistant(body.get("message"), body.get("conversation_id"))
    except AssistantInputError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}, ensure_ascii=False),
            status_code=400, mimetype="application/json",
        )
    except QuotaExceededError as exc:
        return func.HttpResponse(
            json.dumps({"error": "Cuota diaria del asistente agotada. Intenta de nuevo tras el reinicio.",
                        "resets_at": exc.resets_at,
                        "retry_after_seconds": exc.retry_after_seconds}),
            status_code=429, mimetype="application/json",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )
    except (AiOperationDisabledError, RuntimeError):
        return func.HttpResponse(
            json.dumps({"error": "Asistente no disponible"}),
            status_code=503, mimetype="application/json",
        )
    except APIError:
        logging.error("Fallo el servicio de seleccion de consultas")
        return func.HttpResponse(
            json.dumps({"error": "No fue posible consultar Azure OpenAI"}),
            status_code=502, mimetype="application/json",
        )

    return func.HttpResponse(
        json.dumps(result, ensure_ascii=False),
        status_code=200, mimetype="application/json",
    )


@app.route(route="assistant/quota", methods=["GET"])
def assistant_quota(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "assistant:ask")
    if error is not None:
        return error
    try:
        initialize_database()
        quota = get_quota_status("assistant")
    except AiOperationDisabledError:
        return func.HttpResponse(
            json.dumps({"error": "Cuota del asistente no disponible"}),
            status_code=503, mimetype="application/json",
        )
    return func.HttpResponse(
        json.dumps(quota), status_code=200, mimetype="application/json",
    )


@app.route(route="business/options", methods=["GET"])
def business_options(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "complaints:read")
    if error is not None:
        return error
    initialize_database()
    return func.HttpResponse(
        json.dumps(get_demo_options(), ensure_ascii=False),
        status_code=200, mimetype="application/json",
    )


@app.route(route="business/reports", methods=["GET"])
def business_reports(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "reports:read")
    if error is not None:
        return error
    initialize_database()
    return func.HttpResponse(
        json.dumps(get_branch_report(), ensure_ascii=False),
        status_code=200, mimetype="application/json",
    )


@app.route(route="complaints", methods=["POST"])
def complaints_create(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "complaints:write")
    if error is not None:
        return error
    try:
        body = req.get_json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        return func.HttpResponse(json.dumps({"error": "JSON inválido"}), status_code=400, mimetype="application/json")
    initialize_database()
    try:
        result = create_complaint(
            body.get("order_folio"), body.get("branch_code"),
            body.get("message"), body.get("category"),
        )
    except ComplaintInputError as exc:
        return func.HttpResponse(json.dumps({"error": str(exc)}, ensure_ascii=False), status_code=400, mimetype="application/json")
    return func.HttpResponse(json.dumps(result, ensure_ascii=False), status_code=201, mimetype="application/json")


@app.route(route="complaints/{folio}", methods=["GET"])
def complaints_detail(req: func.HttpRequest) -> func.HttpResponse:
    user, error = authorize(req, "complaints:read")
    if error is not None:
        return error
    initialize_database()
    result = get_complaint(req.route_params.get("folio", ""))
    if result is None:
        return func.HttpResponse(json.dumps({"error": "Queja no encontrada"}), status_code=404, mimetype="application/json")
    return func.HttpResponse(json.dumps(result, ensure_ascii=False), status_code=200, mimetype="application/json")

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
    # Algunos hosts resuelven /invoices/stats como la ruta parametrizada.
    # Conservar el contrato público y la autorización específica de stats.
    if req.route_params.get("factura_id") == "stats":
        return invoices_stats(req)

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


@app.route(
    route="invoices/{factura_id}/analysis",
    methods=["GET"],
)
def invoices_saved_analysis(
    req: func.HttpRequest,
) -> func.HttpResponse:
    user, error = authorize(req, "invoices:read")

    if error is not None:
        return error

    invoice_id = req.route_params.get("factura_id", "")

    initialize_database()

    invoice = get_invoice(invoice_id)
    if invoice is None:
        return func.HttpResponse(
            json.dumps({"error": "Factura no encontrada"}),
            status_code=404,
            mimetype="application/json",
        )

    saved_analysis = get_saved_invoice_analysis(invoice_id)

    return func.HttpResponse(
        json.dumps(
            {
                "invoice_id": invoice_id,
                "data": saved_analysis,
            },
            ensure_ascii=False,
        ),
        status_code=200,
        mimetype="application/json",
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
        
@app.route(
    route="invoices/{factura_id}/reviews",
    methods=["GET"],
)
def invoices_review_history(
    req: func.HttpRequest,
) -> func.HttpResponse:

    # Autenticacion y autorizacion obligatorias
    user, error = authorize(req, "invoices:review")

    if error is not None:
        return error

    invoice_id = req.route_params.get("factura_id", "")

    try:
        limit = int(req.params.get("limit", "50"))
        offset = int(req.params.get("offset", "0"))

        if limit < 1 or limit > 100 or offset < 0:
            raise ValueError()

    except (ValueError, TypeError):
        return func.HttpResponse(
            json.dumps({
                "error": "Parametros de paginacion invalidos"
            }),
            status_code=400,
            mimetype="application/json",
        )

    initialize_database()

    invoice = get_invoice(invoice_id)

    if invoice is None:
        return func.HttpResponse(
            json.dumps({
                "error": "Factura no encontrada"
            }),
            status_code=404,
            mimetype="application/json",
        )

    history = list_invoice_reviews(
        invoice_id=invoice_id,
        limit=limit,
        offset=offset,
    )

    return func.HttpResponse(
        json.dumps(
            {
                "invoice_id": invoice_id,
                "history": history["data"],
                "total": history["total"],
                "limit": history["limit"],
                "offset": history["offset"],
            },
            ensure_ascii=False,
        ),
        status_code=200,
        mimetype="application/json",
    )

@app.route(
    route="invoices/analyze",
    methods=["POST"],
)
def invoices_analyze(req: func.HttpRequest) -> func.HttpResponse:

    # La seguridad se valida antes de leer o procesar
    # el documento.
    user, error = authorize(req, "invoices:analyze")

    if error is not None:
        return error

    content_type = (
        req.headers.get("Content-Type", "")
        .split(";")[0]
        .strip()
        .lower()
    )

    supported_types = {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }

    if content_type not in supported_types:
        return func.HttpResponse(
            json.dumps({
                "error": "Formato no admitido. Usa PDF, PNG o JPEG."
            }),
            status_code=415,
            mimetype="application/json",
        )

    content_length = req.headers.get("Content-Length")

    if content_length:
        try:
            if int(content_length) > MAX_DOCUMENT_BYTES:
                return func.HttpResponse(
                    json.dumps({
                        "error": "El archivo supera 4 MB."
                    }),
                    status_code=413,
                    mimetype="application/json",
                )
        except ValueError:
            return func.HttpResponse(
                json.dumps({
                    "error": "Content-Length invalido."
                }),
                status_code=400,
                mimetype="application/json",
            )

    document_bytes = req.get_body()

    if len(document_bytes) > MAX_DOCUMENT_BYTES:
        return func.HttpResponse(
            json.dumps({
                "error": "El archivo supera 4 MB."
            }),
            status_code=413,
            mimetype="application/json",
        )

    try:
        result = analyze_and_save_invoice(document_bytes)

        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            status_code=201,
            mimetype="application/json",
        )

    except DocumentValidationError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=400,
            mimetype="application/json",
        )

    except (DuplicateDocumentError, DuplicateBusinessError) as exc:
        related_invoice_id = getattr(exc, "invoice_id", None) or getattr(
            exc, "related_invoice_id", None
        )
        return func.HttpResponse(
            json.dumps({
                "error": str(exc),
                "related_invoice_id": related_invoice_id,
            }),
            status_code=409,
            mimetype="application/json",
        )

    except QuotaExceededError as exc:
        return func.HttpResponse(
            json.dumps({"error": "Cuota diaria de análisis agotada. Intenta de nuevo tras el reinicio.",
                        "resets_at": exc.resets_at,
                        "retry_after_seconds": exc.retry_after_seconds}),
            status_code=429,
            mimetype="application/json",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        )

    except AiOperationDisabledError as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=503,
            mimetype="application/json",
        )

    except (IncompleteInvoiceError, InvoiceExtractionError) as exc:
        return func.HttpResponse(
            json.dumps({"error": str(exc)}),
            status_code=422,
            mimetype="application/json",
        )

    except (HttpResponseError, APIError) as exc:
        logging.error(
            "Fallo el servicio de IA: %s",
            type(exc).__name__,
        )

        return func.HttpResponse(
            json.dumps({
                "error": "No fue posible completar el analisis."
            }),
            status_code=502,
            mimetype="application/json",
        )
