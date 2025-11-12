"""
Intelligent RAG Chatbot for Swippe - Real-World Use Cases
===========================================================

Features:
1. Conversation Memory - Maintains context across messages
2. Personalized Recommendations - Based on user's past orders & cart
3. Multi-Intent Handling - Recipes, nutrition, price comparisons, substitutes
4. Smart Query Understanding - Handles typos, slang, regional names
5. Contextual Awareness - Remembers what user asked before

Author: Swippe AI Team
Version: 2.0 (Intelligent Edition)
"""

import os
from openai import OpenAI
from db_adapter import get_db_connection
from datetime import datetime, timedelta
import json
import re
import gc
from collections import defaultdict

# Initialize ChromaDB
print("🧠 Initializing Intelligent RAG System...")
collection = None
chroma_client = None
try:
    import chromadb
    from chromadb.utils import embedding_functions
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L12-v1",
        device="cpu"
    )
    
    collection = chroma_client.get_collection("products", embedding_function=sentence_transformer_ef)
    print("✅ ChromaDB collection loaded")
except Exception as e:
    print(f"⚠️  ChromaDB not available (Python 3.13 compatibility): {str(e)[:80]}")
    print("   Chatbot will use database fallback mode")
    collection = None
    chroma_client = None

# Initialize OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
try:
    if OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_AVAILABLE = True
        print("✅ OpenAI client initialized")
    else:
        client = None
        OPENAI_AVAILABLE = False
        print("⚠️  OpenAI API key not set - Using fallback responses")
except Exception as e:
    client = None
    OPENAI_AVAILABLE = False
    print(f"⚠️  OpenAI initialization failed: {e}")
    print("   Using fallback responses (database-only mode)")

# Conversation Memory Store (session_id -> conversation history)
conversation_memory = defaultdict(list)
MAX_MEMORY_MESSAGES = 10  # Keep last 10 messages per user

# Product Name Variations & Synonyms
PRODUCT_SYNONYMS = {
    'doodh': 'milk',
    'chawal': 'rice',
    'sabzi': 'vegetable',
    'aloo': 'potato',
    'pyaz': 'onion',
    'tamatar': 'tomato',
    'tel': 'oil',
    'ghee': 'ghee',
    'daal': 'dal',
    'atta': 'flour',
    'chini': 'sugar',
    'namak': 'salt',
    'mirch': 'chili',
    'haldi': 'turmeric',
    'phal': 'fruit',
    'kela': 'banana',
    'seb': 'apple',
    'santara': 'orange',
    'aam': 'mango',
    'roti': 'bread',
    'pav': 'bread',
    'paneer': 'paneer',
    'dahi': 'curd',
    'masala': 'spices',
    'biscuit': 'biscuit',
    'namkeen': 'snacks',
    'chai': 'tea',
    'coffee': 'coffee',
}

# Intent Detection Patterns
INTENT_PATTERNS = {
    'recipe': r'recipe|how to cook|how to make|ingredients for|dish|cook|prepare',
    'nutrition': r'nutrition|calories|healthy|protein|vitamins|nutrients|fat|carbs',
    'price_compare': r'cheap|affordable|budget|compare price|less expensive|best price|discount',
    'substitute': r'alternative|substitute|replace|instead of|similar to|like',
    'availability': r'available|in stock|do you have|stock|out of stock',
    'delivery': r'delivery|shipping|deliver|arrive|reach|when will',
    'greeting': r'^(hi|hello|hey|hii|hlo|namaste|good morning|good evening)$',
    'product_search': r'show|find|looking for|need|want|search|get me',
}


def detect_intent(query: str) -> str:
    """Detect user's intent from query"""
    query_lower = query.lower().strip()
    
    for intent, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, query_lower):
            return intent
    
    return 'product_search'  # Default intent


