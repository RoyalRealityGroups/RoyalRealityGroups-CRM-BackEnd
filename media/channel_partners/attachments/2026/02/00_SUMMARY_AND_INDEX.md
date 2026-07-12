# Tenali Double Horse - Sales Management Application
## Summary and Index Document

---

## Project Overview

**Product**: Sales Management Application  
**Application Type**: Web Application (Browser Compatible)  
**Architecture**: Single-Tenant Application (Product, not single project)  
**Technology Stack**: 
- Backend: Python (Django)
- Frontend: React TypeScript (Web Application)
- Database: PostgreSQL
- Cache: Redis
- Integration: Tally ERP
- Infrastructure: AWS (S3, CloudFront, ECS/Kubernetes)
- CI/CD: GitHub Actions

---

## Documentation Index

This documentation set includes:

### Core Documentation
1. **00_SUMMARY_AND_INDEX.md** (This file) - Overview and quick reference
2. **01_MASTERS_DOCUMENTATION.md** - All master screens with fields
3. **02_TRANSACTION_SCREENS_DOCUMENTATION.md** - All transaction screens with fields and workflows
4. **03_DATABASE_SCHEMA_DOCUMENTATION.md** - Complete database schema with multi-tenancy support
5. **04_PRICE_BOOK_CONCEPT.md** - Detailed Price Book concept and implementation

### Architecture & Design
6. **05_APPLICATION_ARCHITECTURE.md** - Application architecture design
7. **06_SECURITY_ARCHITECTURE.md** - Comprehensive security architecture
8. **07_COMPONENT_LIBRARY.md** - Shared component library documentation
9. **08_PERFORMANCE_SCALABILITY.md** - Performance optimization and scalability strategies
10. **09_CI_CD_DEVOPS.md** - CI/CD pipelines and DevOps practices
11. **10_API_DOCUMENTATION_STANDARDS.md** - API design standards and OpenAPI specifications
12. **11_IMPLEMENTATION_GUIDE.md** - Step-by-step implementation guide
13. **12_NOTIFICATIONS_SYSTEM.md** - Comprehensive notifications system (In-App, Push, Email, SMS, WhatsApp)
14. **13_PERMISSIONS_MENU_MANAGEMENT.md** - Dynamic permissions and menu management system
15. **31_SCHEMES_AND_SCREEN_TYPES.md** - Discount schemes and screen types documentation
16. **32_ACTIVITY_AND_AUDIT_LOGS.md** - Activity log and audit log system
17. **33_INVENTORY_MANAGEMENT_MODULE_ANALYSIS.md** - Inventory management module analysis
18. **34_INVENTORY_MANAGEMENT_MODULE.md** - Complete inventory management module design
19. **35_FEATURE_FLAG_IMPLEMENTATION.md** - Feature flag implementation guide
20. **36_ACCOUNTING_MODULE_ANALYSIS.md** - Accounting module analysis
21. **37_ACCOUNTING_MANAGEMENT_MODULE.md** - Complete accounting management module design
22. **38_ACCOUNTING_INTEGRATION.md** - Accounting module integration guide
23. **39_DISTRIBUTOR_RETAILER_ACCOUNTS_ANALYSIS.md** - Analysis of Distributor/Retailer vs Chart of Accounts
24. **40_LEDGER_FOR_DISTRIBUTORS_RETAILERS.md** - How ledgers work for Distributors & Retailers with separate masters
25. **41_LEDGER_IMPLEMENTATION.md** - Complete hybrid ledger implementation guide (basic + account-based)
26. **42_ERP_INTEGRATION_SYSTEM.md** - Flag-based ERP integration system (Tally, Focus ERP, Custom ERP) with API-based integration and session management
27. **43_ERP_SYNC_STATUS_TRACKING.md** - ERP sync status tracking and duplicate prevention system
28. **44_AUTHORIZATION_APPROVAL_SYSTEM.md** - Multi-level authorization/approval system with group-based approvers
29. **45_GROUP_BASED_STANDARDIZATION.md** - Group-based logic standardization guide
30. **46_NO_HARDCODED_GROUPS.md** - No hardcoded groups - end user configuration guide
31. **47_SUPERUSER_PERMISSIONS.md** - Superuser full access - all screens/reports/CRUD operations bypass permissions
32. **48_NO_HARDCODED_ACCESS_LEVELS.md** - No hardcoded access levels - permission-based access control guide
33. **49_LOGIN_PAGE_DOCUMENTATION.md** - Login page/screen documentation with authentication flow, MFA, and security features
34. **50_SETTINGS_SUBMENU_DOCUMENTATION.md** - Settings submenu with Groups, Users, Authorization, Integration, Notifications, and Feature Flags screens
35. **51_ADDITIONAL_TRANSACTION_SCREENS.md** - Analysis and recommendation for additional transaction screens
36. **52_RETAILER_ORDER_CLUBBING_QUERIES.md** - Clarification questions for retailer order creation and clubbing workflow
37. **53_RETAILER_ORDER_CLUBBING_IMPLEMENTATION.md** - Complete implementation summary for retailer order creation and clubbing
38. **54_SCREEN_TO_DATABASE_TABLE_MAPPING.md** - Comprehensive mapping of all screens to their corresponding database tables
39. **55_DEVELOPMENT_ORDER.md** - Complete development order and task planning with phases, dependencies, and timeline

