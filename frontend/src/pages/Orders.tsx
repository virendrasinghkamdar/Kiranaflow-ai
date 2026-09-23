// KiranaFlow AI - Orders Page

import { useState, useEffect } from 'react';
import { getOrders, getOrderDetail } from '../services/api';
import type { OrderBrief, OrderDetail, AgentEvent } from '../types';

export default function Orders() {
  const [orders, setOrders] = useState<OrderBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    getOrders()
      .then((data: any) => setOrders(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const openOrder = async (orderId: number) => {
    setDetailLoading(true);
    try {
      const detail = await getOrderDetail(orderId) as OrderDetail;
      setSelectedOrder(detail);
    } catch { /* */ }
    setDetailLoading(false);
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Orders</h1>
        <p className="page-subtitle">{orders.length} orders</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedOrder ? '1fr 1.2fr' : '1fr', gap: '16px' }}>
        {/* Orders List */}
        <div className="card">
          {loading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading orders...</div>
          ) : orders.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📦</div>
              <h3>No orders yet</h3>
              <p>Process a customer request from the dashboard to create orders.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Customer</th>
                  <th style={{ textAlign: 'center' }}>Items</th>
                  <th style={{ textAlign: 'right' }}>Total</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr
                    key={order.id}
                    onClick={() => openOrder(order.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--brand-700)' }}>
                      KF-{1000 + order.id}
                    </td>
                    <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{order.customer_name}</td>
                    <td style={{ textAlign: 'center' }}>{order.item_count}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{order.total}</td>
                    <td>
                      <span className="stock-badge in-stock" style={{ textTransform: 'capitalize' }}>
                        {order.status}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                      {formatDate(order.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Order Detail Panel */}
        {selectedOrder && (
          <div className="card">
            <div className="card-header">
              <h3>Order #{selectedOrder.display_id}</h3>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedOrder(null)}
              >
                ✕ Close
              </button>
            </div>
            <div className="card-body">
              {detailLoading ? (
                <div className="loading-overlay"><div className="spinner" /></div>
              ) : (
                <>
                  {/* Customer Info */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 4 }}>
                      Customer
                    </div>
                    <div style={{ fontWeight: 600 }}>{selectedOrder.customer_name}</div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {selectedOrder.customer_phone} · {selectedOrder.channel}
                    </div>
                  </div>

                  {/* Original Request */}
                  {selectedOrder.original_request && (
                    <div style={{
                      padding: '12px 16px', background: 'var(--bg-tertiary)',
                      borderRadius: 'var(--radius-sm)', marginBottom: 16,
                      fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text-secondary)',
                    }}>
                      "{selectedOrder.original_request}"
                    </div>
                  )}

                  {/* Items */}
                  <div style={{ marginBottom: 16 }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 8 }}>
                      Items
                    </div>
                    {selectedOrder.items.map((item, i) => (
                      <div key={i} className="order-line">
                        <span>{item.quantity} × {item.product_name}</span>
                        <span style={{ fontWeight: 600 }}>₹{item.total_price}</span>
                      </div>
                    ))}
                    <div className="order-line" style={{ color: 'var(--text-tertiary)' }}>
                      <span>Subtotal</span><span>₹{selectedOrder.subtotal}</span>
                    </div>
                    {selectedOrder.delivery_fee > 0 && (
                      <div className="order-line" style={{ color: 'var(--text-tertiary)' }}>
                        <span>Delivery</span><span>₹{selectedOrder.delivery_fee}</span>
                      </div>
                    )}
                    <div className="order-total-line">
                      <span>TOTAL</span><span>₹{selectedOrder.total}</span>
                    </div>
                  </div>

                  {/* Agent Events */}
                  {selectedOrder.agent_events && selectedOrder.agent_events.length > 0 && (
                    <div>
                      <div style={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: 8 }}>
                        Agent Execution History
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {selectedOrder.agent_events.map((event: AgentEvent, i: number) => (
                          <div key={i} className="event-step">
                            <div className={`step-icon ${event.status === 'failed' ? 'failed' : 'completed'}`}>
                              {event.status === 'failed' ? '✗' : '✓'}
                            </div>
                            <div className="step-text">
                              <strong>{event.event_type.replace(/_/g, ' ')}</strong>
                              <br />
                              <span style={{ fontSize: '0.75rem' }}>{event.description}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
