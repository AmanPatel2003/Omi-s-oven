// ---------------------------------------------------------------------------
// Generic envelope every backend endpoint responds with:
//   { success: boolean, data: T, message: string }
// RTK Query's `transformResponse` unwraps this per-endpoint so components
// only ever see `T`. Keep this type in sync with the backend's response
// wrapper — if the backend changes the envelope shape, this is the one
// place to update.
// ---------------------------------------------------------------------------
export interface ApiEnvelope<T> {
  success: boolean;
  data: T;
  message: string;
}

// Shape returned by FastAPI/Pydantic on a 422 validation error.
export interface ValidationErrorResponse {
  detail: Array<{
    loc: (string | number)[];
    msg: string;
    type: string;
  }>;
}

export type UserRole = "customer" | "staff" | "admin" | "super_admin";

// Base fields present regardless of how the user authenticated.
interface BaseUser {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: UserRole;
  createdAt: string;
}

// Email/password registered user — no `picture`.
export interface EmailUser extends BaseUser {
  authProvider: "email";
}

// Google-authenticated user — has `picture`, provider is fixed.
export interface GoogleUser extends BaseUser {
  authProvider: "google";
  picture: string;
}

// The backend's /auth/login and /auth/google-login responses use slightly
// different `user` shapes (see build-prompt note under Auth Module). Model
// both as a discriminated union on `authProvider` rather than optional
// fields everywhere, so a missing `picture` is a type error, not a runtime
// surprise.
export type User = EmailUser | GoogleUser;

export interface AuthTokens {
  accessToken: string;
  // The refresh token itself never reaches client JS — it's set directly as
  // an httpOnly cookie by the Route Handler. It is NOT part of this type on
  // purpose; if you find yourself adding `refreshToken` here, stop — that
  // defeats the point of the httpOnly cookie strategy.
}

export interface LoginResponse extends AuthTokens {
  user: User;
}

export interface RegisterResponse extends AuthTokens {
  user: User;
}

export interface RefreshResponse extends AuthTokens {
  user: User;
}

export interface LoginRequest {
  identifier: string; // email or phone
  password: string;
}

export interface RegisterRequest {
  name: string;
  email: string;
  phone: string;
  password: string;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

// ---------------------------------------------------------------------------
// Products & Categories module
// ---------------------------------------------------------------------------

/** Backend's paginated-list shape, nested inside the usual ApiEnvelope. */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}

export interface ProductVariant {
  id: string;
  label: string; // e.g. "500g", "1kg"
  price: number; // paise
}

export interface ProductImage {
  id: string;
  url: string;
  alt: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
}

export interface Product {
  id: string;
  slug: string;
  name: string;
  description: string;
  price: number; // paise — base/list price
  discountPrice: number | null; // paise — set only when on sale
  images: ProductImage[];
  category: Category;
  tags: string[];
  isEggless: boolean;
  avgRating: number;
  reviewCount: number;
  variants: ProductVariant[];
  inStock: boolean;
}

export type ProductSort =
  | "price_asc"
  | "price_desc"
  | "newest"
  | "bestselling"
  | "rating";

export interface ProductQueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  category?: string; // category slug
  minPrice?: number;
  maxPrice?: number;
  isEggless?: boolean;
  tags?: string[];
  sort?: ProductSort;
}

export interface Review {
  id: string;
  productId: string;
  userName: string;
  rating: number; // 1-5
  comment: string;
  createdAt: string;
}

export interface ReviewSubmitRequest {
  productId: string;
  rating: number;
  comment: string;
}

export interface CategoryWithProducts extends Category {
  products: Paginated<Product>;
}

// ---------------------------------------------------------------------------
// Cart & Coupons module
// ---------------------------------------------------------------------------

export interface CartItem {
  id: string;
  productId: string;
  variantId: string | null;
  name: string;
  image: string | null;
  unitPrice: number; // paise, reflects variant price if variantId is set
  quantity: number;
  lineTotal: number; // paise
  // Backend does a live stock check on every cart read — surface these
  // rather than assuming the quantity added earlier is still available.
  inStock: boolean;
  availableStock: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  couponCode: string | null;
}

export interface CartSummary {
  subtotal: number; // paise
  discount: number; // paise, from an applied coupon
  pointsDiscount: number; // paise, from redeemed reward points
  tax: number; // paise
  deliveryFee: number; // paise — 0 means free delivery
  total: number; // paise
}

export interface AddToCartRequest {
  productId: string;
  variantId?: string;
  quantity: number;
}

export interface UpdateCartItemRequest {
  itemId: string;
  quantity: number;
}

export interface Coupon {
  code: string;
  description: string;
  discountType: "flat" | "percentage";
  discountValue: number;
}

