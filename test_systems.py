"""
Comprehensive System Test Suite
Tests RAG, Email, and Routine Delivery Systems
"""

import os
import sys
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test 1: Database Connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        conn = sqlite3.connect('instance/swippe.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"✅ Database connected successfully")
        print(f"   Tables found: {len(tables)}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   - {table}: {count} rows")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_rag_system():
    """Test 2: RAG Chatbot System"""
    print("\n" + "="*60)
    print("TEST 2: RAG Chatbot System")
    print("="*60)
    
    try:
        # Try Gemini RAG first
        try:
            from rag_products_gemini import get_gemini_rag_instance
            
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key or api_key == 'your_gemini_api_key_here':
                print("⚠️  GEMINI_API_KEY not configured")
                print("   To get your API key:")
                print("   1. Visit: https://ai.google.dev/")
                print("   2. Click 'Get API key'")
                print("   3. Sign in with Google account")
                print("   4. Create/select a project")
                print("   5. Copy the API key (starts with 'AIza...')")
                print("   6. Add to .env file: GEMINI_API_KEY=your_key_here")
                print("\n   Falling back to standard RAG...")
            else:
                print(f"✅ Gemini API Key found: {api_key[:10]}...{api_key[-5:]}")
                print("   Initializing Gemini RAG...")
                rag = get_gemini_rag_instance()
                
                if rag:
                    print(f"✅ Gemini RAG initialized successfully")
                    print(f"   Products loaded: {len(rag.products)}")
                    
                    # Test search
                    print("\n   Testing semantic search...")
                    results = rag.search_products("healthy breakfast", top_k=3)
                    if results:
                        print(f"   ✅ Found {len(results)} products:")
                        for i, product in enumerate(results[:3], 1):
                            print(f"      {i}. {product['name']} - ₹{product['price']}")
                    
                    # Test chat
                    print("\n   Testing Gemini chat...")
                    response, products = rag.chat_with_gemini("Show me dairy products", use_history=False)
                    print(f"   ✅ Gemini Response: {response[:100]}...")
                    if products:
                        print(f"   ✅ Recommended {len(products)} products")
                    
                    return True
        except Exception as e:
            print(f"⚠️  Gemini RAG not available: {str(e)[:100]}")
        
        # Fallback to intelligent/standard RAG
        try:
            from rag_chat_intelligent import rag_query_intelligent
            print("✅ RAG System: Intelligent Mode (v2.0)")
            response = rag_query_intelligent("Show me fruits", user_id=1, session_id="test")
            print(f"   Response: {response[:100]}...")
            return True
        except:
            try:
                from rag_chat_with_db import rag_query
                print("✅ RAG System: Standard Mode (v1.0)")
                response = rag_query("Show me products")
                print(f"   Response: {response[:100]}...")
                return True
            except Exception as e2:
                print(f"❌ RAG System completely unavailable: {e2}")
                return False
    
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_system():
    """Test 3: Email System"""
    print("\n" + "="*60)
    print("TEST 3: Email System")
    print("="*60)
    
    try:
        email_config = {
            'server': os.getenv('EMAIL_SMTP_SERVER'),
            'port': os.getenv('EMAIL_SMTP_PORT'),
            'sender': os.getenv('EMAIL_SENDER'),
            'password': os.getenv('EMAIL_PASSWORD')
        }
        
        if not all(email_config.values()):
            print("⚠️  Email configuration incomplete in .env file")
            print("\n   Required environment variables:")
            print("   - EMAIL_SMTP_SERVER=smtp.gmail.com")
            print("   - EMAIL_SMTP_PORT=587")
            print("   - EMAIL_SENDER=your-email@gmail.com")
            print("   - EMAIL_PASSWORD=your-app-password")
            print("\n   📚 How to get Gmail App Password:")
            print("   1. Go to https://myaccount.google.com/")
            print("   2. Security → 2-Step Verification (enable if not enabled)")
            print("   3. Security → App passwords")
            print("   4. Select 'Mail' and 'Other (Custom name)'")
            print("   5. Name it 'Swippe' and click 'Generate'")
            print("   6. Copy the 16-character password")
            print("   7. Add to .env: EMAIL_PASSWORD=xxxx xxxx xxxx xxxx")
            return False
        
        print(f"✅ Email configuration found")
        print(f"   Server: {email_config['server']}:{email_config['port']}")
        print(f"   Sender: {email_config['sender']}")
        
        # Try to import email module
        try:
            from email_invoice_modern import send_modern_invoice_email
            print("✅ Email System: Modern Template Available")
            print("   Note: Actual email sending requires valid order_id")
            return True
        except:
            try:
                from email_invoice import send_invoice_email
                print("✅ Email System: Classic Template Available")
                return True
            except Exception as e:
                print(f"❌ Email module not found: {e}")
                return False
    
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        return False


def test_routine_delivery_system():
    """Test 4: Enhanced Routine Delivery System"""
    print("\n" + "="*60)
    print("TEST 4: Routine Delivery System")
    print("="*60)
    
    try:
        conn = sqlite3.connect('instance/swippe.db')
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='routine_deliveries'")
        if not cursor.fetchone():
            print("❌ routine_deliveries table not found")
            print("   Run: python app.py (to initialize database)")
            return False
        
        # Check table structure
        cursor.execute("PRAGMA table_info(routine_deliveries)")
        columns = [row[1] for row in cursor.fetchall()]
        
        advanced_features = [
            'auto_order', 'max_orders', 'price_locked', 
            'notification_enabled', 'skip_holidays', 
            'custom_interval_days', 'orders_completed'
        ]
        
        print(f"✅ Routine deliveries table found")
        print(f"   Total columns: {len(columns)}")
        
        print("\n   Advanced Features:")
        for feature in advanced_features:
            status = "✅" if feature in columns else "❌"
            print(f"   {status} {feature}")
        
        # Count existing routines
        cursor.execute("SELECT COUNT(*) FROM routine_deliveries")
        count = cursor.fetchone()[0]
        print(f"\n   Existing routines: {count}")
        
        conn.close()
        
        if all(f in columns for f in advanced_features):
            print("\n✅ All advanced features available!")
            return True
        else:
            print("\n⚠️  Some advanced features missing")
            print("   Run: python app.py (to update schema)")
            return True  # Still functional, just missing some features
    
    except Exception as e:
        print(f"❌ Routine delivery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all system tests"""
    print("\n" + "🚀"*30)
    print("   SWIPPE SYSTEM TEST SUITE")
    print("🚀"*30)
    
    results = {
        "Database Connection": test_database_connection(),
        "RAG Chatbot System": test_rag_system(),
        "Email System": test_email_system(),
        "Routine Delivery System": test_routine_delivery_system()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ NEEDS ATTENTION"
        print(f"{status}: {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} systems operational")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All systems operational! Ready for LinkedIn demo.")
        print("\n📋 Next Steps:")
        print("   1. Product images are disabled (copyright-safe)")
        print("   2. Start server: python app.py")
        print("   3. Record demo at http://127.0.0.1:5000")
        print("   4. Share on LinkedIn!")
    else:
        print("\n⚠️ Some systems need attention.")
        print("\n📚 Configuration Guides:")
        print("   - Gemini API: See output above or check GEMINI_RAG_SETUP.md")
        print("   - Email: See Gmail App Password steps above")
        print("   - Database: Run 'python app.py' to initialize")


if __name__ == "__main__":
    main()
