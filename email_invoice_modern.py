"""
MODERN EMAIL INVOICE SYSTEM - Enhanced UI Version
Beautiful, modern email template with gradient backgrounds and improved styling
"""

import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Database Adapter (PostgreSQL or SQLite)
from db_adapter import get_db_connection

# Email Configuration from Environment Variables
EMAIL_CONFIG = {
    'SMTP_SERVER': os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('EMAIL_SMTP_PORT', '587')),
    'SENDER_EMAIL': os.getenv('EMAIL_SENDER', 'your-email@gmail.com'),
    'SENDER_PASSWORD': os.getenv('EMAIL_PASSWORD', 'your-app-password'),
    'SENDER_NAME': os.getenv('EMAIL_SENDER_NAME', 'Swippe Quick Commerce')
}

# Check if email is properly configured (both must be non-empty strings)
EMAIL_ENABLED = bool(EMAIL_CONFIG['SENDER_EMAIL'] and EMAIL_CONFIG['SENDER_PASSWORD'])

def generate_modern_invoice_html(order_data, order_items):
    """Generate beautiful modern HTML invoice"""
    
    order_date = datetime.fromisoformat(order_data['ordered_at']).strftime('%B %d, %Y at %I:%M %p')
    
    # Calculate totals
    subtotal = sum(item['sale_price'] * item['quantity'] for item in order_items)
    discount = sum((item['market_price'] - item['sale_price']) * item['quantity'] for item in order_items)
    delivery_fee = 0 if subtotal >= 199 else 40
    total = subtotal + delivery_fee
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #1f2937;
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                padding: 20px;
            }}
            .email-container {{
                max-width: 650px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 25px 70px rgba(0, 0, 0, 0.15);
            }}
            .header {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 50px 30px;
                text-align: center;
                position: relative;
            }}
            .header::before {{
                content: '🛒';
                font-size: 80px;
                position: absolute;
                opacity: 0.1;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
            }}
            .header h1 {{
                margin: 0;
                font-size: 42px;
                font-weight: 800;
                text-shadow: 0 3px 15px rgba(0, 0, 0, 0.3);
                letter-spacing: 2px;
                position: relative;
                z-index: 1;
            }}
            .header p {{
                margin: 12px 0 0 0;
                font-size: 18px;
                opacity: 0.95;
                font-weight: 500;
                position: relative;
                z-index: 1;
            }}
            .invoice-banner {{
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                padding: 30px;
                text-align: center;
                border-bottom: 4px solid #10b981;
            }}
            .invoice-banner h2 {{
                color: #059669;
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 8px;
            }}
            .invoice-banner .badge {{
                display: inline-block;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 8px 20px;
                border-radius: 25px;
                font-size: 14px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
                animation: pulse 2s ease-in-out infinite;
            }}
            @keyframes pulse {{
                0%, 100% {{ transform: scale(1); }}
                50% {{ transform: scale(1.05); }}
            }}
            .order-details {{
                padding: 30px;
                background: linear-gradient(135deg, #fafafa 0%, #f3f4f6 100%);
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
            }}
            .detail-box {{
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
                border-left: 4px solid #10b981;
            }}
            .detail-box strong {{
                display: block;
                color: #6b7280;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 6px;
            }}
            .detail-box span {{
                color: #059669;
                font-size: 18px;
                font-weight: 600;
            }}
            .section-title {{
                padding: 25px 30px 15px 30px;
                font-size: 20px;
                font-weight: 700;
                color: #374151;
                border-bottom: 3px solid #f0fdf4;
            }}
            .items-container {{
                padding: 0 30px 30px 30px;
            }}
            .item-card {{
                background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
                padding: 20px;
                margin-bottom: 15px;
                border-radius: 12px;
                border: 2px solid #f3f4f6;
                transition: all 0.3s ease;
            }}
            .item-card:hover {{
                border-color: #10b981;
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(16, 185, 129, 0.1);
            }}
            .item-header {{
                display: flex;
                justify-content: space-between;
                align-items: start;
                margin-bottom: 12px;
            }}
            .item-name {{
                font-size: 16px;
                font-weight: 600;
                color: #1f2937;
                flex: 1;
            }}
            .item-brand {{
                display: inline-block;
                background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
                color: #0369a1;
                padding: 4px 12px;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                margin-top: 6px;
            }}
            .item-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding-top: 12px;
                border-top: 2px dashed #e5e7eb;
            }}
            .item-price {{
                font-size: 18px;
                font-weight: 700;
                color: #059669;
            }}
            .item-quantity {{
                background: #f3f4f6;
                padding: 6px 14px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                color: #6b7280;
            }}
            .discount-badge {{
                background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
                color: #059669;
                padding: 4px 10px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            }}
            .totals-section {{
                padding: 30px;
                background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
            }}
            .totals-card {{
                background: white;
                padding: 30px;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }}
            .total-row {{
                display: flex;
                justify-content: space-between;
                padding: 12px 0;
                font-size: 16px;
            }}
            .total-row.savings {{
                color: #059669;
                font-weight: 600;
            }}
            .total-row.final {{
                border-top: 3px solid #10b981;
                padding-top: 20px;
                margin-top: 15px;
                font-size: 24px;
                font-weight: 800;
                color: #059669;
            }}
            .free-delivery {{
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border: 2px dashed #10b981;
                border-radius: 12px;
                padding: 15px;
                text-align: center;
                margin-top: 20px;
                color: #059669;
                font-weight: 600;
            }}
            .footer {{
                background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .footer h3 {{
                font-size: 24px;
                margin-bottom: 15px;
            }}
            .footer p {{
                margin: 10px 0;
                opacity: 0.9;
            }}
            .footer-links {{
                margin-top: 25px;
                padding-top: 25px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                font-size: 14px;
                opacity: 0.8;
            }}
            .highlight-text {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                color: #92400e;
                padding: 3px 8px;
                border-radius: 5px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <h1>SWIPPE</h1>
                <p>⚡ Lightning Fast Delivery in Minutes</p>
            </div>
            
            <!-- Success Banner -->
            <div class="invoice-banner">
                <h2>✅ Order Confirmed!</h2>
                <p style="margin: 10px 0 15px 0; color: #6b7280; font-size: 15px;">Your order has been confirmed and is being prepared</p>
                <span class="badge">Processing Now</span>
            </div>
            
            <!-- Order Details -->
            <div class="order-details">
                <div class="detail-box">
                    <strong>Order ID</strong>
                    <span>#{order_data['order_id']}</span>
                </div>
                <div class="detail-box">
                    <strong>Order Date</strong>
                    <span>{order_date}</span>
                </div>
            </div>
            
            <!-- Order Items -->
            <h3 class="section-title">📦 Your Order Items</h3>
            <div class="items-container">
    """
    
    # Add items
    for item in order_items:
        item_total = item['sale_price'] * item['quantity']
        discount_pct = 0
        if item['market_price'] > item['sale_price']:
            discount_pct = int((item['market_price'] - item['sale_price']) / item['market_price'] * 100)
        
        html += f"""
                <div class="item-card">
                    <div class="item-header">
                        <div>
                            <div class="item-name">{item['product_name'][:60]}</div>
                            <span class="item-brand">{item['brand']}</span>
                        </div>
                    </div>
                    <div class="item-footer">
                        <div>
                            <span class="item-price">₹{item['sale_price']:.0f}</span>
                            {f'<span class="discount-badge" style="margin-left: 8px;">{discount_pct}% OFF</span>' if discount_pct > 0 else ''}
                        </div>
                        <span class="item-quantity">Qty: {item['quantity']}</span>
                        <span class="item-price">₹{item_total:.0f}</span>
                    </div>
                </div>
        """
    
    html += """
            </div>
            
            <!-- Totals -->
            <div class="totals-section">
                <div class="totals-card">
    """
    
    html += f"""
                    <div class="total-row">
                        <span>Subtotal</span>
                        <span style="font-weight: 600;">₹{subtotal:.0f}</span>
                    </div>
    """
    
    if discount > 0:
        html += f"""
                    <div class="total-row savings">
                        <span>💰 You Saved</span>
                        <span>- ₹{discount:.0f}</span>
                    </div>
        """
    
    html += f"""
                    <div class="total-row">
                        <span>Delivery Fee</span>
                        <span style="font-weight: 600;">₹{delivery_fee:.0f}</span>
                    </div>
                    <div class="total-row final">
                        <span>Total Amount</span>
                        <span>₹{total:.0f}</span>
                    </div>
    """
    
    if delivery_fee == 0:
        html += """
                    <div class="free-delivery">
                        🎉 Congratulations! You got <span class="highlight-text">FREE DELIVERY</span>
                    </div>
        """
    
    html += """
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <h3>🎉 Thank You for Shopping with Swippe!</h3>
                <p style="font-size: 18px; margin: 15px 0;">Your order will be delivered in <span class="highlight-text">10-30 minutes</span></p>
                <p>📱 Track your order in real-time from our app</p>
                <p>🚚 Our delivery partner is on the way</p>
                <div class="footer-links">
                    <p>Questions? Contact us at <strong>support@swippe.com</strong></p>
                    <p>📞 Customer Care: 1800-SWIPPE (24/7)</p>
                    <p style="margin-top: 15px; font-size: 12px;">🔒 Your satisfaction is our priority</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_modern_invoice_email(order_id, customer_email=None):
    """Send modern styled invoice email"""
    
    # Check if email is enabled
    if not EMAIL_ENABLED:
        print("⚠️  Email system disabled: EMAIL_SENDER or EMAIL_PASSWORD not configured")
        return False, "Email system not configured"
    
    print(f"📧 Attempting to send email for order #{order_id}...")
    print(f"   SMTP Server: {EMAIL_CONFIG['SMTP_SERVER']}:{EMAIL_CONFIG['SMTP_PORT']}")
    print(f"   Sender: {EMAIL_CONFIG['SENDER_EMAIL']}")
    
    try:
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get order details
        cursor.execute('''
            SELECT o.id as order_id, o.ordered_at, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = ?
        ''', (order_id,))
        
        order_data = cursor.fetchone()
        if not order_data:
            conn.close()
            print(f"❌ Order #{order_id} not found in database")
            return False, "Order not found"
        
        # Get order items
        cursor.execute('''
            SELECT p.product as product_name, p.brand, p.sale_price, p.market_price, o.quantity
            FROM orders o
            JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
        ''', (order_id,))
        
        order_items = cursor.fetchall()
        conn.close()
        
        if not order_items:
            print(f"❌ No items found for order #{order_id}")
            return False, "No items in order"
        
        # Determine recipient email
        recipient_email = customer_email or order_data['email']
        print(f"   Recipient: {recipient_email}")
        
        # Generate HTML
        html_content = generate_modern_invoice_html(dict(order_data), [dict(item) for item in order_items])
        
        # Create email
        message = MIMEMultipart('alternative')
        message['Subject'] = f'✅ Order #{order_id} Confirmed - Swippe Quick Commerce'
        message['From'] = f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>"
        message['To'] = recipient_email
        
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)
        
        # Send email
        print(f"   Connecting to SMTP server...")
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT'], timeout=30) as server:
            print(f"   Starting TLS...")
            server.starttls()
            print(f"   Logging in...")
            server.login(EMAIL_CONFIG['SENDER_EMAIL'], EMAIL_CONFIG['SENDER_PASSWORD'])
            print(f"   Sending message...")
            server.send_message(message)
        
        print(f"✅ Invoice email sent successfully to {recipient_email}")
        return True, f"Invoice sent to {recipient_email}"
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication failed: {str(e)}"
        print(f"❌ {error_msg}")
        print(f"   Check EMAIL_SENDER and EMAIL_PASSWORD environment variables")
        return False, error_msg
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False, error_msg

if __name__ == '__main__':
    # Test the modern email
    print("🎨 Testing Modern Email Template...")
    success, message = send_modern_invoice_email(1, 'test@gmail.com')
    print(f"{'✅' if success else '❌'} {message}")
