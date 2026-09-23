// KiranaFlow AI - Enhanced Customers Page
// Shows full customer profiles with purchase history and detailed order breakdown

import { useState, useEffect } from 'react';
import { getCustomers, getCustomerDetail } from '../services/api';
import type { CustomerWithStats } from '../types';

export default function Customers() {
  const [customers, setCustomers] = useState<CustomerWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    getCustomers()
      .then((data: any) => setCustomers(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const openCustomer = async (id: number) => {
    try {
      const detail = await getCustomerDetail(id);
      setSelectedCustomer(detail);
    } catch { /* */ }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const filtered = searchQuery.trim()
    ? customers.filter(c =>
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.phone.includes(searchQuery)
    )
    : customers;

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1>Customers</h1>
          <p className="page-subtitle">{customers.length} customers in your neighborhood</p>
        </div>
      </div>

      <div className="filter-bar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name or phone..."
          />
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selectedCustomer ? '1fr 1fr' : '1fr', gap: '16px' }}>
        <div className="card">
          {loading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading...</div>
          ) : filtered.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">👥</div>
              <h3>No customers found</h3>
              <p>Customers are created automatically when orders are processed.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Area</th>
                  <th style={{ textAlign: 'center' }}>Orders</th>
                  <th style={{ textAlign: 'right' }}>Total Spent</th>
                  <th>Last Order</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(c => (
                  <tr key={c.id} onClick={() => openCustomer(c.id)} style={{ cursor: 'pointer' }}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {c.name}
                      {(c as any).preferred_time && (
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', fontWeight: 400 }}>
                          🕐 {(c as any).preferred_time}
                        </div>
                      )}
                    </td>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.82rem' }}>{c.phone}</td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.address?.split(',').slice(0, 2).join(',') || '—'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{
                        fontWeight: 600,
                        color: c.order_count >= 3 ? 'var(--brand-600)' : 'var(--text-secondary)',
                      }}>{c.order_count}</span>
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{c.total_spent.toLocaleString('en-IN')}</td>
                    <td style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)' }}>
                      {formatDate(c.last_order_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {selectedCustomer && (
          <div className="card">
            <div className="card-header">
              <h3>{selectedCustomer.name}</h3>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedCustomer(null)}>
                ✕ Close
              </button>
            </div>
            <div className="card-body">
              <div style={{
                padding: '16px', marginBottom: 16,
                background: 'linear-gradient(135deg, var(--brand-50), rgba(255,255,255,0.5))',
                borderRadius: 'var(--radius-md)',
              }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 4 }}>
                  📞 <strong>{selectedCustomer.phone}</strong>
                </div>
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 4 }}>
                  📍 {selectedCustomer.address || 'No address'}
                </div>
                {selectedCustomer.email && (
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: 4 }}>
                    ✉️ {selectedCustomer.email}
                  </div>
                )}
                {selectedCustomer.preferred_time && (
                  <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    🕐 Preferred: {selectedCustomer.preferred_time} delivery
                  </div>
                )}
                <div style={{
                  display: 'flex', gap: 16, marginTop: 12, paddingTop: 12,
                  borderTop: '1px solid var(--border-light)',
                }}>
                  <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--brand-700)' }}>
                      ₹{selectedCustomer.total_spent?.toLocaleString('en-IN')}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)' }}>Total Spent</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {selectedCustomer.orders?.length || 0}
                    </div>
                    <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)' }}>Orders</div>
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                Order History
              </div>
              {selectedCustomer.orders?.length > 0 ? (
                selectedCustomer.orders.map((o: any) => (
                  <div key={o.id} style={{
                    padding: '12px 14px', background: 'var(--bg-tertiary)',
                    borderRadius: 'var(--radius-sm)', marginBottom: 8,
                    border: '1px solid var(--border-light)',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--brand-700)', fontSize: '0.85rem' }}>
                        {o.display_id}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>₹{o.total}</span>
                    </div>
                    {o.items?.length > 0 && (
                      <div style={{ paddingLeft: 8 }}>
                        {o.items.map((item: any, idx: number) => (
                          <div key={idx} style={{
                            display: 'flex', justifyContent: 'space-between',
                            fontSize: '0.78rem', color: 'var(--text-secondary)', padding: '2px 0',
                          }}>
                            <span>{item.quantity}× {item.product_name}</span>
                            <span>₹{item.total_price}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)', marginTop: 4 }}>
                      {new Date(o.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ fontSize: '0.82rem', color: 'var(--text-tertiary)', padding: '16px', textAlign: 'center' }}>
                  No orders yet
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