def normalize_query(query: str) -> str:
    """Convert regional/slang terms to standard terms"""
    query_lower = query.lower()
    
    # Replace synonyms
    for regional, standard in PRODUCT_SYNONYMS.items():
        query_lower = query_lower.replace(regional, standard)
    
    # Fix common typos
    typo_fixes = {
        'milke': 'milk',
        'bred': 'bread',
        'rize': 'rice',
        'vegitable': 'vegetable',
        'tomatoe': 'tomato',
        'oneon': 'onion',
    }
    
    for typo, correct in typo_fixes.items():
        query_lower = query_lower.replace(typo, correct)
    
    return query_lower


def get_user_context(user_id: int) -> dict:
    """Get user's personalized context from database"""
    context = {
        'past_orders': [],
        'cart_items': [],
        'preferences': []
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user's recent orders (last 5)
        cursor.execute("""
            SELECT DISTINCT p.category, p.sub_category, p.product
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.ordered_at DESC
            LIMIT 20
        """, (user_id,))
        
        past_orders = cursor.fetchall()
        if past_orders:
            context['past_orders'] = [
                {'category': row[0], 'sub_category': row[1], 'product': row[2]}
                for row in past_orders
            ]
        
        # Get current cart items
        cursor.execute("""
            SELECT p.category, p.sub_category, p.product, c.quantity
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = ?
        """, (user_id,))
        
        cart_items = cursor.fetchall()
        if cart_items:
            context['cart_items'] = [
                {'category': row[0], 'sub_category': row[1], 'product': row[2], 'quantity': row[3]}
                for row in cart_items
            ]
        
        conn.close()
        
    except Exception as e:
        print(f"Error getting user context: {e}")
    
    return context


def add_to_conversation_memory(session_id: str, role: str, content: str):
    """Add message to conversation memory"""
    conversation_memory[session_id].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })
    
    # Keep only last N messages
    if len(conversation_memory[session_id]) > MAX_MEMORY_MESSAGES:
        conversation_memory[session_id] = conversation_memory[session_id][-MAX_MEMORY_MESSAGES:]


def get_conversation_history(session_id: str) -> list:
    """Get conversation history for context"""
    return conversation_memory.get(session_id, [])


def search_products_smart(query: str, user_context: dict = None, n: int = 20) -> list:
    """Smart product search with filtering and personalization"""
    if not collection:
        return []
    
    # Normalize query
    normalized_query = normalize_query(query)
    
    try:
        # Retrieve products from ChromaDB
        results = collection.query(
            query_texts=[normalized_query],
            n_results=n
        )
        
        # Filter unwanted categories
        excluded_keywords = [
            'hygiene', 'sanitary', 'pad', 'diaper', 'baby care', 'shampoo',
            'soap', 'toothpaste', 'detergent', 'cleaning', 'utensil',
            'cookware', 'appliance', 'cosmetic', 'beauty', 'perfume',
            'toilet', 'tissue', 'napkin'
        ]
        
        # Priority keywords for grocery
        priority_keywords = [
            'milk', 'bread', 'vegetable', 'fruit', 'rice', 'dal', 'oil',
            'spice', 'masala', 'atta', 'flour', 'sugar', 'salt', 'tea',
            'coffee', 'snack', 'biscuit', 'beverage', 'grocery', 'foodgrains',
            'egg', 'butter', 'cheese', 'paneer', 'curd', 'ghee'
        ]
        
        filtered_products = []
        
        if results['documents'] and results['documents'][0]:
            for doc in results['documents'][0]:
                doc_lower = doc.lower()
                
                # Skip excluded products
                if any(keyword in doc_lower for keyword in excluded_keywords):
                    continue
                
                # Calculate priority score
                priority_score = sum(1 for keyword in priority_keywords if keyword in doc_lower)
                
                # Boost score if product matches user's past orders
                if user_context and user_context.get('past_orders'):
                    for order in user_context['past_orders']:
                        if order['product'].lower() in doc_lower:
                            priority_score += 3  # Strong boost
                        elif order['category'].lower() in doc_lower:
                            priority_score += 1  # Category boost
                
                filtered_products.append({
                    'score': priority_score,
                    'content': doc
                })
        
        # Sort by score
        filtered_products.sort(key=lambda x: x['score'], reverse=True)
        
        return [p['content'] for p in filtered_products[:10]]
        
    except Exception as e:
        print(f"Search error: {e}")
        return []


