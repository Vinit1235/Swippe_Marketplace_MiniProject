# 🛒 Swippe - Quick Commerce Platform

> 10-Minute Grocery Delivery Platform built with Flask, RAG Chatbot, and Modern Web Technologies

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Overview

Swippe is a comprehensive quick commerce platform that delivers groceries and essentials in just 10 minutes. Built with Flask and featuring an AI-powered RAG chatbot, advanced order tracking, and a complete admin system.

### ✨ Key Features

- 🛍️ **27,555+ Products** - Extensive catalog with real-time search and filtering
- 🤖 **RAG Chatbot** - AI-powered customer support using OpenAI and ChromaDB
- 📍 **GPS Address Management** - Store multiple delivery addresses with coordinates
- 📦 **Order Tracking** - Real-time order status with visual progress indicators
- 🔄 **Routine Deliveries** - Schedule recurring orders for daily essentials
- 👨‍💼 **Admin Dashboard** - Complete management system for users and orders
- 📧 **Email Invoices** - Automated invoice generation and delivery
- 🎨 **Modern UI** - Responsive design with smooth animations

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+
SQLite3
OpenAI API Key
```

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/swippe.git
cd swippe
```

2. **Install dependencies:**
```bash
pip install -r requirenments.txt
```

3. **Set up environment variables:**
```bash
# Create .env file
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

4. **Initialize the database:**
```bash
python app.py
```
The database will be created automatically on first run.

5. **Run the application:**
```bash
python app.py
```

6. **Access the app:**
Open your browser and go to `http://127.0.0.1:5000`

### Default Admin Account

```
Email: admin@swippe.com
Password: admin123
```

## 📁 Project Structure

```
Swippe/
├── app.py                          # Main Flask application
├── email_invoice.py                # Email system for order invoices
├── rag_chat_with_db.py            # RAG chatbot with database integration
├── rag_setup_optimized.py         # RAG system initialization
├── requirenments.txt              # Python dependencies
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
│
├── templates/                     # HTML templates
│   ├── auth/
│   │   └── login.html            # Login/Signup page
│   ├── products/
│   │   ├── home.html             # Product catalog
│   │   └── detail.html           # Product details
│   ├── orders/
│   │   ├── list.html             # Order history
│   │   └── tracking.html         # Order tracking
│   ├── admin/
│   │   ├── dashboard.html        # Admin dashboard
│   │   └── users.html            # User management
│   └── components/
│       ├── sidebar.html          # Navigation sidebar
│       └── theme-manager.html    # Dark/light theme
│
├── static/
│   └── images/
│       └── products/             # Product images
│
├── instance/
│   └── swippe.db                 # SQLite database (auto-generated)
│
└── chroma_db/                    # ChromaDB vector store (auto-generated)
```

## 🔧 Configuration

### Email System Setup

1. **For Gmail (Recommended):**
   - Enable 2-Factor Authentication
   - Generate App Password: https://myaccount.google.com/apppasswords
   - Update `email_invoice.py` line 17 with your App Password

2. **For Outlook/Hotmail:**
   - No 2FA required
   - Use regular password
   - Update SMTP settings in `email_invoice.py`

See `EMAIL_SETUP_QUICKSTART.md` for detailed instructions.

### RAG Chatbot Setup

The RAG (Retrieval-Augmented Generation) chatbot requires:
- OpenAI API key in environment variables
- ChromaDB for vector storage (auto-initialized)
- Product database populated

Run setup:
```bash
python rag_setup_optimized.py
```

## 📊 Database Schema

### Key Tables

- **users** - User accounts with roles (admin/user)
- **products** - Complete product catalog (27,555+ items)
- **orders** - Order history and tracking
- **addresses** - GPS-enabled delivery addresses
- **routine_deliveries** - Scheduled recurring orders

## 🎯 Features in Detail

### 1. Product Catalog
- 27,555+ products across multiple categories
- Real-time search and filtering
- Brand and category navigation
- Rating-based sorting
- Image gallery support

### 2. RAG Chatbot
- Natural language product queries
- Order assistance
- FAQ support
- Context-aware responses
- Product recommendations

### 3. Order Management
- Shopping cart with quantity management
- Multiple payment methods
- Order tracking with status updates
- Order history
- Reorder functionality

### 4. Address Management
- Multiple delivery addresses
- GPS coordinates storage
- Default address selection
- Address search and filtering

### 5. Routine Deliveries
- Schedule daily/weekly deliveries
- Manage routine items
- Automatic order placement
- Flexible scheduling

### 6. Admin System
- User management (view, edit, delete)
- Role assignment (admin/user)
- Order overview
- System statistics
- Product management

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
- **Flask 2.x** - Web framework
- **SQLite3** - Database
- **bcrypt** - Password hashing
- **OpenAI API** - AI chatbot
- **ChromaDB** - Vector database
- **smtplib** - Email sending

### Frontend
- **HTML5/CSS3** - Structure and styling
- **JavaScript** - Interactivity
- **Responsive Design** - Mobile-friendly

### AI/ML
- **OpenAI GPT** - Language model
- **ChromaDB** - Vector embeddings
- **RAG Architecture** - Retrieval-augmented generation

## 📝 API Endpoints

### Public Routes
- `GET /` - Home page (redirects to login)
- `GET /login` - Login page
- `POST /login` - Login authentication
- `GET /register` - Signup page
- `POST /register` - User registration

### Protected Routes (Requires Login)
- `GET /products` - Product catalog
- `GET /product/<id>` - Product details
- `GET /cart` - Shopping cart
- `POST /api/order` - Place order
- `GET /orders` - Order history
- `GET /tracking` - Order tracking
- `GET /addresses` - Address management
- `GET /routine` - Routine deliveries
- `POST /api/chat` - Chatbot API

### Admin Routes (Requires Admin Role)
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/users` - User management
- `POST /admin/toggle-role/<id>` - Toggle user role

## 🐛 Known Issues

- Email system requires 2FA setup for Gmail
- Large product images may slow initial load
- RAG chatbot requires OpenAI API credits

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

- **Email Setup:** `EMAIL_SETUP_QUICKSTART.md`
- **RAG Setup:** `RAG_SETUP_GUIDE.md`
- **Project Report:** `PROJECT_REPORT.md`
- **Features List:** `FEATURES_COMPLETED.md`
- **System Updates:** `SYSTEM_UPDATES_OCT_2025.md`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- OpenAI for GPT API
- Flask community for excellent documentation
- ChromaDB for vector storage
- All contributors and testers

## 📞 Support

For support, email support@swippe.com or open an issue in the repository.

## 🌟 Show Your Support

Give a ⭐️ if this project helped you!

---

**Built with ❤️ using Flask and OpenAI**

*Swippe - Delivering happiness in 10 minutes!* 🚀
