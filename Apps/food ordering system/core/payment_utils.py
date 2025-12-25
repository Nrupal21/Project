"""
Payment utility functions for Razorpay integration.
Handles payment order creation, verification, and processing.
"""
import razorpay
import hmac
import hashlib
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


# Initialize Razorpay client with API credentials from settings
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_razorpay_order(amount, order_id, receipt_id=None):
    """
    Create a Razorpay payment order for online payment processing.
    
    This function initializes a payment order with Razorpay's payment gateway.
    The order must be created before showing the payment interface to the customer.
    
    Workflow:
    1. Convert amount to paise (Razorpay requires amount in smallest currency unit)
    2. Prepare order data with amount, currency, and receipt
    3. Call Razorpay API to create order
    4. Return order details for frontend payment integration
    
    Args:
        amount (Decimal or float): Order amount in rupees
        order_id (str): Unique order identifier from our system
        receipt_id (str, optional): Custom receipt ID for tracking
    
    Returns:
        dict: Razorpay order response containing:
            - id: Razorpay order ID (required for payment)
            - entity: 'order'
            - amount: Amount in paise
            - currency: 'INR'
            - receipt: Receipt identifier
            - status: 'created'
            - created_at: Timestamp
    
    Raises:
        razorpay.errors.BadRequestError: If order parameters are invalid
        razorpay.errors.ServerError: If Razorpay server error occurs
    
    Example:
        >>> order = create_razorpay_order(499.50, 'ORD123', 'RECEIPT001')
        >>> print(order['id'])  # rzp_order_xxxxxxxxxxxxx
    
    Note:
        - Amount is automatically converted to paise (multiply by 100)
        - Currency is hardcoded to INR (Indian Rupees)
        - Receipt ID defaults to order_id if not provided
        - Order expires after RAZORPAY_PAYMENT_TIMEOUT (default: 15 minutes)
    """
    try:
        # Convert amount to paise (1 Rupee = 100 paise)
        # Razorpay requires amount in smallest currency unit
        amount_in_paise = int(float(amount) * 100)
        
        # Use provided receipt ID or fallback to order ID
        if not receipt_id:
            receipt_id = str(order_id)
        
        # Prepare order data for Razorpay API
        order_data = {
            'amount': amount_in_paise,  # Amount in paise
            'currency': settings.RAZORPAY_CURRENCY,  # 'INR'
            'receipt': receipt_id,  # Receipt identifier for tracking
            'payment_capture': 1,  # Auto-capture payment (1 = automatic, 0 = manual)
            'notes': {
                'order_id': str(order_id),  # Store our internal order ID
                'created_at': timezone.now().isoformat(),  # Timestamp for reference
            }
        }
        
        # Create order via Razorpay API
        razorpay_order = razorpay_client.order.create(data=order_data)
        
        return razorpay_order
        
    except razorpay.errors.BadRequestError as e:
        # Invalid parameters or configuration error
        print(f"Razorpay BadRequestError while creating order: {e}")
        raise
    except razorpay.errors.ServerError as e:
        # Razorpay server-side error
        print(f"Razorpay ServerError while creating order: {e}")
        raise
    except Exception as e:
        # Unexpected error
        print(f"Unexpected error while creating Razorpay order: {e}")
        raise