---

## Development Tasks

All development task files are located in the `tasks/` directory. Each documentation file has a corresponding task file with detailed implementation tasks.

- **Task Files Directory**: `tasks/`
- **Task Files README**: `tasks/README.md`
- **Total Task Files**: 55 (one for each documentation file)
- **Development Order**: See `55_DEVELOPMENT_ORDER.md`

---

## Master Screens Summary

### 1. State Master
- **Purpose**: Manage states
- **Fields**: State ID, State Name, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

### 2. City Master
- **Purpose**: Manage cities under states
- **Fields**: City ID, State ID, City Name, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

### 3. Area Master
- **Purpose**: Manage areas under cities
- **Fields**: Area ID, State ID, City ID, Area Name, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

### 4. Company Master
- **Purpose**: Manage company profiles
- **Fields**: Company ID, State ID, City ID, Company Name, Email, Mobile, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Note**: Company can have multiple locations (managed in Location Master)

### 5. Location Master
- **Purpose**: Manage company's physical/operational locations (where company exists and operates from)
- **Fields**: Location ID, Location Code, Location Name, Company ID, State ID, City ID, Area ID, Address, Contact Details, GST Number, Is Primary Location, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Relationship**: Each location belongs to one company (Company → Many Locations)
- **Note**: Different from warehouses - this is for company's operational locations

### 6. Warehouse Master
- **Purpose**: Manage warehouses, distribution centers, and storage facilities for companies
- **Fields**: Warehouse ID, Warehouse Code, Warehouse Name, Location ID, Warehouse Type, State ID, City ID, Area ID, Address (required), Contact Details (required), Is Primary Warehouse, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Relationship**: Each warehouse belongs to one location (Company → Location → Warehouse)
- **Note**: Separate from company locations - used for inventory management and order fulfillment

### 7. Category Master
- **Purpose**: Manage item categories
- **Fields**: Category ID, Category Name, Description, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

### 8. Tax Master
- **Purpose**: Manage tax rates (GST, VAT, etc.) for items and transactions
- **Fields**: Tax ID, Tax Name, Tax Rate, Tax Type, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Usage**: Used in Item Catalog for item-wise tax assignment, and in Orders/Invoices for tax calculation

### 9. Super Stockist Master
- **Purpose**: Manage super stockists who manage multiple distributors
- **Fields**: Super Stockist ID, Super Stockist Code, Company Name, Contact Person, Mobile, Email, GST, State, City, Area, Billing Address, Shipping Address, Credit Limit, Credit Days, Tally Ledger Name, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Hierarchy**: Super Stockist → Distributor → Retailer
- **Pricing**: Super stockists get different (higher discount) pricing than distributors

### 10. Distributor Master
- **Purpose**: Manage distributor/agent records with super stockist linkage
- **Fields**: Distributor ID, Distributor Code, Super Stockist ID (Optional), Agent Name, Mobile, Email, Areas (Multi-select), Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

### 11. Retailers Master
- **Purpose**: Manage retailer information
- **Fields**: Retailer ID, Retailer Code, Retailer Name, Mobile, Email, GST, State, City, Area, Billing Address, Shipping Address, Distributor, Tally Party Name, Is Active, Audit Fields
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)

---

## Transaction Screens Summary

### 1. Item Catalog
- **Purpose**: Add and maintain items
- **Key Fields**: Item Name, Image, Category, Company, State, City, Price, Bag Weight, Unit, Tax, Discount, Priority
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: Price Book History tab, Bulk Upload