def handle_recipe_query(query: str, products: list) -> str:
    """Handle recipe-related queries"""
    if not OPENAI_AVAILABLE:
        return "🍳 Recipe assistant needs OpenAI API key to be configured. Please check with the admin!"
    
    recipe_prompt = f"""The user is asking for a recipe or cooking instructions: "{query}"

Available ingredients from our store:
{chr(10).join(products[:5])}

Provide:
1. A simple recipe suggestion using available ingredients
2. List of ingredients needed (with emojis)
3. Quick cooking steps (3-5 steps max)
4. Mention specific product names and prices from our store

Keep it concise (200 words max). Be helpful and encouraging!"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful cooking assistant for a grocery store."},
                {"role": "user", "content": recipe_prompt}
            ],
            temperature=0.8,
            max_tokens=350
        )
        return response.choices[0].message.content
    except Exception as e:
        return "🍳 I'd love to help with recipes! Try asking about specific dishes like 'dal recipe' or 'paneer curry ingredients'."


def handle_nutrition_query(query: str, products: list) -> str:
    """Handle nutrition and health queries"""
    if not OPENAI_AVAILABLE:
        return "🥗 Nutrition assistant needs OpenAI API key to be configured. Please check with the admin!"
    
    nutrition_prompt = f"""The user is asking about nutrition/health: "{query}"

Relevant products:
{chr(10).join(products[:5])}

Provide:
1. Nutritional information (if applicable)
2. Health benefits
3. Recommended products from our list
4. Serving suggestions

Keep it informative but brief (200 words max). Use health emojis!"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a nutrition expert helping grocery shoppers."},
                {"role": "user", "content": nutrition_prompt}
            ],
            temperature=0.7,
            max_tokens=350
        )
        return response.choices[0].message.content
    except Exception as e:
        return "🥗 For nutrition info, try asking about specific products like 'is milk healthy?' or 'protein rich foods'."


def handle_price_comparison(query: str, products: list) -> str:
    """Handle price comparison queries"""
    if not OPENAI_AVAILABLE:
        # Fallback: show products with basic price info
        if products:
            product_list = "\n".join([f"• {p}" for p in products[:5]])
            return f"""💰 **Budget-Friendly Options:**

{product_list}

💡 **Money-Saving Tips:**
- Free delivery on orders above ₹199
- Check for combo offers in product details
- Bulk quantities often have better rates

Need help with a specific product? Let me know! 🛒"""
        return "💰 Let me find you the best deals! Try asking 'cheapest rice' or 'affordable milk brands'."
    
    price_prompt = f"""The user wants affordable/budget options: "{query}"

Available products:
{chr(10).join(products[:8])}

Provide:
1. List 3-4 most affordable options with specific prices
2. Mention any discounts or combo offers
3. Suggest bulk buying for savings
4. Be specific about product names and brands

Keep it focused on value (150 words max). Use money emojis!"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a savvy shopping assistant helping customers find the best deals."},
                {"role": "user", "content": price_prompt}
            ],
            temperature=0.6,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return "💰 Let me find you the best deals! Try asking 'cheapest rice' or 'affordable milk brands'."


def rag_query_intelligent(query: str, user_id: int = None, session_id: str = None) -> str:
    """
    Intelligent RAG query with context awareness and multi-intent handling
    
    Args:
        query: User's question
        user_id: User ID for personalization
        session_id: Session ID for conversation memory
    
    Returns:
        AI-generated response
    """
    if not collection:
        return "🔧 AI assistant is initializing... Please try again in a moment!"
    
    # Generate session ID if not provided
    if not session_id:
        session_id = f"user_{user_id}_{datetime.now().date()}"
    
    # Add to conversation memory
    add_to_conversation_memory(session_id, 'user', query)
    
    try:
        # 1. Detect intent
        intent = detect_intent(query)
        print(f"🎯 Detected intent: {intent}")
        
        # 2. Get user context for personalization
        user_context = get_user_context(user_id) if user_id else None
        
        # 3. Search for relevant products
        products = search_products_smart(query, user_context, n=20)
        
        if not products:
            products = ["No grocery products found for this query."]
        
        # 4. Get conversation history
        conversation_history = get_conversation_history(session_id)
        
        # 5. Handle different intents
        if intent == 'recipe':
            response_text = handle_recipe_query(query, products)
        
        elif intent == 'nutrition':
            response_text = handle_nutrition_query(query, products)
        
        elif intent == 'price_compare':
            response_text = handle_price_comparison(query, products)
        
        elif intent == 'greeting':
            # Personalized greeting
            greeting_context = ""
            if user_context and user_context.get('past_orders'):
                recent_category = user_context['past_orders'][0]['category']
                greeting_context = f"\n\nI see you often buy {recent_category} products. Want recommendations?"
            
            response_text = f"""👋 **Hi! Welcome to Swippe!**

