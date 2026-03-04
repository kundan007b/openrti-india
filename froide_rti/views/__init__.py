import hmac
import hashlib
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _

import razorpay

from ..models import RTIPayment

logger = logging.getLogger(__name__)

RTI_FEE_AMOUNT = 1000  # ₹10 in paise (Razorpay uses paise)


@login_required
def initiate_payment(request, foirequest_pk):
    """
    Initiate Razorpay payment for RTI application fee (₹10).
    RTI Act 2005, Section 6(1).
    """
    from foirequest.models import FoiRequest

    foirequest = get_object_or_404(FoiRequest, pk=foirequest_pk, user=request.user)

    # Check if payment already exists
    payment, created = RTIPayment.objects.get_or_create(foirequest=foirequest)

    if payment.status == "completed" or payment.is_bpl_exempt:
        return redirect("foirequest-show", slug=foirequest.slug)

    if payment.is_bpl_exempt:
        return render(request, "froide_rti/payment_exempt.html", {"foirequest": foirequest})

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    razorpay_order = client.order.create(
        {
            "amount": RTI_FEE_AMOUNT,
            "currency": "INR",
            "receipt": f"rti_{foirequest.pk}",
            "notes": {
                "foirequest_id": str(foirequest.pk),
                "applicant": request.user.get_full_name() or request.user.username,
            },
        }
    )

    payment.razorpay_order_id = razorpay_order["id"]
    payment.save()

    context = {
        "foirequest": foirequest,
        "payment": payment,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": RTI_FEE_AMOUNT,
        "amount_display": "₹10",
        "user_name": request.user.get_full_name() or request.user.username,
        "user_email": request.user.email,
    }
    return render(request, "froide_rti/payment.html", context)


@csrf_exempt
@require_POST
def verify_payment(request):
    """
    Verify Razorpay payment signature after successful payment.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
        return JsonResponse({"error": "Missing payment data"}, status=400)

    # Verify signature
    message = f"{razorpay_order_id}|{razorpay_payment_id}"
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, razorpay_signature):
        logger.warning(f"Invalid Razorpay signature for order {razorpay_order_id}")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    try:
        payment = RTIPayment.objects.get(razorpay_order_id=razorpay_order_id)
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = "completed"
        payment.save()

        logger.info(f"RTI payment completed: {payment}")
        return JsonResponse({"status": "success", "redirect": payment.foirequest.get_absolute_url()})

    except RTIPayment.DoesNotExist:
        return JsonResponse({"error": "Payment record not found"}, status=404)


@login_required
def bpl_exemption(request, foirequest_pk):
    """
    Handle BPL (Below Poverty Line) fee exemption.
    RTI Act 2005: BPL applicants are exempt from the ₹10 fee.
    """
    from foirequest.models import FoiRequest

    foirequest = get_object_or_404(FoiRequest, pk=foirequest_pk, user=request.user)

    if request.method == "POST":
        certificate_number = request.POST.get("certificate_number", "").strip()
        certificate_file = request.FILES.get("certificate_file")

        if not certificate_number:
            return render(
                request,
                "froide_rti/bpl_exemption.html",
                {
                    "foirequest": foirequest,
                    "error": _("BPL certificate number is required."),
                },
            )

        payment, _ = RTIPayment.objects.get_or_create(foirequest=foirequest)
        payment.is_bpl_exempt = True
        payment.bpl_certificate_number = certificate_number
        payment.payment_method = "bpl_exempt"
        payment.status = "exempt"
        payment.amount = 0

        if certificate_file:
            payment.bpl_certificate_file = certificate_file

        payment.save()
        return redirect("foirequest-show", slug=foirequest.slug)

    return render(
        request,
        "froide_rti/bpl_exemption.html",
        {"foirequest": foirequest},
    )
