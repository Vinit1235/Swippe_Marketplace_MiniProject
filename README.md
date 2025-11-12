# 🛒 Swippe - AI-Powered Quick Commerce Platform

> 10-Minute Grocery Delivery Platform with Google Gemini AI, FAISS Semantic Search, and Advanced Subscription Management

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![Gemini](https://img.shields.io/badge/Gemini-2.0-orange.svg)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

Swippe is a full-stack quick commerce platform built by a team of 5 SE Data Science students as a capstone project. It demonstrates modern web development practices combined with cutting-edge AI technology for intelligent product recommendations and natural language search.

### ✨ Key Features

- 🛍️ **27,555+ Products** - Extensive catalog with intelligent search and filtering
- 🤖 **Google Gemini AI Chatbot** - Context-aware conversational AI with FAISS semantic search
- 📍 **GPS Address Management** - Multiple delivery addresses with coordinates
- 📦 **Real-time Order Tracking** - Complete order lifecycle management
- 🔄 **Advanced Routine Deliveries** - Price lock, auto-order, smart suggestions
- 👨‍💼 **Admin Dashboard** - User management, analytics, and system oversight
- 📧 **Email Invoices** - Beautiful HTML email templates with order details
- 🎨 **Modern Responsive UI** - TailwindCSS with smooth animations and skeleton loaders

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+
SQLite3 (or PostgreSQL for production)
Google Gemini API Key (optional - for AI chatbot)
Gmail App Password (optional - for email invoices)
```

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/swippe.git
cd swippe
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables (Optional):**
```bash
# Create .env file
GEMINI_API_KEY=your_gemini_api_key_here
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_16_digit_app_password
```
See `API_KEYS_GUIDE.md` for detailed setup instructions.

4. **Initialize the database:**
```bash
python app.py
```
The database and products will be imported automatically on first run.

5. **Run the application:**
```bash
python app.py
```

6. **Access the app:**
Open your browser and go to `http://127.0.0.1:5000`

7. **Test the system (Optional):**
```bash
python test_systems.py
```

### Create Your First Account

- Register a new user via the signup page
- Or use demo credentials if configured

## 📁 Project Structure

```
Swippe/
├── app.py                          # Main Flask application (1000+ lines)
├── db_adapter.py                   # Database adapter (SQLite/PostgreSQL)
├── rag_products_gemini.py          # Gemini AI + FAISS RAG system
├── rag_chat_intelligent.py         # Fallback intelligent chatbot
├── email_invoice_modern.py         # Modern HTML email templates
├── test_systems.py                 # System testing suite
├── check_security.py               # Security validation
├── requirements.txt                # Python dependencies
├── products.xlsx                   # Product database (27,555+ items)
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
│
├── templates/                      # HTML templates (1000+ lines total)
│   ├── auth/
│   │   ├── login.html             # Modern login/signup with animations
│   │   └── dashboard.html         # User dashboard
│   ├── products/
│   │   ├── home.html              # Product catalog with hero banner
│   │   └── detail.html            # Product details page
│   ├── orders/
│   │   ├── list.html              # Order history
│   │   └── tracking.html          # Real-time order tracking
│   ├── admin/
│   │   ├── dashboard.html         # Admin analytics dashboard
│   │   └── users.html             # User management interface
│   ├── components/
│   │   ├── sidebar.html           # Navigation sidebar
│   │   └── theme-manager.html     # Dark/light theme toggle
│   ├── cart.html                  # Shopping cart with free delivery tracker
│   ├── checkout.html              # Checkout with delivery slots
│   ├── addresses.html             # GPS address management
│   ├── routine.html               # Routine delivery subscriptions
│   ├── chatbot.html               # AI chatbot interface
│   ├── profile.html               # User profile settings
│   ├── settings.html              # App settings
│   ├── help.html                  # Help and FAQ
│   └── loading.html               # Loading animation
│
├── static/
│   ├── banner.jpeg                # Hero section background
│   └── images/
│       └── products/              # Product images (disabled for demo)
│
├── instance/
│   └── swippe.db                  # SQLite database (auto-generated)
│
└── faiss_index/                   # FAISS vector embeddings (auto-generated)
```

## 🔧 Configuration

### Gemini AI Chatbot Setup (Optional)

1. **Get Gemini API Key:**
   - Visit https://ai.google.dev/
   - Sign in with Google account
   - Click "Get API key"
   - Copy your API key (starts with `AIza...`)

2. **Add to environment:**
```bash
# In .env file
GEMINI_API_KEY=your_api_key_here
```

3. **Free Tier Limits:**
   - 1,500 requests/day
   - 1 million tokens/month
   - No credit card required

**Note:** App works without Gemini API - chatbot will use fallback intelligent mode.

### Email System Setup (Optional)

1. **For Gmail:**
   - Enable 2-Step Verification: https://myaccount.google.com/security
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

2. **Add to environment:**
```bash
# In .env file
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

**Note:** App works without email - invoices just won't be sent.

See `API_KEYS_GUIDE.md` for detailed step-by-step instructions.

## 📊 Database Schema

### Key Tables

- **users** - User accounts with roles (admin/user), bcrypt password hashing
- **products** - Complete product catalog (27,555+ items) with categories, brands, prices, ratings
- **orders** - Order history with product references, delivery slots, payment methods
- **addresses** - GPS-enabled delivery addresses with latitude/longitude
- **routine_deliveries** - Advanced subscription system with:
  - Price lock feature
  - Auto-order capabilities
  - Custom delivery frequencies
  - Skip holiday options
  - Order completion tracking
  - Monthly spend analytics

## 🎯 Features in Detail

### 1. Product Catalog
- **27,555+ real products** imported from Excel database
- **Smart search** - Searches across product names, brands, categories, sub-categories
- **Advanced filtering** - By category, brand, price range, ratings
- **Quick filter chips** - One-click category selection
- **Skeleton loaders** - Better UX during data loading
- **Responsive grid** - Adapts to mobile, tablet, desktop

### 2. Google Gemini AI Chatbot
- **Conversational AI** - Powered by Google Gemini 2.0 Flash
- **FAISS semantic search** - Vector embeddings for intelligent product matching
- **Context awareness** - Remembers conversation history
- **Natural language** - "Show me healthy breakfast options" instead of keywords
- **Product recommendations** - AI suggests relevant products with details
- **Multi-turn conversations** - Understands follow-up questions
- **Fallback modes** - Works even without API key (intelligent/standard modes)

### 3. Shopping Cart & Checkout
- **Dynamic cart** - Real-time price calculations
- **Free delivery tracker** - Visual progress bar showing threshold
- **Delivery slot selection** - 10min, 20min, 30min, 1hr, 2hr options
- **ETA calculations** - Based on distance and selected slot
- **Multiple payment methods** - COD, UPI, Cards, Wallets
- **Order summary** - Clear breakdown of costs

### 4. Order Management
- **Complete order history** - All past orders with details
- **Real-time tracking** - Order status updates
- **Order timeline** - Visual progress indicators
- **Cancel orders** - Easy cancellation before dispatch
- **Reorder** - One-click reordering of past purchases
- **Email invoices** - Beautiful HTML email with order details

### 5. GPS Address Management
- **Multiple addresses** - Home, work, other locations
- **GPS coordinates** - Latitude/longitude for accurate delivery
- **Default address** - Quick checkout with saved address
- **Address validation** - Pincode, city, state verification
- **Edit/delete** - Full CRUD operations

### 6. Advanced Routine Deliveries
- **Smart scheduling** - Daily, weekly, biweekly, monthly, or custom intervals
- **Price lock** - Lock current price for future deliveries (save money)
- **Auto-order** - Automatic order placement on schedule
- **Skip next delivery** - Pause when you don't need it
- **Max orders** - Set limit on total deliveries
- **AI suggestions** - Smart recommendations based on order history
- **Monthly analytics** - Projected spend, total savings, active subscriptions
- **Frequency recommendations** - AI calculates optimal delivery frequency

### 7. Admin Dashboard
- **User management** - View, edit, delete users
- **Role assignment** - Promote/demote admin privileges
- **Order overview** - All orders across platform
- **System statistics** - Total users, orders, products, revenue
- **Recent activity** - Latest users and orders
- **Analytics dashboard** - Charts and metrics (future enhancement)

## 🔐 Security Features

- Password hashing with bcrypt
- Session-based authentication
- Role-based access control (RBAC)
- SQL injection prevention
- CSRF protection
- Secure email configuration

## 📈 Performance

- Optimized database queries with indexes
- Efficient product search algorithms
- ChromaDB vector search for chatbot
- Lazy loading for images
- Caching for frequent queries

## 🛠️ Technologies Used

### Backend
- **Flask 3.x** - Python web framework
- **SQLite3** - Development database
- **PostgreSQL** - Production database (via db_adapter.py)
- **bcrypt** - Secure password hashing
- **Google Gemini AI** - Conversational AI (gemini-2.0-flash)
- **FAISS** - Vector similarity search
- **sentence-transformers** - Text embeddings (all-MiniLM-L6-v2)
- **pandas** - Excel data import and processing
- **smtplib** - Email delivery system

### Frontend
- **HTML5** - Semantic markup
- **TailwindCSS** - Utility-first CSS framework
- **Vanilla JavaScript** - No framework dependencies
- **Fetch API** - Async data loading
- **LocalStorage** - Client-side cart management
- **CSS Animations** - Smooth transitions and loaders

### AI/ML Stack
- **Google Gemini 2.0 Flash** - Large language model
- **FAISS CPU** - Facebook AI similarity search
- **Sentence Transformers** - Embedding generation
- **RAG Architecture** - Retrieval-augmented generation
- **Vector Embeddings** - Semantic product search
- **Conversation Memory** - Context-aware chat

### Development Tools
- **Git** - Version control
- **VS Code** - IDE
- **Python 3.8+** - Programming language
- **pip** - Package manager

## 📝 API Endpoints

### Public Routes
- `GET /` - Home page (redirects to login)
- `GET /login` - Login page with beautiful animations
- `POST /login` - Login authentication
- `GET /register` - Signup page
- `POST /register` - User registration with validation

### Protected Routes (Requires Login)
- `GET /products` - Product catalog with filters
- `GET /products/<id>` - Product details with related items
- `GET /api/search?q=query` - Smart search API
- `GET /cart` - Shopping cart page
- `POST /api/order` - Place order with delivery details
- `GET /orders` - Order history
- `GET /orders/tracking/<id>` - Track specific order
- `GET /api/orders` - Get all user orders (JSON)
- `POST /api/order/<id>/cancel` - Cancel order
- `GET /addresses` - Address management page
- `GET /api/addresses` - Get all addresses (JSON)
- `POST /api/addresses` - Add new address with GPS
- `PUT /api/addresses/<id>` - Update address
- `DELETE /api/addresses/<id>` - Delete address
- `POST /api/addresses/<id>/set-default` - Set default address

### Routine Delivery API
- `GET /routine` - Routine deliveries page
- `GET /api/routine` - Get all routines with analytics
- `POST /api/routine` - Create new routine delivery
- `PUT /api/routine/<id>` - Update routine
- `DELETE /api/routine/<id>` - Delete routine
- `POST /api/routine/<id>/toggle` - Pause/resume routine
- `POST /api/routine/<id>/skip-next` - Skip next delivery
- `POST /api/routine/<id>/lock-price` - Lock current price
- `GET /api/routine/suggestions` - AI-powered suggestions
- `GET /api/routine/analytics` - Comprehensive analytics

### AI Chatbot API
- `POST /api/chat` - Send message to Gemini AI chatbot
- `POST /api/chat/reset` - Clear conversation history
- `GET /api/products/semantic-search?q=query` - FAISS semantic search

### Admin Routes (Requires Admin Role)
- `GET /admin` - Admin dashboard with statistics
- `GET /admin/users` - User management interface
- `POST /admin/users/<id>/toggle-admin` - Toggle admin role

### Utility Routes
- `GET /profile` - User profile page
- `GET /api/user/profile` - Get user details (JSON)
- `POST /api/user/change-password` - Change password
- `GET /settings` - App settings
- `GET /help` - Help and FAQ
- `POST /api/support/contact` - Submit support request
- `GET /logout` - Clear session and logout

## 🐛 Known Issues

- **Product images disabled** - Copyrighted images removed for LinkedIn demo (can be re-enabled)
- **Email requires Gmail App Password** - 2-factor authentication setup needed
- **Gemini API rate limits** - Free tier has 1,500 requests/day limit
- **FAISS indexing time** - First load takes 30-60 seconds to generate embeddings
- **SQLite limitations** - Use PostgreSQL for production deployment

## 🚧 Future Enhancements

- [ ] Payment gateway integration (Stripe/Razorpay)
- [ ] Real-time delivery tracking with maps
- [ ] Push notifications for order updates
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Product reviews and ratings
- [ ] Wishlist functionality
- [ ] Promotional codes and discounts
- [ ] Multi-language support
- [ ] Social media login

## 📚 Documentation

- **API Keys Guide:** `API_KEYS_GUIDE.md` - Step-by-step setup for Gemini AI and Gmail
- **LinkedIn Demo Guide:** `LINKEDIN_DEMO_GUIDE.md` - How to record and post demo
- **LinkedIn Post:** `LINKEDIN_POST.md` - Ready-to-use professional post template
- **System Testing:** `test_systems.py` - Automated testing suite
- **Security Check:** `check_security.py` - Validate no credentials in code
- **Project Summaries:**
  - `LINKEDIN_READY_SUMMARY.md` - Complete project overview
  - `BANNER_FIX_COMPLETE.md` - UI enhancements documentation
  - `SECURITY_CLEANUP_SUMMARY.md` - Security audit results

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

This project was built by a team of 5 SE Data Science students as our capstone project.

**Team Members:**
- [Add your names here]

## 🙏 Acknowledgments

- **Google** - For Gemini AI API and excellent documentation
- **Facebook AI** - For FAISS vector similarity search
- **Flask Community** - For the amazing web framework
- **Hugging Face** - For sentence-transformers library
- **TailwindCSS** - For beautiful utility-first CSS
- **Our Mentors** - For guidance throughout the project

## 📞 Support & Feedback

We'd love to hear your thoughts and suggestions!

- **GitHub Issues:** Open an issue for bugs or feature requests
- **Pull Requests:** Contributions are welcome!
- **LinkedIn:** Connect with us and share feedback

## 🌟 Show Your Support

Give a ⭐️ if this project helped you learn something new!

## 🎓 Learning Outcomes

Through this project, we gained hands-on experience with:
- ✅ Full-stack web development (Frontend + Backend + Database)
- ✅ AI/ML integration (Gemini AI, FAISS, embeddings)
- ✅ RESTful API design and implementation
- ✅ Database design and optimization (indexes, foreign keys)
- ✅ User authentication and security (bcrypt, sessions, CSRF)
- ✅ Responsive UI/UX design (TailwindCSS, animations)
- ✅ Version control and collaboration (Git, GitHub)
- ✅ Project planning and agile development

## 📈 Project Statistics

- **Total Lines of Code:** 5,000+
- **Python Files:** 10+
- **HTML Templates:** 20+
- **Database Tables:** 5
- **API Endpoints:** 40+
- **Products in Database:** 27,555
- **Development Time:** 3 weeks

---

**Built with ❤️ by SE Data Science Students**

*Swippe - Where AI meets Quick Commerce!* 🚀
