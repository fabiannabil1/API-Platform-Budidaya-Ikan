# Fish Market API - Role Change Management System

A comprehensive Fish Market API with role change management functionality, allowing users to request role changes and administrators to approve or reject these requests.

## Features

### Core Features
- **User Authentication & Authorization** - JWT-based authentication system
- **Product Management** - CRUD operations for fish products
- **Order Management** - Complete order processing system
- **Auction System** - Real-time bidding for fish products
- **Chat System** - Real-time messaging between users
- **Location Management** - Geographic location services
- **Fish Freshness Detection** - AI-powered freshness analysis using YOLO

### Role Change Management (New)
- **Role Change Requests** - Users can request to change their role (buyer to seller or vice versa)
- **Admin Approval System** - Administrators can approve or reject role change requests
- **Request Tracking** - Complete audit trail of role change requests
- **Admin Dashboard Integration** - Role requests management in admin panel

## User Roles

1. **Buyer** - Can browse products, place orders, participate in auctions, chat with sellers
2. **Seller** - Can create products, manage inventory, create auctions, chat with buyers
3. **Admin** - Full system access, user management, role change approval

## API Endpoints

### Role Change Management

#### Request Role Change
```http
POST /role-change/request
Authorization: Bearer <token>
Content-Type: application/json

{
    "new_role": "seller",
    "reason": "I want to start selling fish products"
}
```

#### List Role Change Requests (Admin Only)
```http
GET /role-change/requests
Authorization: Bearer <admin_token>
```

#### Approve Role Change Request (Admin Only)
```http
POST /role-change/approve/<request_id>
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "admin_notes": "Request approved after verification"
}
```

#### Reject Role Change Request (Admin Only)
```http
POST /role-change/reject/<request_id>
Authorization: Bearer <admin_token>
Content-Type: application/json

{
    "admin_notes": "Insufficient documentation provided"
}
```

### Other Core Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/profile` - Get user profile
- `PUT /auth/profile` - Update user profile

#### Products
- `GET /products` - List all products
- `POST /products` - Create new product (Seller/Admin)
- `GET /products/<id>` - Get product details
- `PUT /products/<id>` - Update product (Seller/Admin)
- `DELETE /products/<id>` - Delete product (Seller/Admin)

#### Orders
- `GET /orders` - List user orders
- `POST /orders` - Create new order
- `GET /orders/<id>` - Get order details
- `PUT /orders/<id>/status` - Update order status (Seller/Admin)

#### Auctions
- `GET /auctions` - List active auctions
- `POST /auctions` - Create new auction (Seller/Admin)
- `POST /auctions/<id>/bid` - Place bid on auction
- `GET /auctions/<id>/bids` - Get auction bids
- `POST /auctions/<id>/close` - Close auction (Seller/Admin)

#### Chat
- `GET /chat/users` - Search users for chat
- `GET /chat/<user_id>` - Get chat messages
- `POST /chat/<user_id>/send` - Send message

#### Fish Freshness
- `POST /fish/analyze` - Analyze fish freshness using AI

## Database Schema

### Role Change Requests Table
```sql
CREATE TABLE role_change_requests (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    current_role VARCHAR(20) NOT NULL,
    requested_role VARCHAR(20) NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    admin_notes TEXT,
    approved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js 14+ (for admin panel)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd fish-market-api
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Database Setup**
```bash
# Create PostgreSQL database
createdb fish_market_db

# Run database migrations
psql -d fish_market_db -f db_diagram/diagram.sql
psql -d fish_market_db -f db_diagram/role_change_requests.sql
psql -d fish_market_db -f db_diagram/locations_table.sql
```

5. **Environment Configuration**
Create `.env` file:
```env
DB_HOST=localhost
DB_NAME=fish_market_db
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_PORT=5432
JWT_SECRET_KEY=your_secret_key
FLASK_ENV=development
```

6. **Run the application**
```bash
python main.py
```

The API will be available at `http://localhost:5000`

### Admin Panel Setup

The admin panel is located in the `admin_web` directory and provides a web interface for managing the system.

