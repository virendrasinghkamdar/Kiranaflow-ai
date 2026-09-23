// KiranaFlow AI - API Service Layer

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Agent ──

export async function processCustomerRequest(
  message: string,
  customerPhone: string = '9876543210',
  channel: string = 'whatsapp',
  selections: { product_query: string; product_id: number; quantity: number }[] = []
) {
  return request('/agent/process', {
    method: 'POST',
    body: JSON.stringify({
      message,
      customer_phone: customerPhone,
      channel,
      selections,
    }),
  });
}

// ── Dashboard ──

export async function getDashboardStats() {
  return request('/dashboard');
}

// ── Products ──

export async function getProducts(category?: string) {
  const params = category ? `?category=${encodeURIComponent(category)}` : '';
  return request(`/products${params}`);
}

export async function getProductCategories() {
  return request<string[]>('/products/categories');
}

export async function getLowStockProducts() {
  return request('/products/low-stock');
}

export async function searchProducts(query: string) {
  return request(`/products?search=${encodeURIComponent(query)}`);
}

// ── Dashboard Drilldowns ──

export async function getDashboardLowStock() {
  return request('/dashboard/low-stock');
}

export async function getDashboardPendingDeliveries() {
  return request('/dashboard/pending-deliveries');
}

export async function getDashboardRevenueBreakdown() {
  return request('/dashboard/revenue-breakdown');
}

export async function getNeighborhoodPulse() {
  return request('/dashboard/pulse');
}

// ── Orders ──

export async function getOrders(status?: string) {
  const params = status ? `?status=${encodeURIComponent(status)}` : '';
  return request(`/orders${params}`);
}

export async function getOrderDetail(orderId: number) {
  return request(`/orders/${orderId}`);
}

// ── Customers ──

export async function getCustomers() {
  return request('/customers');
}

export async function getCustomerDetail(customerId: number) {
  return request(`/customers/${customerId}`);
}

export async function lookupCustomerByPhone(phone: string) {
  return request<any>(`/customers/lookup?phone=${encodeURIComponent(phone)}`);
}

// ── Delivery ──

export async function getDeliveryPersons() {
  return request('/delivery/persons');
}

export async function dispatchDelivery(orderId: number) {
  return request(`/delivery/dispatch/${orderId}`, { method: 'POST' });
}

export async function completeDelivery(orderId: number) {
  return request(`/delivery/complete/${orderId}`, { method: 'POST' });
}

// ── Events ──

export async function getAgentEvents(filters?: {
  order_id?: number;
  event_type?: string;
  status?: string;
}) {
  const params = new URLSearchParams();
  if (filters?.order_id) params.set('order_id', String(filters.order_id));
  if (filters?.event_type) params.set('event_type', filters.event_type);
  if (filters?.status) params.set('status', filters.status);
  const qs = params.toString();
  return request(`/events${qs ? `?${qs}` : ''}`);
}

// ── Inventory Transactions ──

export async function getInventoryTransactions(productId?: number) {
  const params = productId ? `?product_id=${productId}` : '';
  return request(`/inventory-transactions${params}`);
}

// ── Health ──

export async function healthCheck() {
  return request('/health');
}
