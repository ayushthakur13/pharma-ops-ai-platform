export type UserRole = "Super Admin" | "Manager" | "Pharmacist" | "Staff";

export interface UserSummary {
  id: number;
  email: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserSummary;
}

export interface CurrentUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface RegisterResponse {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface ApiError {
  detail?: string;
  message?: string;
}

export interface StockItem {
  id: number;
  product_id: number;
  store_id: number;
  quantity_on_hand: number;
  reorder_level: number;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  price: string;
  unit: string;
}

export interface Batch {
  id: number;
  product_id: number;
  store_id: number;
  batch_number: string;
  expiry_date: string;
  quantity: number;
}

export interface Prescription {
  id: number;
  patient_id: string;
  store_id: number;
  created_by_user_id: number;
  status: string;
  created_at: string;
}

export interface Transaction {
  id: number;
  prescription_id: number;
  store_id: number;
  created_by_user_id: number;
  payment_method: string;
  total_amount: string;
  created_at: string;
}

export interface StockAgingResponse {
  store_id: number;
  aging_buckets: Array<{ range: string; count: number }>;
}

export interface DemandTrendsResponse {
  store_id: number;
  trend: Array<{ date: string; transactions: number }>;
}

export interface StorePerformanceResponse {
  stores: Array<{
    store_id: number;
    stock_out_rate: number;
    transaction_count: number;
    revenue: string;
  }>;
}

export interface ReplenishmentResponse {
  recommendations: Array<{
    product_id: number;
    suggested_order_quantity: number;
    reason: string;
    source: "rule_based" | "ai";
  }>;
}

export interface AnomalyResponse {
  anomalies: Array<{
    type: string;
    severity: "low" | "medium" | "high";
    confidence: number;
    explanation: string;
  }>;
  source: "rule_based" | "ai";
}

export interface AIQueryResponse {
  answer: string;
  intent: string;
  source: "rule_based" | "ai";
  data: Record<string, unknown>;
}

export interface OfflineQueuedResult {
  offline_queued: true;
  queued_at: string;
}
