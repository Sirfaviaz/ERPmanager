from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.db import IntegrityError
from datetime import datetime

from .forms import BillUploadForm
from .models import Order, OrderItem
from .utils import extract_order_data
from .helpers import compute_order_from
from .google_services import update_google_sheet_user_layout
import tempfile


def parse_flexible_date(date_str):
    formats = ["%B %d, %Y", "%b %d, %Y", "%b. %d, %Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


# 1. Upload & Extract

def extract_order_view(request):
    context = {}
    if request.method == 'POST':
        form = BillUploadForm(request.POST, request.FILES)
        if form.is_valid():
            bill_file = form.cleaned_data['bill_file']
            try:
                data, bill_type = extract_order_data(bill_file)
                data["order_type"] = compute_order_from(data.get("order_type", ""), data.get("order_for", ""))
                context['order_data'] = data
                context['bill_type'] = bill_type
            except Exception as e:
                context['error'] = f"❌ Extraction failed: {str(e)}"
        else:
            context['error'] = "❌ Invalid form submission."
    else:
        form = BillUploadForm()

    context['form'] = form
    return render(request, 'orders/upload.html', context)


# 2. Save Extracted Order

@require_POST
def save_order_view(request):
    try:
        order_type = request.POST.get("order_type", "").strip()
        customer_name = request.POST.get("customer_name", "").strip()
        customer_address = request.POST.get("customer_address", "").strip()
        customer_phone = request.POST.get("customer_phone", "").strip()
        order_number = request.POST.get("order_number", "").strip()
        order_date_raw = request.POST.get("order_date", "").strip()
        google_location = request.POST.get("google_location", "").strip()
        items_count = int(request.POST.get("items-count", 0))

        order_date = parse_flexible_date(order_date_raw)

        if not order_type or not order_number or not order_date or items_count == 0:
            return JsonResponse({"success": False, "error": "❌ Missing required order fields (type, number, date, or items)."})

        if Order.objects.filter(order_number=order_number).exists():
            return JsonResponse({"success": False, "error": f"❌ Order with number '{order_number}' already exists."})

        order = Order.objects.create(
            source=order_type,
            customer_name=customer_name,
            customer_address=customer_address,
            customer_phone=customer_phone,
            google_location=google_location,
            order_number=order_number,
            order_date=order_date,
            is_delivered=False,
        )

        for i in range(items_count):
            product_name = request.POST.get(f"items-{i}-item_name", "").strip()
            quantity = int(request.POST.get(f"items-{i}-quantity", 1))
            selling_price = request.POST.get(f"items-{i}-selling_price", 0.0)

            if product_name:
                OrderItem.objects.create(
                    order=order,
                    product_name=product_name,
                    quantity=quantity,
                    selling_price=selling_price,
                )

        return JsonResponse({"success": True, "message": "✅ Order and items saved successfully!"})

    except Exception as e:
        return JsonResponse({"success": False, "error": f"❌ Failed to save: {str(e)}"})


# 3. Order List View

def order_list_view(request):
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    orders = Order.objects.all()

    if query:
        orders = orders.filter(
            Q(customer_name__icontains=query) |
            Q(order_number__icontains=query) |
            Q(customer_phone__icontains=query)
        )

    if start_date:
        orders = orders.filter(order_date__gte=start_date)

    if end_date:
        orders = orders.filter(order_date__lte=end_date)

    orders = orders.prefetch_related('items').order_by('-order_date')

    return render(request, 'orders/order_list.html', {
        'orders': orders,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
    })


# 4. Update Order

@require_POST
def update_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.customer_name = request.POST.get("customer_name", "")
    order.customer_phone = request.POST.get("customer_phone", "")
    order.customer_address = request.POST.get("customer_address", "")
    order.order_number = request.POST.get("order_number", "")
    order.order_date = request.POST.get("order_date") or None
    order.is_delivered = "is_delivered" in request.POST
    order.save()

    try:
        items_count = int(request.POST.get("items_count", 0))
    except:
        items_count = 0

    for i in range(items_count):
        item_id = request.POST.get(f"item_{i}_id")
        if item_id:
            try:
                item = OrderItem.objects.get(id=item_id, order=order)
                item.product_name = request.POST.get(f"item_{i}_name", "")
                item.quantity = int(request.POST.get(f"item_{i}_qty", 1))
                item.selling_price = request.POST.get(f"item_{i}_price") or None
                item.save()
            except OrderItem.DoesNotExist:
                continue

    return redirect("orders:order_list")


# 5. Delete Order

@require_POST
def delete_order_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect("orders:order_list")


# 6. Mark Delivered

@require_POST
def mark_order_delivered(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if not order.is_delivered:
        order.is_delivered = True
        order.save()
        messages.success(request, f"✅ Order #{order.order_number} marked as delivered.")
    else:
        messages.info(request, f"ℹ️ Order #{order.order_number} is already delivered.")
    return redirect("orders:order_list")


# 7. Push to Google Sheets

@require_POST
def push_to_google_sheet_view(request):
    import json
    try:
        credentials_file = request.FILES.get("credentials_file")
        spreadsheet_name = request.POST.get("spreadsheet_name")
        worksheet_name = request.POST.get("worksheet_name")
        order_data_raw = request.POST.get("data")

        if not (credentials_file and spreadsheet_name and worksheet_name and order_data_raw):
            return JsonResponse({"success": False, "error": "Missing required fields."})

        order_data = json.loads(order_data_raw)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as temp_cred:
            for chunk in credentials_file.chunks():
                temp_cred.write(chunk)
            credentials_path = temp_cred.name

        result = update_google_sheet_user_layout(
            data=order_data,
            credentials_path=credentials_path,
            spreadsheet_name=spreadsheet_name,
            worksheet_name=worksheet_name
        )

        return JsonResponse({"success": True, "message": f"✅ Google Sheet updated! Serial: {result.get('next_sl')}"})

    except Exception as e:
        return JsonResponse({"success": False, "error": f"❌ Google Sheet push failed: {str(e)}"})



from django.shortcuts import render
from django.http import JsonResponse
from .models import OrderItem
from .erp.client import ERPClient
import requests


def erp_item_search_page(request):
    """
    Render the ERP item search and testing page with sample local DB items.
    """
    db_items = OrderItem.objects.values("product_name").distinct()[:50]
    return render(request, "orders/test_erp_item_match.html", {"db_items": db_items})


def erp_item_details(request):
    """
    Fetch detailed info and warehouse-wise stock for an ERP item.
    """
    code = request.GET.get("code", "")
    if not code:
        return JsonResponse({"success": False, "error": "No item code provided."})

    client = ERPClient()

    try:
        # Fetch item details from ERP
        item_url = f"{client.base_url}/api/resource/Item/{code}"
        item_res = requests.get(item_url, headers=client._headers())
        item_res.raise_for_status()
        item_data = item_res.json().get("data", {})

        # Fetch stock list from ERP
        stock_list = client.get_item_stock(code)

        stock_by_warehouse = []
        total_qty = 0
        highest_price = 0

        for stock in stock_list:
            qty = stock.get("actual_qty", 0)
            rate = stock.get("valuation_rate", 0)
            warehouse = stock.get("warehouse", "Unknown")

            stock_by_warehouse.append({
                "warehouse": warehouse,
                "qty": qty,
                "valuation_rate": rate
            })

            total_qty += qty
            if rate > highest_price:
                highest_price = rate

        return JsonResponse({
            "success": True,
            "item_code": code,
            "item_name": item_data.get("item_name", ""),
            "item_group": item_data.get("item_group", ""),
            "total_qty": total_qty,
            "highest_valuation_rate": highest_price,
            "stock_by_warehouse": stock_by_warehouse,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": f"❌ ERP Error: {str(e)}"})


def erp_item_suggestions(request):
    """
    Return live search suggestions for items from ERP.
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    client = ERPClient()
    items = client.search_items(query)

    suggestions = [
        {"label": item["item_name"], "value": item["item_code"]}
        for item in items
    ]
    return JsonResponse({"results": suggestions})
