// KiranaFlow AI - TypeScript Type Definitions

export interface Product {
  id: number;
  name: string;
  category: string;
  brand: string;
  unit: string;
  price: number;
  cost_price?: number;
  stock: number;
  low_stock_threshold: number;
  description: string;
  aliases: string[];
  is_active: boolean;
}

export interface Customer {
  id: number;
  name: string;
  phone: string;
  address: string;
  created_at: string;
}

export interface CustomerWithStats extends Customer {
  order_count: number;
  total_spent: number;
  last_order_at: string | null;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface OrderBrief {
  id: number;
  customer_name: string;
  item_count: number;
  total: number;
  status: string;
  created_at: string;
}

export interface OrderDetail {
  id: number;
  display_id: string;
  customer_id: number;
  customer_name: string;
  customer_phone: string;
  status: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
  delivery_address: string;
  delivery_requested: boolean;
  original_request: string;
  channel: string;
  created_at: string;
  items: OrderItem[];
  agent_events: AgentEvent[];
}

export interface AgentEvent {
  id: number;
  order_id: number | null;
  session_id: string | null;
  event_type: string;
  description: string;
  status: string;
  tool_name: string | null;
  tool_input: Record<string, unknown> | null;
  tool_output: Record<string, unknown> | null;
  confidence: number | null;
  timestamp: string;
}

export interface ResolvedItem {
  product_id: number;
  product_name: string;
  brand: string;
  unit: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  stock_available: number;
  confidence: number;
  match_explanation: string;
  cost_price?: number;
}

export interface AlternativeSuggestion {
  original_query: string;
  product: Product;
  reason: string;
}

export interface LowStockAlert {
  product_name: string;
  current_stock: number;
  threshold: number;
  suggested_restock: number;
}

export interface OrderResult {
  success: boolean;
  order_id: number | null;
  order_display_id: string;
  customer_name: string;
  items: ResolvedItem[];
  subtotal: number;
  delivery_fee: number;
  total: number;
  delivery_requested: boolean;
  delivery_address: string;
  confirmation_message: string;
  low_stock_alerts: LowStockAlert[];
  agent_events: AgentEvent[];
  alternatives: AlternativeSuggestion[];
  error: string | null;
  operator_confidence?: {
    product_matching: number;
    inventory_verification: number;
    order_confidence: number;
  };
  delivery_person?: {
    name: string;
    phone: string;
    vehicle: string;
  };
  bill_summary?: string;
  dispatch?: {
    customer_message?: {
      order_id: string;
      status: string;
      text?: string;
      delivery_person: { name: string; phone: string; vehicle: string };
      estimated_time: string;
      bill_summary: string;
      total: number;
    };
    delivery_person_message?: {
      order_id: string;
      text?: string;
      customer: { name: string; phone: string; address: string };
      items: { product_name: string; quantity: number; unit_price: number; total_price: number }[];
      total: number;
      payment_mode: string;
      bill_summary: string;
    };
    delivery_person_name?: string;
    delivery_person_phone?: string;
  };
  confirmation_message_hi?: string;
  needs_selection?: boolean;
  understood_as?: string;
  pending_choices?: {
    original_query: string;
    quantity: number;
    unit: string;
    options: Product[];
  }[];
}

export interface DashboardStats {
  today_orders: number;
  today_revenue: number;
  today_profit: number;
  today_margin_pct: number;
  week_orders: number;
  week_revenue: number;
  week_profit: number;
  week_margin_pct: number;
  month_orders: number;
  month_revenue: number;
  month_profit: number;
  month_margin_pct: number;
  low_stock_count: number;
  pending_deliveries: number;
  total_products: number;
  total_customers: number;
  inventory_value: number;
  potential_profit: number;
}

export interface InventoryTransaction {
  id: number;
  product_id: number;
  product_name: string;
  type: string;
  quantity: number;
  previous_stock: number;
  new_stock: number;
  order_id: number | null;
  timestamp: string;
}