### 2. Price Book
- **Purpose**: Define prices at Company/State/City/Area levels
- **Key Fields**: Price Book Mode, Company, State, City, Item, Price, Effective Dates
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: Grid view, Bulk Upload, Import/Export, Price History

### 3. Orders
- **Purpose**: Place and manage orders
- **Key Fields**: Retailer, Items, Quantity, Price, Tax, Discount, Total Amount, Order Status, Tally Posting Status
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Workflow**: Pending → Approved/Rejected → Posted to Tally → Delivered

### 4. Invoices
- **Purpose**: View invoices from Tally
- **Key Fields**: Invoice Number, Order Reference, Retailer, Distributor, Items, Amounts, Payment Status
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: Download PDF, Filter, Search

### 5. Proof of Delivery (P.O.D)
- **Purpose**: Upload delivery confirmation images
- **Key Fields**: Order, Delivery Date, Images (1-5), Notes
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: Multiple image upload, Image gallery view

### 6. Payments
- **Purpose**: Record payments from retailers
- **Key Fields**: Retailer, Invoice, Payment Date, Payment Amount, Payment Mode, Cheque Details, Remarks
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: Payment mode validation, Invoice status update

### 7. Ledger
- **Purpose**: View financial transactions with hybrid approach (basic + account-based)
- **Key Fields**: Retailer/Distributor/Account, Date, Voucher Details, Debit, Credit, Balance
- **Access**: Based on screen permissions assigned to user's groups (Superuser sees all screens)
- **Special Features**: 
  - Hybrid approach: Basic ledger (always) + Account ledger (when accounting enabled)
  - View modes: Auto (detect), Basic, Account
  - Date range filter, Export, Refresh from Tally, Create Manual Entries
  - Support for Retailer Ledger, Distributor Ledger, Account Ledger

---

## Database Tables Summary

- **Total Tables**: 66 (added location_master, warehouse_master, unit_master, item_units, activity_log, audit_log, system_configuration, inventory tables, accounting tables, distributor_ledger_entries, erp_configuration, erp_sync_log, erp_session_management, retailer_orders, retailer_order_items, order_clubbing)
- **Master Tables**: 12 (including location_master, warehouse_master, unit_master)
- **System Tables**: 3 (system_configuration, activity_log, audit_log)
- **Inventory Tables**: 5 (optional, enabled via feature flag)
- **Accounting Tables**: 8 (optional, enabled via feature flag)
- **Transaction Tables**: 12
- **Notification Tables**: 6
- **Django Built-in Tables**: 6 (auth_user, auth_group, auth_permission, etc.)
- **Custom Permission/Menu Tables**: 6 (extends Django tables)

### Master Tables (12 tables)
1. `state_master` - States
2. `city_master` - Cities
3. `area_master` - Areas
4. `company_master` - Companies
5. `location_master` - Company's operational locations (where company exists)
6. `warehouse_master` - Warehouses and storage facilities for companies
7. `category_master` - Categories
8. `tax_master` - Tax rates (GST, VAT, etc.)
9. `unit_master` - Available units (KG, BAG, PIECE, TON, etc.)
10. `distributor_master` - Distributors
11. `distributor_area_mapping` - Distributor-Area mapping (many-to-many)
12. `retailer_master` - Retailers
11. `unit_master` - Available units (KG, BAG, PIECE, etc.)

### Transaction Tables (15 tables)
1. `item_catalog` - Items/Products
2. `item_units` - Maps items to multiple units with conversion factors
3. `price_book` - Price entries
4. `price_book_history` - Price change history
5. `retailer_orders` - Retailer order creation (by retailers)
6. `retailer_order_items` - Retailer order line items
7. `orders` - Combined orders and individual orders
8. `order_items` - Order line items (with retailer tracking for combined orders)
9. `order_clubbing` - Relationship between combined orders and retailer orders
10. `invoices` - Invoices from Tally
11. `invoice_items` - Invoice line items
12. `proof_of_delivery` - P.O.D records
13. `pod_images` - P.O.D images
14. `payments` - Payment records
15. `ledger_entries` - Ledger entries from Tally

### Notification Tables (6 tables)
1. `notification_templates` - Notification templates
2. `notifications` - Notification records
3. `notification_preferences` - User notification preferences
4. `notification_logs` - Notification delivery logs
5. `channel_configurations` - Channel configuration (API keys, settings)
6. `notification_rules` - Notification rules (when and how to send)

### Permissions & Menu Tables

