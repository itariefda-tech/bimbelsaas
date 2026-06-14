from datetime import date

from flask import Blueprint, g, request

from app.common.errors import ValidationError
from app.common.responses import success_response
from app.common.validation import json_payload, optional_string, required_positive_int, required_string, required_uuid
from app.permissions.decorators import require_auth
from app.services.financial_service import FinancialService

financial_api = Blueprint("financial", __name__)


@financial_api.post("/financial/invoices")
@require_auth
def create_invoice():
    payload = json_payload()
    try:
        due_date = date.fromisoformat(required_string(payload, "due_date"))
    except ValueError as error:
        raise ValidationError("due_date must use YYYY-MM-DD format.") from error
    invoice = FinancialService().create_invoice(
        g.principal,
        academy_id=required_uuid(payload.get("academy_id"), "academy_id"),
        branch_id=required_uuid(payload.get("branch_id"), "branch_id"),
        student_id=required_uuid(payload.get("student_id"), "student_id"),
        invoice_number=required_string(payload, "invoice_number"),
        description=required_string(payload, "description"),
        amount_minor=required_positive_int(payload, "amount_minor"),
        due_date=due_date,
        notes=optional_string(payload, "notes"),
    )
    return success_response(data=FinancialService.serialize_invoice(invoice), message="Invoice created.", status=201)


@financial_api.patch("/financial/invoices/<uuid:invoice_id>/issue")
@require_auth
def issue_invoice(invoice_id):
    invoice = FinancialService().issue(g.principal, invoice_id)
    return success_response(data=FinancialService.serialize_invoice(invoice), message="Invoice issued.")


@financial_api.patch("/financial/invoices/<uuid:invoice_id>/cancel")
@require_auth
def cancel_invoice(invoice_id):
    invoice = FinancialService().cancel(
        g.principal, invoice_id, required_string(json_payload(), "reason")
    )
    return success_response(data=FinancialService.serialize_invoice(invoice), message="Invoice cancelled.")


@financial_api.get("/financial/invoices/<uuid:invoice_id>")
@require_auth
def invoice_detail(invoice_id):
    return success_response(data=FinancialService().get_invoice(g.principal, invoice_id), message="Invoice loaded.")


@financial_api.post("/financial/invoices/<uuid:invoice_id>/payments")
@require_auth
def submit_payment(invoice_id):
    payload = json_payload()
    proof = payload.get("proof")
    if not isinstance(proof, dict):
        raise ValidationError("proof must be an object.")
    payment = FinancialService().submit_payment(
        g.principal,
        invoice_id,
        reference_number=required_string(payload, "reference_number"),
        amount_minor=required_positive_int(payload, "amount_minor"),
        method=required_string(payload, "method"),
        proof=proof,
    )
    return success_response(data=FinancialService.serialize_payment(payment), message="Payment proof submitted.", status=201)


@financial_api.patch("/financial/payments/<uuid:payment_id>/decision")
@require_auth
def decide_payment(payment_id):
    payload = json_payload()
    approve = payload.get("approve")
    if not isinstance(approve, bool):
        raise ValidationError("approve must be a boolean.")
    payment = FinancialService().decide_payment(
        g.principal, payment_id, approve=approve, reason=optional_string(payload, "reason")
    )
    return success_response(data=FinancialService.serialize_payment(payment), message="Payment decision recorded.")


@financial_api.get("/parent/invoices")
@require_auth
def parent_invoices():
    academy_id = g.principal.user.academy_id
    if academy_id is None:
        raise ValidationError("An academy is required.")
    data = FinancialService().list_parent_invoices(g.principal, academy_id)
    return success_response(data=data, message="Parent invoices loaded.", meta={"count": len(data)})