I'm your intelligent shopping assistant. I can help you with:

🛒 **Product Search** - "Show me fresh vegetables", "I need rice"
💰 **Best Deals** - "What's on sale?", "Cheapest cooking oil"
🍳 **Recipes** - "Recipe for dal", "Ingredients for biryani"
🥗 **Nutrition** - "Is this healthy?", "High protein foods"
📦 **Orders** - "Track my order", "Order history"
🚚 **Delivery** - "When will it arrive?", "Delivery areas"
{greeting_context}

What would you like to explore today? 😊"""
        
        elif intent == 'delivery':
            response_text = """🚚 **Super Fast Delivery!**

⚡ **10-Minute Delivery** on most orders in your area
🆓 **Free Delivery** on orders above ₹199
📍 **Live Tracking** - Track your order in real-time
🕐 **24/7 Service** - Order anytime, day or night

📦 To track your order:
1. Go to "My Orders" 
2. Click on order number
3. See live location on map

Want to place an order now? Just tell me what you need! 🛒"""
        
        else:
            # Default: Smart product recommendation with context
            if not OPENAI_AVAILABLE:
                # Fallback without OpenAI
                if products:
                    product_list = "\n".join([f"{i+1}. {p}" for i, p in enumerate(products[:5])])
                    response_text = f"""🛒 **Here's what I found for you:**

{product_list}

💡 **Quick Tip:** Click on any product to see full details, add to cart, and checkout!

Looking for something else? Try being more specific like:
- "Show me basmati rice"
- "Cheapest cooking oil"
- "Fresh vegetables available"

How else can I help? 😊"""
                else:
                    response_text = generate_smart_fallback(query)
            else:
                # Use OpenAI for intelligent responses
                context_text = "\n".join(products[:5])
                
                # Build conversation context
                recent_conversation = ""
                if len(conversation_history) > 1:
                    recent_messages = conversation_history[-3:-1]  # Last 2 messages
                    recent_conversation = "\n".join([
                        f"{msg['role'].title()}: {msg['content'][:100]}" 
                        for msg in recent_messages
                    ])
                
                # Build personalization context
                personalization_text = ""
                if user_context:
                    if user_context.get('past_orders'):
                        past_categories = list(set([o['category'] for o in user_context['past_orders'][:5]]))
                        personalization_text += f"\nUser often buys: {', '.join(past_categories)}"
                    
                    if user_context.get('cart_items'):
                        cart_products = [c['product'] for c in user_context['cart_items'][:3]]
                        personalization_text += f"\nCurrent cart: {', '.join(cart_products)}"
                
                system_prompt = """You are Swippe's advanced AI shopping assistant! 🛒🧠

PERSONALITY:
- Friendly, helpful, and conversational
- Use emojis appropriately (food-related preferred)
- Sound natural, not robotic

