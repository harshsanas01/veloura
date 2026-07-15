export type Gender = "men" | "women" | "unisex";

export type UserRole = "customer" | "admin";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Category {
  id: string;
  slug: string;
  name: string;
  description: string | null;
}

export interface ProductVariant {
  id: string;
  sku: string;
  size: string;
  color_name: string;
  color_hex: string;
  inventory_quantity: number;
  image_url: string;
}

export interface ProductListItem {
  id: string;
  slug: string;
  name: string;
  brand: string;
  gender: Gender;
  category_slug: string;
  category_name: string;
  base_price: number;
  sale_price: number | null;
  effective_price: number;
  primary_image: string;
  available_colors: string[];
  is_featured: boolean;
  in_stock: boolean;
}

export interface ProductColor {
  name: string;
  hex: string;
}

export interface Product {
  id: string;
  slug: string;
  name: string;
  brand: string;
  description: string;
  short_description: string;
  gender: Gender;
  category: Category;
  base_price: number;
  sale_price: number | null;
  effective_price: number;
  material: string;
  care_instructions: string;
  occasion_tags: string[];
  style_tags: string[];
  season_tags: string[];
  is_featured: boolean;
  variants: ProductVariant[];
  available_sizes: string[];
  available_colors: ProductColor[];
}

export interface ProductListResponse {
  items: ProductListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type SortOption =
  | "newest"
  | "price_asc"
  | "price_desc"
  | "featured"
  | "name_asc"
  | "biggest_discount";

export interface ProductFilters {
  q?: string;
  gender?: Gender;
  category?: string[];
  size?: string[];
  color?: string[];
  brand?: string[];
  material?: string[];
  occasion?: string[];
  season?: string[];
  min_price?: number;
  max_price?: number;
  in_stock_only?: boolean;
  sale_only?: boolean;
  sort?: SortOption;
  page?: number;
  page_size?: number;
}

export interface ProductFacets {
  brands: string[];
  materials: string[];
  occasions: string[];
  seasons: string[];
  min_price: number;
  max_price: number;
}

export interface CartItemVariant {
  id: string;
  sku: string;
  size: string;
  color_name: string;
  color_hex: string;
  image_url: string;
  inventory_quantity: number;
  product_id: string;
  product_name: string;
  product_slug: string;
  product_brand: string;
  unit_price: number;
}

export interface CartItem {
  id: string;
  quantity: number;
  variant: CartItemVariant;
  line_total: number;
}

export interface Cart {
  id: string;
  items: CartItem[];
  subtotal: number;
  item_count: number;
  coupon_code: string | null;
  coupon_error: string | null;
  discount_amount: number;
  shipping_estimate: number;
  tax_estimate: number;
  estimated_total: number;
  free_shipping_remaining: number;
}

export interface WishlistItem {
  id: string;
  product_id: string;
  slug: string;
  name: string;
  brand: string;
  primary_image: string;
  base_price: number;
  sale_price: number | null;
  effective_price: number;
  on_sale: boolean;
  in_stock: boolean;
}

export interface Wishlist {
  items: WishlistItem[];
}

export interface ShippingAddressInput {
  full_name: string;
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone: string;
}

export type OrderStatus =
  | "pending"
  | "paid"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "returned";

export interface OrderItem {
  id: string;
  product_name: string;
  variant_size: string;
  variant_color: string;
  unit_price: number;
  quantity: number;
  line_total: number;
  product_slug: string | null;
  image_url: string | null;
}

export interface OrderStatusHistoryEntry {
  status: OrderStatus;
  note: string | null;
  created_at: string;
}

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: number;
  discount_amount: number;
  shipping_cost: number;
  tax: number;
  total: number;
  coupon_code: string | null;
  customer_notes: string | null;
  shipping_address: ShippingAddressInput;
  items: OrderItem[];
  status_history: OrderStatusHistoryEntry[];
  can_cancel: boolean;
  created_at: string;
}

export interface OrderSummary {
  id: string;
  order_number: string;
  status: OrderStatus;
  total: number;
  item_count: number;
  created_at: string;
}

export interface StylistOutfitItem {
  product_id: string;
  variant_id: string;
  reason: string;
  product_name: string;
  product_slug: string;
  brand: string;
  image_url: string;
  price: number;
  size: string;
  color_name: string;
  color_hex: string;
}