export interface ValidateCouponRequest {
  code: string;
  // Passed along so the backend can compute the actual discount preview
  // against the shopper's current cart, not just check the code exists.
  cartTotal: number;
}

export interface ValidateCouponResponse {
  valid: boolean;
  coupon: Coupon | null;
  estimatedDiscount: number; // paise — 0 if invalid
  message: string;
}

// ---------------------------------------------------------------------------
// Addresses — not in this module's listed backend routes, but the Checkout
// spec explicitly reuses an AddressForm "from the account module," which
// hasn't been specced yet. This is the minimal address CRUD checkout needs;
// treat it as provisional until a real Account module defines the actual
// routes/shape.
// ---------------------------------------------------------------------------

export type AddressType = "Home" | "Work" | "Other";

// Field names match the backend's AddressRequest exactly, per the Account
// module spec — this replaces the guessed shape (label/line1/pincode) used
// provisionally back in the Checkout module before this was known.
export interface Address {
  id: string;
  fullName: string;
  phone: string;
  addressLine1: string;
  addressLine2: string | null;
  city: string;
  state: string;
  postalCode: string;
  landmark: string | null;
  addressType: AddressType;
  isDefault: boolean;
}

export type AddressInput = Omit<Address, "id" | "isDefault">;

// ---------------------------------------------------------------------------
// Checkout, Orders & Payments module
// ---------------------------------------------------------------------------

export type PaymentMethod = "cod" | "online";
export type PaymentStatus = "pending" | "paid" | "failed";

export interface OrderItem {
  productId: string;
  name: string;
  image: string | null;
  variantLabel: string | null;
  unitPrice: number; // paise
  quantity: number;
}

export interface OrderStatusHistoryEntry {
  status: import("@/lib/constants").OrderStatus;
  timestamp: string;
}

export interface Order {
  id: string;
  items: OrderItem[];
  address: Address;
  status: import("@/lib/constants").OrderStatus;
  statusHistory: OrderStatusHistoryEntry[];
  paymentMethod: PaymentMethod;
  paymentStatus: PaymentStatus;
  subtotal: number;
  discount: number;
  pointsDiscount: number;
  tax: number;
  deliveryFee: number;
  total: number;
  createdAt: string;
}

export interface CreateOrderRequest {
  addressId: string;
  paymentMethod: PaymentMethod;
  redeemPoints: boolean;
}

export interface OrderTracking {
  status: import("@/lib/constants").OrderStatus;
  latitude: number | null;
  longitude: number | null;
  estimatedArrival: string | null;
  updatedAt: string;
}

// --- Payments ---------------------------------------------------------------

export interface CreatePaymentResponse {
  razorpayOrderId: string;
  amount: number; // paise, matches Razorpay's expected unit
  currency: string; // "INR"
}

export interface VerifyPaymentRequest {
  orderId: string;
  razorpayPaymentId: string;
  razorpayOrderId: string;
  razorpaySignature: string;
}

export interface Payment {
  id: string;
  orderId: string;
  status: PaymentStatus;
  amount: number;
}

// ---------------------------------------------------------------------------
// Delivery Tracking module (customer-facing)
// ---------------------------------------------------------------------------

export interface DeliveryTracking {
  currentLocation: { latitude: number; longitude: number } | null;
  deliveredAt: string | null;
  estimatedArrival: string | null;
}

// ---------------------------------------------------------------------------
// Custom Cake Orders module
// ---------------------------------------------------------------------------

export interface CustomOrder {
  id: string;
  occasion: string;
  flavor: string;
  size: string;
  shape: string;
  message: string;
  budgetMin: number; // paise
  budgetMax: number; // paise
  neededBy: string; // ISO date
  addressId: string | null; // null = store pickup
  referenceImages: string[]; // URLs — see the note on CreateCustomOrderRequest
  status: import("@/lib/constants").CustomOrderStatus;
  quotedPrice: number | null; // paise — set once status is "quoted"
  createdAt: string;
}

export interface CreateCustomOrderRequest {
  occasion: string;
  flavor: string;
  size: string;
  shape: string;
  message: string;
  budgetMin: number;
  budgetMax: number;
  neededBy: string;
  addressId: string | null;
  // Per the build spec: the backend expects pre-uploaded URLs here, not raw
  // files, and no upload endpoint has been confirmed to exist yet. This is
  // always sent as [] for now — see components/forms/CustomOrderForm.tsx.
  referenceImages: string[];
}

// ---------------------------------------------------------------------------
// Rewards & Notifications module
// ---------------------------------------------------------------------------