1. **Access the admin panel**
   - Open `admin_web/index.html` in a web browser
   - Login with admin credentials

2. **Admin Panel Features**
   - Dashboard with system statistics
   - Product management
   - Order management
   - Revenue analytics
   - Chat management
   - **Role change requests management** (New)

## Azure Deployment

### Prerequisites
- Azure account with active subscription
- Azure CLI installed
- Azure App Service and PostgreSQL resources

### Deployment Steps

1. **Create Azure Resources**
```bash
# Create resource group
az group create --name fish-market-rg --location "East US"

# Create App Service plan
az appservice plan create --name fish-market-plan --resource-group fish-market-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group fish-market-rg --plan fish-market-plan --name fish-market-api --runtime "PYTHON|3.11"

# Create PostgreSQL server
az postgres server create --resource-group fish-market-rg --name fish-market-db-server --admin-user dbadmin --admin-password <secure-password> --sku-name B_Gen5_1
```

2. **Configure Environment Variables**
```bash
az webapp config appsettings set --resource-group fish-market-rg --name fish-market-api --settings \
    DB_HOST=fish-market-db-server.postgres.database.azure.com \
    DB_NAME=fish_market_db \
    DB_USERNAME=dbadmin@fish-market-db-server \
    DB_PASSWORD=<secure-password> \
    DB_PORT=5432 \
    JWT_SECRET_KEY=<secure-jwt-secret> \
    FLASK_ENV=production
```

3. **Deploy using GitHub Actions**
   - The `azure-deployment.yml` file is configured for automatic deployment
   - Set up GitHub secrets for Azure credentials
   - Push to main branch to trigger deployment

4. **Database Setup on Azure**
```bash
# Connect to Azure PostgreSQL
psql -h fish-market-db-server.postgres.database.azure.com -U dbadmin@fish-market-db-server -d postgres

# Create database and run migrations
CREATE DATABASE fish_market_db;
\c fish_market_db;
\i db_diagram/diagram.sql
\i db_diagram/role_change_requests.sql
\i db_diagram/locations_table.sql
```

### Production Configuration

1. **Security Settings**
   - Enable HTTPS only
   - Configure CORS for admin panel
   - Set up proper firewall rules for PostgreSQL

2. **Monitoring**
   - Enable Application Insights
   - Set up log analytics
   - Configure alerts for errors

3. **Scaling**
   - Configure auto-scaling rules
   - Set up load balancing if needed

## API Documentation

### Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Response Format
All API responses follow this format:
```json
{
    "success": true,
    "message": "Operation successful",
    "data": { ... }
}
```

Error responses:
```json
{
    "success": false,
    "message": "Error description",
    "error": "Detailed error information"
}
```

### Role Change Request Workflow

1. **User submits role change request**
   - User calls `POST /role-change/request`
   - Request is stored with 'pending' status

2. **Admin reviews request**
   - Admin views requests in admin panel
   - Admin can see user details and request reason

3. **Admin makes decision**
   - Admin approves: User role is updated, request marked 'approved'
   - Admin rejects: Request marked 'rejected' with admin notes

4. **User notification**
   - User can check request status via API
   - System can be extended to send email notifications

## Testing

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest tests/

# Run with coverage
pytest --cov=routes tests/
```

### API Testing
Use tools like Postman or curl to test endpoints:

```bash
# Register new user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","phone":"1234567890","password":"password123","role":"buyer"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"1234567890","password":"password123"}'

# Request role change
curl -X POST http://localhost:5000/role-change/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"new_role":"seller","reason":"Want to sell fish"}'
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/role-management`)
3. Commit your changes (`git commit -am 'Add role management feature'`)
4. Push to the branch (`git push origin feature/role-management`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the API documentation for endpoint details

## Changelog

### Version 2.0.0 (Latest)
- ✅ Added role change management system
- ✅ Enhanced admin panel with role requests management
- ✅ Improved security and authorization
- ✅ Added comprehensive API documentation
- ✅ Azure deployment configuration

### Version 1.0.0
- Initial release with core features
- User authentication and authorization
- Product and order management
- Auction system
- Chat functionality
- Fish freshness detection