RESPONSE RULES:
1. **Specificity**: Always mention actual product names, brands, and prices
2. **Recommendations**: Suggest 2-3 specific products with details
3. **Context Awareness**: Reference past conversation if relevant
4. **Personalization**: Use user's purchase history when available
5. **Actionable**: End with a question or call-to-action
6. **Concise**: 150-250 words maximum

FOCUS ONLY ON:
✅ Food, beverages, vegetables, fruits, dairy, grains, spices, snacks, groceries

NEVER SUGGEST:
❌ Hygiene products, baby items, cleaning supplies, utensils, appliances

CONVERSATION STYLE:
- First-time query: Give overview + specific recommendations
- Follow-up query: Build on previous context
- Price query: Compare options with specific prices
- Vague query: Ask clarifying questions"""
            
            user_message = f"""Available Products:
{context_text}
{personalization_text}

Recent Conversation:
{recent_conversation if recent_conversation else "First interaction"}

Customer Question: {query}

Your Response (be specific, mention products/prices, be conversational):"""
            
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.75,
                    max_tokens=350
                )
                response_text = response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI error: {e}")
                response_text = generate_smart_fallback(query)
        
        # Add response to conversation memory
        add_to_conversation_memory(session_id, 'assistant', response_text)
        
        # Cleanup
        gc.collect()
        
        return response_text
        
    except Exception as e:
        print(f"❌ RAG Error: {e}")
        return generate_smart_fallback(query)


def generate_smart_fallback(query: str) -> str:
    """Enhanced fallback responses"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ['milk', 'doodh', 'dairy']):
        return """🥛 **Fresh Dairy Products:**

We have premium dairy delivered fresh:
- **Amul Milk** - Toned/Full Cream (₹25-₹65/500ml)
- **Mother Dairy** - Quality assured
- **Amul Butter** - 100g pack (₹50)
- **Amul Cheese** - Slices/cubes (₹120-₹150)
- **Fresh Paneer** - Daily fresh (₹80/200g)

🚚 Delivered within 10 minutes! Want me to show curd, ghee, or other dairy products?"""
    
    elif any(word in query_lower for word in ['bread', 'roti', 'pav']):
        return """🍞 **Fresh Bakery:**

Freshly baked daily:
- **Britannia Bread** - White/Brown (₹30-₹50)
- **Modern Bread** - Whole wheat (₹35)
- **Harvest Gold** - Premium options (₹45-₹60)
- **Fresh Pav** - Perfect for vada pav! (₹20/6pcs)

💡 Order before 8 AM for guaranteed fresh bread! Looking for anything specific?"""
    
    else:
        return """👋 **Hi! I'm your Swippe AI assistant!**

I can help with:
🔍 **Find Products** - "Show me rice", "I need vegetables"
💰 **Best Prices** - "Cheapest oil", "Budget groceries"
🍳 **Recipes** - "Dal recipe", "Ingredients for pasta"
📦 **Track Orders** - "Where is my order?"

Try asking naturally:
- "What's fresh today?"
- "Show affordable snacks"
- "I need ingredients for breakfast"

What can I help you find? 😊"""


# Clear old conversation memories (run periodically)
def cleanup_old_conversations(days_old=7):
    """Remove conversation history older than specified days"""
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    for session_id in list(conversation_memory.keys()):
        messages = conversation_memory[session_id]
        if messages:
            last_message_time = datetime.fromisoformat(messages[-1]['timestamp'])
            if last_message_time < cutoff_date:
                del conversation_memory[session_id]
    
    gc.collect()


# Test function
if __name__ == "__main__":
    print("\n🧪 Testing Intelligent RAG System\n")
    
    test_queries = [
        ("Show me some milk products", 1),
        ("I need something cheap for breakfast", 1),
        ("How do I make dal?", 1),
        ("Is rice healthy?", 1),
    ]
    
    session_test = f"test_session_{datetime.now().timestamp()}"
    
    for query, user_id in test_queries:
        print(f"\n❓ Query: {query}")
        print(f"🤖 Response:\n{rag_query_intelligent(query, user_id, session_test)}")
        print("-" * 80)
