export type Gender = "men" | "women" | "unisex";

export type UserRole = "customer" | "admin";

export interface User {
  id: string;
  email: string;
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

export type SortOption = "newest" | "price_asc" | "price_desc" | "featured" | "name_asc";

export interface ProductFilters {
  q?: string;
  gender?: Gender;
  category?: string[];
  size?: string[];
  color?: string[];
  min_price?: number;
  max_price?: number;
  sort?: SortOption;
  page?: number;
  page_size?: number;
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
}

export interface WishlistItem {
  id: string;
  product_id: string;
  slug: string;
  name: string;
  brand: string;
  primary_image: string;
  effective_price: number;
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
  | "cancelled";

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

export interface Order {
  id: string;
  order_number: string;
  status: OrderStatus;
  subtotal: number;
  shipping_cost: number;
  tax: number;
  total: number;
  shipping_address: ShippingAddressInput;
  items: OrderItem[];
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

export interface ApiErrorShape {
  detail: string;
}