**Django Built-in Tables (Used):**
1. `auth_user` - User accounts (Django built-in)
2. `auth_group` - Groups/Roles (Django built-in)
3. `auth_permission` - Permissions (Django built-in)
4. `auth_user_groups` - User-Role mapping (Django built-in)
5. `auth_group_permissions` - Role-Permission mapping (Django built-in)
6. `django_content_type` - Content types (Django built-in)

**Custom Tables (Extend Django):**
7. `user_profile` - Extended user fields (extends auth_user)
8. `custom_group` - Extended group metadata (extends auth_group)
9. `custom_permission` - Extended permission metadata (extends auth_permission)
10. `menus` - Menu items (main menus, submenus, menu items)
11. `screens` - Screen/component information
12. `menu_permissions` - Menu-Permission mapping

**Total: 33 Tables (6 Django built-in + 6 custom extensions + 21 application tables)**

---

## Key Features

### 1. Multi-Level Pricing (Price Book)
- Company, State, City, and Area level pricing
- Automatic price resolution during order placement
- Price history and audit trail
- Bulk price management

### 2. Order Management
- **Retailer Order Creation**: Retailers create orders for items they need
- **Distributor Review**: Distributors review retailer orders assigned to them
- **Order Clubbing**: Distributors can club multiple retailer orders into combined orders
- **Combined & Individual Orders**: Support for both combined orders (from clubbed retailer orders) and individual orders
- **Admin Approval Workflow**: Multi-level approval for orders
- **Automatic Tally Integration**: Approved orders automatically posted to Tally
- **Status Tracking**: Complete order lifecycle tracking

### 3. Tally Integration
- Order posting to Tally
- Invoice fetching from Tally
- Ledger synchronization
- Real-time data sync

### 4. Proof of Delivery
- Image upload (multiple images)
- Delivery confirmation
- Order status update

### 5. Payment Tracking
- Payment recording against invoices
- Multiple payment modes
- Invoice status updates
- Payment verification

### 6. Financial Visibility
- **Hybrid Ledger System**:
  - Basic ledger for retailer/distributor (always available)
  - Account-based ledger via General Ledger (when accounting enabled)
  - Dual view options (basic or account-based)
  - Automatic account linking when accounting enabled
- Ledger view from Tally (sync support)
- Invoice tracking
- Payment reconciliation
- Outstanding balance tracking

### 7. Notifications System
- In-app notifications (real-time)
- Push notifications (mobile)
- Email notifications
- SMS notifications
- WhatsApp notifications
- User preference management
- Notification templates
- Delivery tracking and analytics

### 8. Permissions & Menu Management
- Dynamic menu management (admin panel)
- Permission-based access control
- Role-based permissions
- Screen-level permissions
- Action-level permissions (CRUD)
- No hardcoded permissions
- API-driven menu rendering
- Protected routes and components

### Enterprise Features
- **Security**: JWT authentication, MFA, encryption at rest and in transit
- **Performance**: Caching, database optimization, CDN
- **Scalability**: Horizontal scaling, load balancing, auto-scaling
- **Observability**: Logging, monitoring, distributed tracing
- **CI/CD**: Automated testing, deployment, infrastructure as code
- **Accessibility**: WCAG 2.1 AA compliant, keyboard navigation, screen reader support
- **Browser Compatibility**: Support for modern browsers with polyfills

---

## User Roles and Access

### Admin
- Full access to all masters
- Order approval/rejection
- Price book management
- View all transactions
- Payment verification
- System configuration

### Distributor
- View assigned retailers
- Review retailer orders assigned to them
- Approve/reject individual retailer orders
- Club multiple retailer orders into combined orders
- Create individual orders manually
- View and manage combined/individual orders
- Upload P.O.D
- Record payments
- View invoices and ledger for assigned retailers
- View own orders

### Retailer
- View own invoices
- View own ledger
- View own orders
- Limited access

---

## Workflow Summary

### Order-to-Delivery Workflow
```
1. Distributor creates order
   ↓
2. Order status: Pending
   ↓
3. Admin reviews and approves/rejects
   ↓
4. If approved: Order posted to Tally
   ↓
5. Invoice generated in Tally
   ↓
6. Invoice synced to application
   ↓
7. Distributor uploads P.O.D
   ↓
8. Order status: Delivered
   ↓
9. Distributor records payment
   ↓
10. Invoice status updated
   ↓
11. Ledger synced from Tally
```

---

## Integration Points