def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verify Razorpay payment signature for security and authenticity.
    
    This is a critical security function that verifies the payment was actually
    processed by Razorpay and not tampered with. It uses HMAC-SHA256 signature
    verification to ensure payment authenticity.
    
    Security Process:
    1. Construct signature payload from order_id and payment_id
    2. Generate HMAC-SHA256 hash using Razorpay secret key
    3. Compare generated signature with received signature
    4. Return verification result
    
    Args:
        razorpay_order_id (str): Razorpay order ID (starts with 'order_')
        razorpay_payment_id (str): Razorpay payment ID (starts with 'pay_')
        razorpay_signature (str): Payment signature from Razorpay callback
    
    Returns:
        bool: True if signature is valid, False otherwise
    
    Security Note:
        CRITICAL: This verification MUST be performed server-side.
        Never trust payment data without signature verification.
        Client-side verification can be bypassed by attackers.
    
    Example:
        >>> is_valid = verify_razorpay_payment(
        ...     'order_xxxxx',
        ...     'pay_yyyyy',
        ...     'signature_hash_here'
        ... )
        >>> if is_valid:
        ...     # Process order and mark as paid
        ...     pass
    
    Technical Details:
        - Uses HMAC-SHA256 for signature generation
        - Secret key from settings.RAZORPAY_KEY_SECRET
        - Signature format: order_id|payment_id
        - Constant-time comparison prevents timing attacks
    """
    try:
        # Construct the expected signature payload
        # Format: razorpay_order_id|razorpay_payment_id
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        
        # Generate HMAC-SHA256 signature using secret key
        # This proves the payment data came from Razorpay
        generated_signature = hmac.new(
            key=settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Compare signatures using constant-time comparison
        # Prevents timing attacks that could reveal signature
        is_valid = hmac.compare_digest(
            generated_signature,
            razorpay_signature
        )
        
        return is_valid
        
    except Exception as e:
        # Log error and return False for safety
        print(f"Error verifying Razorpay signature: {e}")
        return False


def get_payment_details(payment_id):
    """
    Fetch complete payment details from Razorpay.
    
    Retrieves comprehensive payment information including status, amount,
    method used, and timestamps. Useful for verification and record-keeping.
    
    Args:
        payment_id (str): Razorpay payment ID to fetch details for
    
    Returns:
        dict: Payment details containing:
            - id: Payment ID
            - entity: 'payment'
            - amount: Amount in paise
            - currency: 'INR'
            - status: Payment status (captured, authorized, failed, etc.)
            - method: Payment method (card, netbanking, wallet, upi)
            - email: Customer email
            - contact: Customer phone
            - created_at: Timestamp
            - And other payment-specific fields
    
    Raises:
        razorpay.errors.BadRequestError: If payment ID is invalid
        razorpay.errors.ServerError: If Razorpay server error occurs
    
    Example:
        >>> payment = get_payment_details('pay_xxxxxxxxxxxxx')
        >>> print(payment['status'])  # 'captured'
        >>> print(payment['method'])  # 'upi'
    
    Use Cases:
        - Verify payment status before order fulfillment
        - Store payment method for analytics
        - Reconcile payments with bank statements
        - Customer support and dispute resolution
    """
    try:
        # Fetch payment details from Razorpay API
        payment = razorpay_client.payment.fetch(payment_id)
        return payment
        
    except razorpay.errors.BadRequestError as e:
        print(f"Razorpay BadRequestError while fetching payment: {e}")
        raise
    except razorpay.errors.ServerError as e:
        print(f"Razorpay ServerError while fetching payment: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while fetching payment details: {e}")
        raise


def refund_payment(payment_id, amount=None, notes=None):
    """
    Process a refund for a Razorpay payment.
    
    Creates a refund request for a captured payment. Can refund full amount
    or partial amount. Used for order cancellations and dispute resolutions.
    
    Args:
        payment_id (str): Razorpay payment ID to refund
        amount (int, optional): Amount to refund in paise. None for full refund.
        notes (dict, optional): Additional notes about the refund
    
    Returns:
        dict: Refund details containing:
            - id: Refund ID
            - entity: 'refund'
            - amount: Refunded amount in paise
            - payment_id: Original payment ID
            - status: Refund status
            - created_at: Timestamp
    
    Raises:
        razorpay.errors.BadRequestError: If refund parameters are invalid
        razorpay.errors.ServerError: If Razorpay server error occurs
    
    Example:
        >>> # Full refund
        >>> refund = refund_payment('pay_xxxxx')
        >>> 
        >>> # Partial refund (500 rupees)
        >>> refund = refund_payment('pay_xxxxx', amount=50000)
    
    Note:
        - Refunds are processed within 5-7 business days
        - Amount must be in paise (multiply by 100)
        - Partial refunds allowed for captured payments
        - Refund updates order payment_status to 'refunded'
    """
    try:
        # Prepare refund data
        refund_data = {}
        
        if amount is not None:
            # Partial refund - amount in paise
            refund_data['amount'] = amount
        # If amount is None, full refund is processed
        
        if notes:
            refund_data['notes'] = notes
        
        # Create refund via Razorpay API
        refund = razorpay_client.payment.refund(payment_id, refund_data)
        
        return refund
        
    except razorpay.errors.BadRequestError as e:
        print(f"Razorpay BadRequestError while processing refund: {e}")
        raise
    except razorpay.errors.ServerError as e:
        print(f"Razorpay ServerError while processing refund: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error while processing refund: {e}")
        raise


def convert_to_rupees(amount_in_paise):
    """
    Convert amount from paise to rupees.
    
    Razorpay returns amounts in paise (smallest currency unit).
    This helper function converts to rupees for display and storage.
    
    Args:
        amount_in_paise (int): Amount in paise
    
    Returns:
        Decimal: Amount in rupees with 2 decimal places
    
    Example:
        >>> rupees = convert_to_rupees(49950)
        >>> print(rupees)  # Decimal('499.50')
    """
    return Decimal(amount_in_paise) / Decimal(100)


def convert_to_paise(amount_in_rupees):
    """
    Convert amount from rupees to paise.
    
    Razorpay requires amounts in paise (smallest currency unit).
    This helper function converts from rupees for API calls.
    
    Args:
        amount_in_rupees (Decimal or float): Amount in rupees
    
    Returns:
        int: Amount in paise
    
    Example:
        >>> paise = convert_to_paise(499.50)
        >>> print(paise)  # 49950
    """
    return int(float(amount_in_rupees) * 100)