export interface RewardsSummary {
  pointsBalance: number;
  currentTier: string;
  nextTier: string | null; // null if already at the top tier
  pointsToNextTier: number; // 0 if at the top tier
}

export interface RewardTransaction {
  id: string;
  type: "earned" | "redeemed";
  points: number;
  description: string;
  createdAt: string;
}

export interface RewardTier {
  name: string;
  minPoints: number;
  benefits: string[];
}

export interface RedeemPointsRequest {
  points: number;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  isRead: boolean;
  createdAt: string;
}

export interface NotificationPreferences {
  email: boolean;
  sms: boolean;
  whatsapp: boolean;
}

export interface UpdateProfileRequest {
  name: string;
  phone: string;
  email: string;
}

// ---------------------------------------------------------------------------
// Admin — Dashboard & Analytics module
// ---------------------------------------------------------------------------

export interface DashboardStats {
  todayRevenue: number; // paise
  todayOrders: number;
  newCustomers: number;
  avgOrderValue: number; // paise
}

export interface SalesPoint {
  date: string; // ISO date (daily) or "YYYY-MM" (monthly)
  revenue: number; // paise
}

export interface HeatmapCell {
  dayOfWeek: number; // 0 (Sun) - 6 (Sat)
  hour: number; // 0-23
  value: number; // order count or revenue, backend-defined
}

export interface TopProduct {
  id: string;
  name: string;
  unitsSold: number;
  revenue: number; // paise
}

export interface LowStockItem {
  id: string;
  name: string;
  stock: number;
  threshold: number;
}

export interface PendingOrderSummary {
  id: string;
  customerName: string;
  total: number; // paise
  status: import("@/lib/constants").OrderStatus;
  createdAt: string;
}

export interface AnalyticsDateRange {
  from: string; // ISO date
  to: string; // ISO date
}

export interface RevenueByCategory {
  category: string;
  revenue: number; // paise
}

export interface CustomerGrowthPoint {
  date: string;
  newCustomers: number;
  returningCustomers: number;
}

export interface ProductSalesPoint {
  date: string;
  unitsSold: number;
}

export interface DeliveryPerformance {
  avgDeliveryTimeMinutes: number | null;
  note: string | null;
}

export interface RewardsStats {
  pointsIssued: number;
  pointsRedeemed: number;
}

export interface ForecastRow {
  date: string;
  predictedDemand: number;
  confidenceNote: string;
}

export type ExportFormat = "excel" | "pdf";

// ---------------------------------------------------------------------------
// Admin — Catalog Management module
// ---------------------------------------------------------------------------

export interface AdminProductVariant {
  id?: string; // absent for a new, unsaved row in the form
  name: string;
  price: number; // paise
  stock: number;
}

export interface AdminProduct {
  id: string;
  name: string;
  slug: string;
  description: string;
  categoryId: string;
  price: number; // paise
  discountPrice: number | null;
  tags: string[];
  variants: AdminProductVariant[];
  isEggless: boolean;
  lowStockThreshold: number;
  isFeatured: boolean;
  isAvailable: boolean;
  images: ProductImage[];
  stock: number; // used only when variants is empty
}

export type AdminProductInput = Omit<
  AdminProduct,
  "id" | "images" | "isFeatured" | "isAvailable"
>;

export interface AdminProductListParams {
  page?: number;
  pageSize?: number;
  search?: string;
  category?: string;
  sort?: string;
  sortDir?: "asc" | "desc";
}

export interface StockAdjustment {
  variantId?: string; // omitted for single-stock (no-variant) products
  stock: number; // new absolute stock level, not a delta
  reason?: string;
}

export interface AdminCategory {
  id: string;
  name: string;
  slug: string;
  order: number;
  productCount: number;
}

export type AdminCategoryInput = Pick<AdminCategory, "name" | "slug">;

export interface InventoryItem {
  id: string;
  name: string;
  unit: string;
  currentStock: number;
  lowStockThreshold: number;
}

export type InventoryMovementType = "restock" | "adjustment";

export interface InventoryAdjustmentRequest {
  quantity: number;
  reason: string;
  type: InventoryMovementType;
}

export interface InventoryMovement {
  id: string;
  type: InventoryMovementType;
  quantity: number;
  reason: string;
  createdAt: string;
  performedBy: string;
}

// ---------------------------------------------------------------------------
// Admin — Orders, Custom Orders & Coupons module
// ---------------------------------------------------------------------------

export interface AdminOrder extends Order {
  customerName: string;
  customerEmail: string;
  riderId: string | null;
  riderName: string | null;
}

export interface AdminOrderListParams {
  page?: number;
  status?: import("@/lib/constants").OrderStatus;
  from?: string;
  to?: string;
  search?: string;
}

