import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import HardwareScanner, ScannerEventLog, ProductionOrder, StationTrackingLog

@csrf_exempt
def scanner_event_webhook(request):
    """
    Accepts POST requests from physical hardware scanners.
    Expected Payload:
    {
        "mac_address": "00:1B:44:11:3A:B7",
        "event_type": "check_in", # or "check_out"
        "scanned_barcode": "WO-12345"
    }
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        mac_address = data.get('mac_address')
        event_type = data.get('event_type')
        barcode = data.get('scanned_barcode')

        if not all([mac_address, event_type, barcode]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        # Find Scanner
        try:
            scanner = HardwareScanner.objects.get(mac_address=mac_address)
        except HardwareScanner.DoesNotExist:
            return JsonResponse({"error": "Scanner not registered"}, status=404)

        # Log ping
        scanner.last_ping = timezone.now()
        scanner.save(update_fields=['last_ping'])

        # Find Order
        production_order = ProductionOrder.objects.filter(order_number=barcode).first()

        # Create raw event log
        event_log = ScannerEventLog.objects.create(
            scanner=scanner,
            event_type=event_type,
            scanned_barcode=barcode,
            production_order=production_order
        )

        if not production_order:
            event_log.error_message = "Production Order not found"
            event_log.processed = True
            event_log.save(update_fields=['error_message', 'processed'])
            return JsonResponse({"error": "Production Order not found", "log_id": event_log.id}, status=404)

        if not scanner.assigned_station:
            event_log.error_message = "Scanner has no assigned station"
            event_log.processed = True
            event_log.save(update_fields=['error_message', 'processed'])
            return JsonResponse({"error": "Scanner misconfigured"}, status=400)

        # Process Logic
        if event_type == 'check_in':
            # Create StationTrackingLog entry
            StationTrackingLog.objects.create(
                production_order=production_order,
                station=scanner.assigned_station,
                entered_at=timezone.now()
            )
            # Update current station on ProductionOrder
            production_order.current_station = scanner.assigned_station
            production_order.save(update_fields=['current_station'])
        
        elif event_type == 'check_out':
            # Find active log and close it
            active_log = StationTrackingLog.objects.filter(
                production_order=production_order,
                station=scanner.assigned_station,
                exited_at__isnull=True
            ).last()

            if active_log:
                active_log.exited_at = timezone.now()
                active_log.save(update_fields=['exited_at'])
            else:
                event_log.error_message = "No active check-in found for this station"
                event_log.save(update_fields=['error_message'])

        event_log.processed = True
        event_log.save(update_fields=['processed'])

        return JsonResponse({"status": "success", "log_id": event_log.id})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