export interface StylistOutfit {
  id: string | null;
  name: string;
  explanation: string;
  total_price: number;
  items: StylistOutfitItem[];
}

export interface StylistResponse {
  session_id: string;
  summary: string;
  outfits: StylistOutfit[];
  follow_up_suggestions: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSessionSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail {
  id: string;
  title: string;
  messages: ChatMessage[];
  outfits: StylistOutfit[];
}

export interface AdminVariant {
  id: string;
  sku: string;
  size: string;
  color_name: string;
  color_hex: string;
  inventory_quantity: number;
  image_url: string;
}

export interface AdminProduct {
  id: string;
  slug: string;
  name: string;
  brand: string;
  gender: Gender;
  category_id: string;
  base_price: number;
  sale_price: number | null;
  is_featured: boolean;
  is_active: boolean;
  variants: AdminVariant[];
  created_at: string;
}

export interface AdminOrderItem {
  product_name: string;
  variant_size: string;
  variant_color: string;
  unit_price: number;
  quantity: number;
}

export interface AdminOrder {
  id: string;
  order_number: string;
  status: OrderStatus;
  customer_email: string;
  total: number;
  items: AdminOrderItem[];
  created_at: string;
}

export interface AdminProductListResponse {
  items: AdminProduct[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminOrderListResponse {
  items: AdminOrder[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AdminCustomer {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  order_count: number;
  total_spent: number;
  created_at: string;
}

export interface AdminCustomerListResponse {
  items: AdminCustomer[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface BestSellingProduct {
  product_id: string;
  name: string;
  slug: string;
  units_sold: number;
}

export interface TopCategory {
  category_name: string;
  category_slug: string;
  revenue: number;
}

export interface AdminDashboard {
  total_revenue: number;
  total_orders: number;
  total_customers: number;
  average_order_value: number;
  low_stock_variant_count: number;
  out_of_stock_variant_count: number;
  best_selling_products: BestSellingProduct[];
  recent_orders: AdminOrder[];
  top_categories: TopCategory[];
}

export type DiscountType = "fixed" | "percentage";

export interface AdminCoupon {
  id: string;
  code: string;
  discount_type: DiscountType;
  discount_value: number;
  free_shipping: boolean;
  min_order_value: number | null;
  max_discount: number | null;
  starts_at: string | null;
  expires_at: string | null;
  is_active: boolean;
  usage_limit: number | null;
  per_user_limit: number | null;
  applicable_categories: string[];
  applicable_products: string[];
  total_redemptions: number;
  created_at: string;
}

export interface AdminCouponInput {
  code: string;
  discount_type: DiscountType;
  discount_value: number;
  free_shipping?: boolean;
  min_order_value?: number | null;
  max_discount?: number | null;
  is_active?: boolean;
  usage_limit?: number | null;
  per_user_limit?: number | null;
}

export interface ApiErrorShape {
  detail: string;
}

export interface Address {
  id: string;
  full_name: string;
  line1: string;
  line2?: string | null;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone: string;
  is_default_shipping: boolean;
  is_default_billing: boolean;
}

export type AddressInput = Omit<Address, "id">;

export interface StyleProfile {
  gender_presentation: string | null;
  preferred_colors: string[];
  disliked_colors: string[];
  preferred_styles: string[];
  favorite_occasions: string[];
  preferred_brands: string[];
  sizes: Record<string, string>;
  budget_min: number | null;
  budget_max: number | null;
}

export type FitFeedback = "runs_small" | "true_to_size" | "runs_large";
export type ReviewSort = "newest" | "highest" | "lowest" | "most_helpful";

export interface Review {
  id: string;
  product_id: string;
  user_id: string;
  author_name: string;
  rating: number;
  title: string;
  body: string;
  fit_feedback: FitFeedback | null;
  size_purchased: string | null;
  is_verified_purchase: boolean;
  is_active: boolean;
  helpful_count: number;
  helpful_by_me: boolean;
  is_mine: boolean;
  created_at: string;
}

export interface RatingDistribution {
  one: number;
  two: number;
  three: number;
  four: number;
  five: number;
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
  average_rating: number;
  distribution: RatingDistribution;
}