### Tally Integration
- **Order Posting**: Approved orders automatically posted to Tally
- **Invoice Fetching**: Invoices synced from Tally after generation
- **Ledger Sync**: Ledger entries fetched from Tally on demand
- **API Endpoints**: REST API for Tally communication

### File Storage
- **Item Images**: Stored in file system or cloud storage
- **P.O.D Images**: Stored in file system or cloud storage
- **Invoice PDFs**: Generated and stored for download

---

## Technology Implementation Notes

### Backend (Python FastAPI)
- RESTful API with OpenAPI documentation
- Database ORM (SQLAlchemy) with tenant isolation
- Tally API integration
- File upload handling with validation
- JWT authentication and authorization
- Repository pattern for data access
- Caching with Redis
- Background job processing
- Structured logging
- Health checks and monitoring

### Frontend (React TypeScript)
- Component-based architecture with shared library
- State management (React Context/Zustand)
- Form validation (React Hook Form + Zod)
- Responsive design (mobile-first)
- Accessibility (WCAG 2.1 AA)
- Browser compatibility (modern browsers)
- Code splitting and lazy loading
- Virtual scrolling for large lists
- Error boundaries
- TypeScript strict mode

### Component Library
- Reusable UI components
- Consistent design system
- Theme support
- Accessibility built-in
- Type-safe props
- Comprehensive testing

### Database (PostgreSQL)
- Normalized database schema
- Normalized schema (3NF)
- Foreign key constraints
- Optimized indexes for performance
- Row-level security policies
- Triggers for automatic calculations
- Views for complex queries
- Read replicas for scaling
- Connection pooling

### Mobile App (React Native)
- Cross-platform (iOS & Android)
- Offline capability with sync
- Image capture and upload
- Push notifications
- Biometric authentication
- Native performance

### Infrastructure
- **Frontend**: AWS S3 + CloudFront (CDN)
- **Backend**: Containerized (Docker) on ECS/Kubernetes
- **Database**: RDS PostgreSQL with read replicas
- **Cache**: ElastiCache Redis
- **Monitoring**: CloudWatch, Prometheus, Grafana
- **CI/CD**: GitHub Actions
- **IaC**: Terraform

---

## Quick Reference: Field Counts

### Master Screens
- State Master: 5 fields
- City Master: 6 fields
- Area Master: 7 fields
- Company Master: 8 fields
- Location Master: 16 fields (company's operational locations)
- Warehouse Master: 18 fields (warehouses and storage facilities)
- Category Master: 6 fields
- Tax Master: 7 fields
- Super Stockist Master: 19 fields (manages multiple distributors)
- Distributor Master: 8 fields (includes super_stockist_id)
- Retailers Master: 16 fields (includes retailer_code)
- Unit Master: 6 fields

### Transaction Screens
- Item Catalog: 18 fields
- Price Book: 8 filter fields + Grid
- Orders: 15+ fields (including items)
- Invoices: 15+ fields (read-only)
- P.O.D: 8 fields
- Payments: 12 fields
- Ledger: 10 fields (read-only)

---

## Next Steps for Development

1. **Database Setup**
   - Create PostgreSQL database
   - Run schema creation scripts
   - Set up indexes and constraints
   - Create initial master data

2. **Backend Development**
   - Set up Python project structure
   - Create API endpoints for each screen
   - Implement Tally integration
   - Set up authentication/authorization
   - File upload handling

3. **Frontend Development**
   - Set up React TypeScript project
   - Create component library
   - Implement master screens
   - Implement transaction screens
   - Set up routing and navigation

4. **Mobile App Development**
   - Set up mobile project
   - Implement order placement
   - Implement P.O.D upload
   - Implement payment recording
   - Offline sync capability

5. **Testing**
   - Unit tests
   - Integration tests
   - Tally integration tests
   - User acceptance testing

6. **Deployment**
   - Backend deployment
   - Frontend deployment
   - Mobile app distribution
   - Database migration
   - Tally connection setup

---

## Document Locations

All documentation files are located in:
```
~/tenali-double-horse-docs/
├── 00_SUMMARY_AND_INDEX.md
├── 01_MASTERS_DOCUMENTATION.md
├── 02_TRANSACTION_SCREENS_DOCUMENTATION.md
├── 03_DATABASE_SCHEMA_DOCUMENTATION.md
└── 04_PRICE_BOOK_CONCEPT.md
```

---

## Contact and Support

For questions or clarifications regarding this documentation, please refer to the detailed documentation in each respective file.

**Last Updated**: January 2025
**Version**: 1.0