export interface StaffMember {
  id: string;
  name: string;
  role: string;
}

export interface AdminCustomOrder extends CustomOrder {
  customerName: string;
  customerEmail: string;
}

export interface SetQuoteRequest {
  quotedPrice: number; // paise
}

export type CouponDiscountType = "percentage" | "flat";

export interface AdminCoupon {
  id: string;
  code: string;
  description: string;
  discountType: CouponDiscountType;
  discountValue: number;
  maxDiscount: number | null;
  usageLimit: number;
  usedCount: number;
  totalDiscountGiven: number; // paise
  startDate: string;
  endDate: string;
  isActive: boolean;
}

export interface CreateCouponRequest {
  code: string;
  description: string;
  discountType: CouponDiscountType;
  discountValue: number;
  maxDiscount: number | null;
  usageLimit: number;
  startDate: string;
  endDate: string;
}

export interface CouponUsageEntry {
  id: string;
  customerName: string;
  orderId: string;
  discountApplied: number; // paise
  usedAt: string;
}

// ---------------------------------------------------------------------------
// Admin — Staff, Attendance & Salary module
// ---------------------------------------------------------------------------

export interface StaffProfile {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: string;
  isActive: boolean;
  joinedAt: string;
}

export interface CreateStaffRequest {
  name: string;
  email: string;
  phone: string;
  role: string;
}

export interface CreateStaffResponse {
  staff: StaffProfile;
  tempPassword: string;
}

export type UpdateStaffRequest = Pick<
  StaffProfile,
  "name" | "email" | "phone" | "role"
>;

export type AttendanceStatus = "present" | "absent" | "leave" | "holiday";

export interface TodayAttendanceEntry {
  staffId: string;
  staffName: string;
  status: AttendanceStatus;
  clockIn: string | null;
  clockOut: string | null;
}

export interface AttendanceReportRow {
  staffId: string;
  staffName: string;
  days: Record<string, AttendanceStatus>;
}

export interface MarkLeaveRequest {
  staffId: string;
  startDate: string;
  endDate: string;
  reason?: string;
}

export interface StaffAttendanceSummary {
  daysPresent: number;
  daysAbsent: number;
  daysLeave: number;
  daysHoliday: number;
}

export interface SalaryPreviewRow {
  staffId: string;
  staffName: string;
  baseSalary: number;
  daysPresent: number;
  daysAbsent: number;
  deductions: number;
  netSalary: number;
}

export interface ProcessSalaryResponse {
  processed: boolean;
  month: string;
}

// ---------------------------------------------------------------------------
// Admin — Customers & Notifications/Campaigns module
// ---------------------------------------------------------------------------

export interface AdminCustomer {
  id: string;
  name: string;
  email: string;
  phone: string;
  orderCount: number;
  totalSpend: number; // paise
  rewardPoints: number;
  isBlocked: boolean;
  joinedAt: string;
}

export interface AdminCustomerListParams {
  page?: number;
  search?: string;
}

export interface AdminCustomerDetail extends AdminCustomer {
  addresses: Address[];
  recentOrders: Order[];
}

export interface AdjustRewardPointsRequest {
  points: number; // signed delta — positive credits, negative debits
  reason: string;
}

export type NotificationChannel = "email" | "sms" | "whatsapp";

export interface CampaignSegment {
  loyaltyTier?: string;
  inactiveDays?: number;
  minOrders?: number;
}

export interface SendNotificationRequest {
  channel: NotificationChannel;
  targetMode: "specific" | "segment";
  customerIds?: string[];
  segment?: CampaignSegment;
  subject?: string;
  message: string;
}

export interface BroadcastNotificationRequest {
  channel: NotificationChannel;
  subject?: string;
  message: string;
}

export interface CampaignResult {
  sentCount: number;
  failedCount: number;
  skippedCount: number;
  warning: string | null;
}

// ---------------------------------------------------------------------------
// Staff Self-Service module (delivery riders)
// ---------------------------------------------------------------------------

export interface StaffClockStatus {
  isClockedIn: boolean;
  clockInTime: string | null;
}

export interface MyAttendanceDay {
  date: string; // ISO date "YYYY-MM-DD"
  status: AttendanceStatus;
}

export interface StaffAssignedOrder {
  id: string;
  customerName: string;
  customerPhone: string;
  address: Address;
  status: import("@/lib/constants").OrderStatus;
}

export interface MarkDeliveredRequest {
  otp: string;
}

export interface StaffSalarySlip {
  id: string;
  month: string;
  netPaid: number; // paise
  paymentDate: string;
}

export interface LocationPushRequest {
  latitude: number;
  longitude: number;
}
