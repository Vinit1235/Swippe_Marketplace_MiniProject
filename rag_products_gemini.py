"""
RAG Product Search with Gemini AI
==================================
Enhanced product search and chatbot using FAISS embeddings and Google Gemini API
Adapted from Colab notebook for Flask integration
"""

import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os
import sqlite3

# Gemini AI imports
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  Google Generative AI not installed. Install with: pip install google-generativeai")

class GeminiProductRAG:
    """Product search and chat using FAISS + Gemini AI"""
    
    def __init__(self, db_path='instance/swippe.db', gemini_api_key=None):
        """Initialize the RAG system"""
        self.db_path = db_path
        self.embedding_model = None
        self.faiss_index = None
        self.products_df = None
        self.gemini_model = None
        self.chat_history = []
        
        # Configure Gemini API
        if GEMINI_AVAILABLE and gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✅ Gemini AI Model initialized (gemini-2.0-flash-exp)")
            except Exception as e:
                print(f"⚠️  Failed to initialize Gemini: {e}")
                self.gemini_model = None
        else:
            print("⚠️  Gemini API key not provided or library not available")
        
        # Load products and create embeddings
        self._load_products()
        self._create_embeddings()
    
    def _load_products(self):
        """Load products from SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load products with relevant columns
            query = """
                SELECT id, product, category, sub_category, brand, 
                       sale_price, market_price, rating, image_url
                FROM products
                LIMIT 5000
            """
            
            self.products_df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Create text field for embeddings
            self.products_df['text'] = (
                "Product: " + self.products_df['product'].astype(str) +
                ", Category: " + self.products_df['category'].astype(str) +
                ", Brand: " + self.products_df['brand'].astype(str) +
                ", Rating: " + self.products_df['rating'].astype(str) +
                ", Price: ₹" + self.products_df['sale_price'].astype(str)
            )
            
            print(f"✅ Loaded {len(self.products_df)} products from database")
            
        except Exception as e:
            print(f"❌ Failed to load products: {e}")
            self.products_df = pd.DataFrame()
    
    def _create_embeddings(self):
        """Create FAISS embeddings from product data"""
        if self.products_df.empty:
            print("⚠️  No products to create embeddings")
            return
        
        try:
            # Load embedding model
            print("📥 Loading SentenceTransformer model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Get product texts
            texts = self.products_df['text'].tolist()
            
            # Create embeddings
            print("🔄 Creating embeddings (this may take a moment)...")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            embeddings = np.array(embeddings).astype('float32')
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.faiss_index = faiss.IndexFlatL2(dimension)
            self.faiss_index.add(embeddings)
            
            print(f"✅ Created FAISS index with {self.faiss_index.ntotal} embeddings")
            
        except Exception as e:
            print(f"❌ Failed to create embeddings: {e}")
            self.faiss_index = None
    
    def search_products(self, query, top_k=5):
        """Search for similar products based on text query"""
        if self.faiss_index is None or self.embedding_model is None:
            return []
        
        try:
            # Convert query to embedding
            query_embedding = self.embedding_model.encode([query]).astype('float32')
            
            # Search FAISS index
            distances, indices = self.faiss_index.search(query_embedding, top_k)
            
            # Get matching products
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                product = self.products_df.iloc[idx]
                results.append({
                    'id': int(product['id']),
                    'product': product['product'],
                    'category': product['category'],
                    'brand': product['brand'],
                    'sale_price': float(product['sale_price']),
                    'rating': float(product['rating']) if pd.notna(product['rating']) else 0.0,
                    'image_url': product['image_url'] if pd.notna(product['image_url']) else None,
                    'similarity_score': float(dist)
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def chat_with_gemini(self, user_query, use_history=True):
        """Chat with Gemini AI using product context"""
        if not self.gemini_model:
            return {
                'response': "Gemini AI is not available. Please configure your API key.",
                'products': []
            }
        
        try:
            # Search for relevant products
            products = self.search_products(user_query, top_k=3)
            
            # Format product information
            product_context = "\n\nRelevant Products from Database:\n"
            for i, prod in enumerate(products, 1):
                product_context += (
                    f"{i}. {prod['product']}\n"
                    f"   Brand: {prod['brand']}, Category: {prod['category']}\n"
                    f"   Price: ₹{prod['sale_price']:.2f}, Rating: {prod['rating']:.1f}⭐\n\n"
                )
            
            # Create prompt for Gemini
            prompt = f"""You are a helpful shopping assistant for Swippe, a quick commerce platform.

User Query: {user_query}

{product_context}

Based on the products above, provide a helpful, friendly response to the user's query. 
If they're asking about specific products, recommend from the list above.
Keep your response concise and conversational."""
            
            # Use chat history if enabled
            if use_history and self.chat_history:
                chat_session = self.gemini_model.start_chat(history=self.chat_history)
                response = chat_session.send_message(prompt)
            else:
                response = self.gemini_model.generate_content(prompt)
            
            # Update chat history
            if use_history:
                self.chat_history.append({'role': 'user', 'parts': [user_query]})
                self.chat_history.append({'role': 'model', 'parts': [response.text]})
            
            return {
                'response': response.text,
                'products': products,
                'history_length': len(self.chat_history)
            }
            
        except Exception as e:
            print(f"❌ Chat failed: {e}")
            return {
                'response': f"Sorry, I encountered an error: {str(e)}",
                'products': []
            }
    
    def reset_chat_history(self):
        """Clear conversation history"""
        self.chat_history = []
        return "Chat history cleared!"


# Flask integration function
def get_gemini_rag_instance():
    """Get or create singleton instance of GeminiProductRAG"""
    if not hasattr(get_gemini_rag_instance, 'instance'):
        # Get Gemini API key from environment
        gemini_api_key = os.environ.get('GEMINI_API_KEY')
        
        if not gemini_api_key:
            print("⚠️  GEMINI_API_KEY not found in environment variables")
            print("   Add to .env file: GEMINI_API_KEY=your_key_here")
        
        get_gemini_rag_instance.instance = GeminiProductRAG(
            gemini_api_key=gemini_api_key
        )
    
    return get_gemini_rag_instance.instance


# Test function
if __name__ == '__main__':
    print("\n" + "="*70)
    print("GEMINI PRODUCT RAG SYSTEM TEST")
    print("="*70 + "\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize RAG system
    rag = GeminiProductRAG(gemini_api_key=os.environ.get('GEMINI_API_KEY'))
    
    # Test product search
    print("\n🔍 Testing Product Search:")
    print("-" * 70)
    results = rag.search_products("organic milk")
    for i, product in enumerate(results[:3], 1):
        print(f"\n{i}. {product['product']}")
        print(f"   Brand: {product['brand']} | Price: ₹{product['sale_price']}")
        print(f"   Similarity Score: {product['similarity_score']:.4f}")
    
    # Test Gemini chat
    if rag.gemini_model:
        print("\n\n💬 Testing Gemini Chat:")
        print("-" * 70)
        
        test_queries = [
            "What organic products do you have?",
            "I need milk for breakfast",
            "Show me healthy snacks under ₹200"
        ]
        
        for query in test_queries:
            print(f"\n👤 User: {query}")
            result = rag.chat_with_gemini(query)
            print(f"🤖 Gemini: {result['response']}")
            print(f"   [Found {len(result['products'])} relevant products]")
    
    print("\n" + "="*70)
    print("✅ Test completed!")
    print("="*70 + "\n")
