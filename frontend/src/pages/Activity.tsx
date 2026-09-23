// KiranaFlow AI - Agent Activity Page

import { useState, useEffect } from 'react';
import { getAgentEvents } from '../services/api';
import type { AgentEvent } from '../types';

const EVENT_TYPES = [
  'REQUEST_RECEIVED', 'INTENT_DETECTED', 'CUSTOMER_FOUND', 'CUSTOMER_CREATED',
  'PRODUCT_SEARCHED', 'PRODUCT_RESOLVED', 'PRODUCT_NOT_FOUND', 'PRODUCT_UNAVAILABLE',
  'ALTERNATIVE_FOUND', 'PRODUCT_SUBSTITUTED',
  'INVENTORY_CHECKED', 'PRICE_RETRIEVED', 'ORDER_CALCULATED',
  'ORDER_CREATED', 'ORDER_FAILED',
  'INVENTORY_UPDATED', 'LOW_STOCK_CHECKED',
  'CONFIRMATION_SENT', 'DELIVERY_DISPATCHED', 'BRAND_CHOICE_REQUIRED',
  'REPEAT_LAST_ORDER', 'PIPELINE_ERROR',
];

export default function Activity() {
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await getAgentEvents({
        event_type: filterType || undefined,
        status: filterStatus || undefined,
      }) as AgentEvent[];
      setEvents(data);
    } catch { /* */ }
    setLoading(false);
  };

  useEffect(() => { fetchEvents(); }, [filterType, filterStatus]);

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
      ' ' + d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
  };

  const getEventColor = (type: string) => {
    if (type.includes('ERROR') || type.includes('FAILED') || type.includes('NOT_FOUND')) return '#EF4444';
    if (type.includes('UNAVAILABLE') || type.includes('LOW_STOCK')) return '#F59E0B';
    if (type.includes('CREATED') || type.includes('CONFIRMED') || type.includes('SENT')) return '#10B981';
    return 'var(--text-secondary)';
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Agent Activity</h1>
        <p className="page-subtitle">
          Complete autonomous agent execution history
        </p>
      </div>

      <div className="filter-bar">
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="">All Event Types</option>
          {EVENT_TYPES.map(t => (
            <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="warning">Warning</option>
        </select>
        <button className="btn btn-secondary btn-sm" onClick={fetchEvents}>↻ Refresh</button>
      </div>

      <div className="card">
        {loading ? (
          <div className="loading-overlay"><div className="spinner" /> Loading activity...</div>
        ) : events.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🤖</div>
            <h3>No agent activity yet</h3>
            <p>Process a customer request to see the agent in action.</p>
          </div>
        ) : (
          <div style={{ padding: '16px' }}>
            {events.map((event, i) => (
              <div
                key={event.id}
                style={{
                  display: 'flex', gap: '12px', padding: '12px 0',
                  borderBottom: i < events.length - 1 ? '1px solid var(--border-light)' : 'none',
                }}
              >
                {/* Timeline dot */}
                <div style={{
                  width: 10, height: 10, borderRadius: '50%',
                  background: event.status === 'completed' ? 'var(--brand-500)' :
                    event.status === 'failed' ? 'var(--error)' : 'var(--warning)',
                  marginTop: 5, flexShrink: 0,
                }} />

                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span style={{
                      fontWeight: 600, fontSize: '0.82rem',
                      color: getEventColor(event.event_type),
                    }}>
                      {event.event_type.replace(/_/g, ' ')}
                    </span>
                    {event.tool_name && (
                      <span style={{
                        fontFamily: 'monospace', fontSize: '0.7rem',
                        padding: '1px 8px', background: 'var(--bg-tertiary)',
                        borderRadius: '4px', color: 'var(--brand-700)',
                      }}>
                        {event.tool_name}()
                      </span>
                    )}
                    {event.confidence !== null && event.confidence !== undefined && (
                      <span className={`confidence-badge ${event.confidence >= 0.9 ? 'high' : event.confidence >= 0.7 ? 'medium' : 'low'}`}>
                        {Math.round(event.confidence * 100)}%
                      </span>
                    )}
                    {event.order_id && (
                      <span style={{
                        fontFamily: 'monospace', fontSize: '0.7rem',
                        color: 'var(--text-tertiary)',
                      }}>
                        KF-{1000 + event.order_id}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: 2 }}>
                    {event.description}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {formatTime(event.timestamp)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
