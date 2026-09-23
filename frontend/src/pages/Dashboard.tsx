// KiranaFlow AI - Dashboard (Overview) Page
// Premium UI with interactive stat cards, voice input, and autonomous pipeline visualization

import { useState, useEffect, useRef } from 'react';
import {
  getDashboardStats, processCustomerRequest,
  getDashboardLowStock, getDashboardPendingDeliveries,
  getDashboardRevenueBreakdown, getOrders,
  lookupCustomerByPhone, dispatchDelivery,
  getNeighborhoodPulse,
} from '../services/api';
import type { DashboardStats, OrderResult, AgentEvent, ResolvedItem } from '../types';

const QUICK_PROMPTS = [
  { text: "Bhaiya 2 kilo aata bhej do.", emoji: "🌾" },
  { text: "Bhaiya 2 atta, 1 Fortune oil aur 3 Maggi bhej do.", emoji: "🛒" },
  { text: "2 packet Maggi aur ek Tata Salt ghar pe bhej dena.", emoji: "🍜" },
  { text: "Pichla order dobara bhej do.", emoji: "🔁" },
];

// ── Drilldown Modal ──
function DrilldownModal({ title, icon, onClose, children }: {
  title: string; icon: string; onClose: () => void; children: React.ReactNode;
}) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.3rem' }}>{icon}</span>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 700 }}>{title}</h3>
          </div>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [message, setMessage] = useState('');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<OrderResult | null>(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [customerPhone, setCustomerPhone] = useState('9876543210');

  // Customer lookup
  const [customerProfile, setCustomerProfile] = useState<any>(null);
  const [lookingUp, setLookingUp] = useState(false);

  // Delivery dispatch
  const [dispatchInfo, setDispatchInfo] = useState<any>(null);
  const [dispatching, setDispatching] = useState(false);

  // Drilldown state
  const [drilldown, setDrilldown] = useState<string | null>(null);
  const [drilldownData, setDrilldownData] = useState<any>(null);
  const [drilldownLoading, setDrilldownLoading] = useState(false);

  // Voice input
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  // Processing step animation
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [pulse, setPulse] = useState<any>(null);
  const [range, setRange] = useState<'today' | 'week' | 'month'>('today');
  const [confirmLang, setConfirmLang] = useState<'en' | 'hi'>('hi');
  const lastMessageRef = useRef('');

  // Customer phone lookup
  const handlePhoneLookup = async (phone: string) => {
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 10) { setCustomerProfile(null); return; }
    setLookingUp(true);
    try {
      const data = await lookupCustomerByPhone(digits);
      setCustomerProfile(data);
    } catch { setCustomerProfile(null); }
    setLookingUp(false);
  };

  useEffect(() => {
    const timer = setTimeout(() => handlePhoneLookup(customerPhone), 350);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerPhone]);

  // Dispatch delivery after confirmation
  const handleDispatch = async () => {
    if (!result?.order_id || dispatching) return;
    setDispatching(true);
    try {
      const info = await dispatchDelivery(result.order_id);
      setDispatchInfo(info);
    } catch { /* */ }
    setDispatching(false);
  };

  useEffect(() => {
    getDashboardStats()
      .then((d: any) => setStats(d))
      .catch(() => {});
    getNeighborhoodPulse()
      .then(setPulse)
      .catch(() => {});
  }, [result]);

  // Animate agent events appearing one by one
  useEffect(() => {
    if (result?.agent_events?.length) {
      setVisibleSteps(0);
      const timer = setInterval(() => {
        setVisibleSteps(prev => {
          if (prev >= result.agent_events.length) {
            clearInterval(timer);
            return prev;
          }
          return prev + 1;
        });
      }, 120);
      return () => clearInterval(timer);
    }
  }, [result]);

  const handleSubmit = async (overrideMessage?: string, selections?: { product_query: string; product_id: number; quantity: number }[]) => {
    const text = (overrideMessage ?? message).trim();
    if (!text || processing) return;
    lastMessageRef.current = text;
    setMessage(text);
    setProcessing(true);
    setResult(null);
    setShowConfirmation(false);
    setDispatchInfo(null);

    try {
      const res = await processCustomerRequest(text, customerPhone, 'whatsapp', selections || []) as OrderResult;
      setResult(res);
      if (res.success) {
        if (res.dispatch) setDispatchInfo(res.dispatch);
        handlePhoneLookup(customerPhone);
        setTimeout(() => setShowConfirmation(true), 800);
      }
    } catch (err: any) {
      setResult({
        success: false,
        order_id: null,
        order_display_id: '',
        customer_name: '',
        items: [],
        subtotal: 0,
        delivery_fee: 0,
        total: 0,
        delivery_requested: false,
        delivery_address: '',
        confirmation_message: '',
        low_stock_alerts: [],
        agent_events: [],
        alternatives: [],
        error: err.message || 'Failed to process request',
      });
    } finally {
      setProcessing(false);
    }
  };

  // ── Voice Input ──
  const toggleVoice = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Voice input is not supported in this browser. Try Chrome.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'hi-IN';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((r: any) => r[0].transcript)
        .join('');
      setMessage(transcript);
    };

    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  // ── Drilldown Handlers ──
  const openDrilldown = async (type: string) => {
    setDrilldown(type);
    setDrilldownLoading(true);
    try {
      let data;
      switch (type) {
        case 'low-stock': data = await getDashboardLowStock(); break;
        case 'pending-deliveries': data = await getDashboardPendingDeliveries(); break;
        case 'revenue': data = await getDashboardRevenueBreakdown(); break;
        case 'orders': data = await getOrders(); break;
      }
      setDrilldownData(data);
    } catch { setDrilldownData(null); }
    setDrilldownLoading(false);
  };

  const getEventIcon = (event: AgentEvent) => {
    const map: Record<string, string> = {
      'REQUEST_RECEIVED': '📨', 'INTENT_DETECTED': '🧠', 'CUSTOMER_FOUND': '👤',
      'CUSTOMER_CREATED': '👤', 'PRODUCT_SEARCHED': '🔍', 'PRODUCT_RESOLVED': '✅',
      'INVENTORY_CHECKED': '📊', 'PRODUCT_UNAVAILABLE': '❌', 'ALTERNATIVE_FOUND': '🔄',
      'PRODUCT_SUBSTITUTED': '🔄', 'PRICE_RETRIEVED': '💰', 'ORDER_CALCULATED': '🧮',
      'ORDER_CREATED': '📝', 'INVENTORY_UPDATED': '📦', 'LOW_STOCK_CHECKED': '⚠️',
      'CONFIRMATION_SENT': '✉️', 'DELIVERY_DISPATCHED': '🛵', 'BRAND_CHOICE_REQUIRED': '🏷️',
      'REPEAT_LAST_ORDER': '🔁', 'PIPELINE_ERROR': '🚨',
    };
    return map[event.event_type] || (event.status === 'failed' ? '❌' : '✅');
  };

  const getConfidenceClass = (c: number | null) => {
    if (!c) return 'high';
    if (c >= 0.9) return 'high';
    if (c >= 0.7) return 'medium';
    return 'low';
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  };

  const perf = !stats ? null : range === 'week'
    ? { label: 'This week', orders: stats.week_orders, revenue: stats.week_revenue, profit: stats.week_profit, margin: stats.week_margin_pct }
    : range === 'month'
      ? { label: 'This month', orders: stats.month_orders, revenue: stats.month_revenue, profit: stats.month_profit, margin: stats.month_margin_pct }
      : { label: 'Today', orders: stats.today_orders, revenue: stats.today_revenue, profit: stats.today_profit, margin: stats.today_margin_pct };

  return (
    <div className="page-content">
      {/* Page Header */}
      <div className="page-header hero-header">
        <div>
          <h1>Operations Center</h1>
          <p className="page-subtitle">
            Boliye kya chahiye, baaki KiranaFlow sambhale.
          </p>
        </div>
        <div className="header-badges">
          <span className="status-badge online"><span className="dot" /> Live</span>
        </div>
      </div>

      <div className="pnl-panel">
        <div className="pnl-head">
          <div>
            <div className="pnl-kicker">Performance</div>
            <h3>Sales & profit</h3>
          </div>
          <div className="range-pills">
            {(['today', 'week', 'month'] as const).map((key) => (
              <button
                key={key}
                className={range === key ? 'active' : ''}
                onClick={() => setRange(key)}
              >
                {key === 'today' ? 'Today' : key === 'week' ? 'Week' : 'Month'}
              </button>
            ))}
          </div>
        </div>
        <div className="pnl-grid">
          <div className="pnl-metric">
            <span>Sales</span>
            <strong>₹{(perf?.revenue ?? 0).toLocaleString('en-IN')}</strong>
          </div>
          <div className="pnl-metric profit">
            <span>Profit</span>
            <strong>₹{(perf?.profit ?? 0).toLocaleString('en-IN')}</strong>
          </div>
          <div className="pnl-metric">
            <span>Margin</span>
            <strong>{perf?.margin ?? 0}%</strong>
          </div>
          <div className="pnl-metric">
            <span>Orders</span>
            <strong>{perf?.orders ?? 0}</strong>
          </div>
        </div>
        <div className="pnl-foot">
          Stock value ₹{(stats?.inventory_value ?? 0).toLocaleString('en-IN')}
          <span>·</span>
          Unsold margin ₹{(stats?.potential_profit ?? 0).toLocaleString('en-IN')}
        </div>
      </div>

      {/* Stats Grid - Interactive Cards */}
      <div className="stats-grid">
        <button className="stat-card stat-card-interactive" onClick={() => openDrilldown('orders')}>
          <div className="stat-card-glow green" />
          <div className="stat-icon green">📦</div>
          <div className="stat-label">Today's Orders</div>
          <div className="stat-value">{stats?.today_orders ?? '—'}</div>
          <div className="stat-hint">Click to view details →</div>
        </button>
        <button className="stat-card stat-card-interactive" onClick={() => openDrilldown('revenue')}>
          <div className="stat-card-glow blue" />
          <div className="stat-icon blue">₹</div>
          <div className="stat-label">Today's Sales</div>
          <div className="stat-value">₹{stats?.today_revenue?.toLocaleString('en-IN') ?? '—'}</div>
          <div className="stat-hint">Today's profit ₹{stats?.today_profit?.toLocaleString('en-IN') ?? 0}</div>
        </button>
        <button className="stat-card stat-card-interactive" onClick={() => openDrilldown('low-stock')}>
          <div className="stat-card-glow amber" />
          <div className="stat-icon amber">⚠</div>
          <div className="stat-label">Low Stock</div>
          <div className="stat-value">{stats?.low_stock_count ?? '—'}</div>
          <div className="stat-hint">Click to see items →</div>
        </button>
        <button className="stat-card stat-card-interactive" onClick={() => openDrilldown('pending-deliveries')}>
          <div className="stat-card-glow red" />
          <div className="stat-icon red">🚚</div>
          <div className="stat-label">Pending Deliveries</div>
          <div className="stat-value">{stats?.pending_deliveries ?? '—'}</div>
          <div className="stat-hint">Click for details →</div>
        </button>
      </div>

      {pulse?.movers?.length > 0 && (
        <div className="mohalla-pulse">
          <span className="pulse-label">Mohalla pulse</span>
          <div className="pulse-track">
            {pulse.movers.map((m: any, i: number) => (
              <span key={i} className="pulse-chip">{m.name} · {m.qty} sold</span>
            ))}
          </div>
        </div>
      )}

      {/* Live Autonomous Operation */}
      <div className="pipeline-container">
        <div className="pipeline-header">
          <div>
            <h2>Live Operation</h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-tertiary)', margin: 0 }}>
              Request in, order out — KiranaFlow handles the rest.
            </p>
          </div>
          {processing && (
            <span className="status-badge processing">
              <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Processing
            </span>
          )}
        </div>

        {/* Customer Input */}
        <div className="input-section">
          <div className="input-meta">
            <div className="input-label">CUSTOMER REQUEST</div>
            <input
              type="text"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
              onBlur={() => handlePhoneLookup(customerPhone)}
              placeholder="Customer Phone"
              className="phone-input"
            />
            {lookingUp && <span style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>Looking up...</span>}
          </div>

          {/* Customer Profile Card */}
          {customerProfile?.found && (
            <div style={{
              padding: '12px 16px', marginBottom: '12px',
              background: 'linear-gradient(135deg, var(--brand-50), rgba(255,255,255,0.8))',
              borderRadius: 'var(--radius-md)', border: '1px solid var(--brand-100)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                    👤 {customerProfile.name}
                    {customerProfile.is_regular && (
                      <span style={{ marginLeft: 8, fontSize: '0.68rem', padding: '2px 8px', borderRadius: 100, background: '#FEF3C7', color: '#92400E', fontWeight: 600 }}>⭐ Regular</span>
                    )}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: 2 }}>📍 {customerProfile.address}</div>
                  {customerProfile.email && <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 1 }}>✉️ {customerProfile.email}</div>}
                  {customerProfile.preferred_time && <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 1 }}>🕐 Prefers: {customerProfile.preferred_time} delivery</div>}
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--brand-700)' }}>₹{customerProfile.total_spent?.toLocaleString('en-IN')}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-tertiary)' }}>{customerProfile.total_orders} orders</div>
                </div>
              </div>
              {customerProfile.frequently_bought?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Frequently Bought</div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {customerProfile.frequently_bought.map((item: any, i: number) => (
                      <span key={i} style={{
                        fontSize: '0.72rem', padding: '3px 10px', borderRadius: 100,
                        background: 'white', border: '1px solid var(--border-light)',
                        color: 'var(--text-secondary)',
                      }}>{item.product} ({item.total_qty})</span>
                    ))}
                  </div>
                </div>
              )}
              {customerProfile.order_history?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>Purchase History</div>
                  {customerProfile.order_history.slice(0, 4).map((o: any) => (
                    <div key={o.order_id} style={{
                      padding: '6px 0',
                      borderBottom: '1px solid var(--border-light)', fontSize: '0.78rem',
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--brand-700)' }}>{o.display_id}</span>
                        <span style={{ fontWeight: 600 }}>₹{o.total}</span>
                        <span style={{ color: 'var(--text-tertiary)', fontSize: '0.72rem' }}>
                          {new Date(o.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                        </span>
                      </div>
                      {o.items?.length > 0 && (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.72rem', marginTop: 2 }}>
                          {o.items.map((it: any) => `${it.quantity}× ${it.product_name}`).join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {customerProfile.order_history?.length > 0 && (
                <button
                  className="btn btn-secondary btn-sm"
                  style={{ marginTop: 10 }}
                  onClick={() => handleSubmit('Pichla order dobara bhej do.')}
                >
                  🔁 Repeat last order · Pichla wala
                </button>
              )}
            </div>
          )}
          {customerProfile && customerProfile.found === false && customerPhone.replace(/\D/g, '').length >= 10 && (
            <div style={{
              padding: '10px 14px', marginBottom: '12px',
              background: '#F9FAFB', border: '1px dashed var(--border-light)',
              borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-secondary)',
            }}>
              New customer for {customerPhone}. Name and address will be created as a walk-in on first order.
              Try a saved number like <strong>9876543210</strong> (Rahul Sharma) to see purchase history.
            </div>
          )}
          <div className="customer-input-area">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder='Try: "2 kilo aata bhej do" or "do packet maggi aur ek doodh"'
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
            />
          </div>
          <div className="input-actions">
            <div className="action-buttons">
              <button
                className="btn btn-primary"
                onClick={handleSubmit}
                disabled={processing || !message.trim()}
              >
                {processing ? (
                  <><span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} /> Processing...</>
                ) : (
                  <>🚀 Process Order</>
                )}
              </button>
              <button
                className={`btn btn-voice ${isListening ? 'listening' : ''}`}
                onClick={toggleVoice}
                title="Voice input"
              >
                {isListening ? '⏹ Stop' : '🎙 Voice'}
              </button>
            </div>
            <div className="quick-prompts">
              {QUICK_PROMPTS.map((p, i) => (
                <button
                  key={i}
                  className="quick-prompt-btn"
                  onClick={() => setMessage(p.text)}
                >
                  <span>{p.emoji}</span> {p.text.length > 40 ? p.text.slice(0, 40) + '…' : p.text}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Pipeline Results */}
        {result && (
          <div className="pipeline-body">
            {/* Agent Events Column */}
            <div className="pipeline-section">
              <div className="section-header">
                <h4>🤖 Agent Activity</h4>
                <span className="event-count">{result.agent_events.length} steps</span>
              </div>
              <div className="events-list">
                {result.agent_events.map((event, i) => {
                  const icon = getEventIcon(event);
                  const isVisible = i < visibleSteps;
                  return (
                    <div
                      key={i}
                      className={`event-step ${isVisible ? 'visible' : ''} ${event.status === 'failed' ? 'failed' : ''}`}
                    >
                      <div className="step-icon-emoji">{icon}</div>
                      <div className="step-text">
                        <div className="step-title">{event.event_type.replace(/_/g, ' ')}</div>
                        <div className="step-desc">{event.description}</div>
                        {event.confidence !== null && event.confidence !== undefined && (
                          <span className={`confidence-badge ${getConfidenceClass(event.confidence)}`}>
                            {Math.round(event.confidence * 100)}%
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Tool Activity Column */}
            <div className="pipeline-section">
              <div className="section-header">
                <h4>🔧 Tool Execution</h4>
                <span className="event-count">
                  {result.agent_events.filter(e => e.tool_name).length} calls
                </span>
              </div>
              <div className="tools-list">
                {result.agent_events
                  .filter(e => e.tool_name)
                  .map((event, i) => (
                    <div key={i} className="tool-card" style={{ animationDelay: `${i * 80}ms` }}>
                      <div className="tool-header">
                        <span className="tool-name">{event.tool_name}()</span>
                        <span className={`tool-status-badge ${event.status}`}>
                          {event.status === 'completed' ? '✓' : '✗'}
                        </span>
                      </div>
                      {event.tool_input && (
                        <div className="tool-detail">
                          {Object.entries(event.tool_input).slice(0, 3).map(([k, v]) => (
                            <div key={k} className="tool-kv">
                              <span className="tool-key">{k}:</span>
                              <span className="tool-val">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {event.tool_output && (
                        <div className="tool-detail output">
                          {Object.entries(event.tool_output).slice(0, 3).map(([k, v]) => (
                            <div key={k} className="tool-kv">
                              <span className="tool-key">{k}:</span>
                              <span className="tool-val">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>

            {/* Order Summary Column */}
            <div className="pipeline-section">
              <div className="section-header">
                <h4>📋 Order Summary</h4>
              </div>
              {result.success ? (
                <div className="order-summary">
                  <div className="order-badge">
                    <span className="order-id">#{result.order_display_id}</span>
                    <span className="order-confirmed-badge">✓ Confirmed</span>
                  </div>
                  <div className="order-customer">{result.customer_name}</div>
                  {result.understood_as && (
                    <div className="understood-bar">Heard as: {result.understood_as}</div>
                  )}

                  {result.operator_confidence && (
                    <div className="confidence-summary">
                      <div className="confidence-row">
                        <span>Product matching</span>
                        <span className={`confidence-badge ${getConfidenceClass(result.operator_confidence.product_matching)}`}>
                          {Math.round(result.operator_confidence.product_matching * 100)}%
                        </span>
                      </div>
                      <div className="confidence-row">
                        <span>Inventory verification</span>
                        <span className={`confidence-badge ${getConfidenceClass(result.operator_confidence.inventory_verification)}`}>
                          {Math.round(result.operator_confidence.inventory_verification * 100)}%
                        </span>
                      </div>
                      <div className="confidence-row">
                        <span>Order confidence</span>
                        <span className={`confidence-badge ${getConfidenceClass(result.operator_confidence.order_confidence)}`}>
                          {Math.round(result.operator_confidence.order_confidence * 100)}%
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="order-items-list">
                    {result.items.map((item: ResolvedItem, i: number) => (
                      <div key={i} className="order-line">
                        <div className="order-line-left">
                          <span className="order-qty">{item.quantity}×</span>
                          <span>{item.product_name}</span>
                        </div>
                        <span className="order-line-price">₹{item.total_price}</span>
                      </div>
                    ))}
                  </div>

                  <div className="order-totals">
                    <div className="order-line subtle">
                      <span>Subtotal</span><span>₹{result.subtotal}</span>
                    </div>
                    {result.delivery_fee > 0 && (
                      <div className="order-line subtle">
                        <span>Delivery</span><span>₹{result.delivery_fee}</span>
                      </div>
                    )}
                    <div className="order-total-line">
                      <span>TOTAL</span><span>₹{result.total}</span>
                    </div>
                    <div className="order-line subtle" style={{ color: 'var(--brand-700)', fontWeight: 600 }}>
                      <span>Profit on this order</span>
                      <span>₹{result.items.reduce((sum, item) => sum + ((item.unit_price - (item.cost_price || 0)) * item.quantity), 0).toFixed(0)}</span>
                    </div>
                  </div>

                  {result.delivery_requested && (
                    <div className="delivery-badge">🚚 Home Delivery</div>
                  )}
                  {result.delivery_person && (
                    <div className="delivery-assign-card">
                      <div className="delivery-assign-title">Out for delivery</div>
                      <div>{result.delivery_person.name} · {result.delivery_person.phone}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                        {result.delivery_person.vehicle}
                      </div>
                    </div>
                  )}

                  {/* Low Stock Alerts */}
                  {result.low_stock_alerts.map((alert, i) => (
                    <div key={i} className="low-stock-alert">
                      <div className="alert-title">⚠ Low Stock Detected</div>
                      <div className="alert-detail">
                        {alert.product_name}: {alert.current_stock} units remaining
                        (threshold: {alert.threshold}). Restock: {alert.suggested_restock} units.
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="order-error">
                  {result.understood_as && (
                    <div className="understood-bar">Heard as: {result.understood_as}</div>
                  )}
                  <div className="error-box">{result.needs_selection ? '🏷️ ' : '✗ '}{result.error}</div>
                  {result.needs_selection && result.pending_choices?.map((choice, ci) => (
                    <div key={ci} className="brand-choice-panel">
                      <h5>
                        {choice.quantity}{choice.unit ? ` ${choice.unit}` : ''} {choice.original_query} — kaunsa brand?
                      </h5>
                      <div className="brand-choice-grid">
                        {choice.options.map((opt) => (
                          <button
                            key={opt.id}
                            className="brand-choice-card"
                            disabled={opt.stock <= 0 || processing}
                            onClick={() => handleSubmit(lastMessageRef.current || message, [{
                              product_query: choice.original_query,
                              product_id: opt.id,
                              quantity: choice.quantity,
                            }])}
                          >
                            <div className="brand-choice-name">{opt.name}</div>
                            <div className="brand-choice-meta">{opt.brand} · {opt.unit}</div>
                            <div className="brand-choice-price">₹{opt.price}</div>
                            <div className={`brand-choice-stock ${opt.stock === 0 ? 'out' : ''}`}>
                              {opt.stock === 0 ? 'Out of stock' : `${opt.stock} in stock`}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                  {result.alternatives.length > 0 && (
                    <div className="alternatives-section">
                      <h5>🔄 Alternatives Found</h5>
                      {result.alternatives.map((alt, i) => (
                        <div key={i} className="alt-card">
                          <div className="alt-name">{alt.product.name}</div>
                          <div className="alt-info">₹{alt.product.price} · {alt.product.stock} in stock</div>
                          <div className="alt-reason">{alt.reason}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty State */}
        {!result && !processing && (
          <div className="empty-state">
            <div className="empty-icon-large">🏪</div>
            <h3>Ready to process orders</h3>
            <p>Type a request above, or tap a quick prompt.</p>
            <p className="empty-tagline">"Boliye kya chahiye, baaki KiranaFlow sambhale."</p>
            <div className="pipeline-flow">
              {['Request', 'Understand', 'Retrieve', 'Decide', 'Act', 'Update', 'Confirm'].map((step, i) => (
                <span key={i} className="flow-step">
                  {i > 0 && <span className="flow-arrow">→</span>}
                  {step}
                </span>
              ))}
            </div>
          </div>
        )}

        {processing && !result && (
          <div className="loading-overlay">
            <div className="processing-animation">
              <div className="spinner large" />
              <div className="processing-text">Processing through autonomous pipeline...</div>
              <div className="processing-steps">
                {['Parsing request', 'Identifying products', 'Checking inventory', 'Creating order'].map((s, i) => (
                  <span key={i} className="proc-step" style={{ animationDelay: `${i * 600}ms` }}>{s}</span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Overlay */}
      {showConfirmation && result?.success && (
        <div className="modal-overlay" onClick={() => { setShowConfirmation(false); setDispatchInfo(null); }}>
          <div className="confirmation-card" onClick={e => e.stopPropagation()} style={{ maxWidth: 520 }}>
            <div className="check-icon-animated">✓</div>
            <div className="lang-toggle">
              <button className={confirmLang === 'hi' ? 'active' : ''} onClick={() => setConfirmLang('hi')}>हिंदी</button>
              <button className={confirmLang === 'en' ? 'active' : ''} onClick={() => setConfirmLang('en')}>English</button>
            </div>
            <h2>{confirmLang === 'hi' ? 'Order Confirm!' : 'Order Confirmed!'}</h2>
            <div className="conf-detail">
              {confirmLang === 'hi'
                ? `Order #${result.order_display_id} · ${result.customer_name}`
                : `Order #${result.order_display_id} for ${result.customer_name}`}
            </div>
            {confirmLang === 'hi' && result.confirmation_message_hi && (
              <pre style={{
                textAlign: 'left', fontSize: '0.75rem', color: 'var(--text-secondary)',
                background: 'var(--bg-tertiary)', padding: 12, borderRadius: 10,
                whiteSpace: 'pre-wrap', fontFamily: 'Inter, sans-serif', marginBottom: 12,
              }}>{result.confirmation_message_hi}</pre>
            )}
            <div className="conf-items">
              {result.items.map((item, i) => (
                <div key={i} className="conf-line">
                  <span>{item.quantity} × {item.product_name}</span>
                  <span style={{ fontWeight: 600 }}>₹{item.total_price}</span>
                </div>
              ))}
              <div className="conf-total">
                <span>Total</span>
                <span>₹{result.total}</span>
              </div>
            </div>

            {/* Delivery Dispatch — auto-filled after confirmation */}
            {result.delivery_requested && !dispatchInfo && (
              <div style={{ marginBottom: 16 }}>
                <div className="conf-delivery">🚚 Home Delivery Requested</div>
                <button
                  className="btn btn-primary"
                  onClick={handleDispatch}
                  disabled={dispatching}
                  style={{ width: '100%', marginTop: 8 }}
                >
                  {dispatching ? (
                    <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Assigning delivery...</>
                  ) : (
                    <>🛵 Dispatch Delivery Now</>
                  )}
                </button>
              </div>
            )}

            {dispatchInfo && (
              <div style={{ textAlign: 'left', marginBottom: 16 }}>
                <div style={{
                  padding: '14px 18px', borderRadius: 'var(--radius-md)',
                  background: 'linear-gradient(135deg, #EFF6FF, #DBEAFE)', marginBottom: 10,
                }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#1E40AF', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>📱 Sent to Customer</div>
                  <div style={{ fontSize: '0.85rem', color: '#1D4ED8', fontWeight: 600, marginBottom: 4 }}>
                    🛵 {dispatchInfo.customer_message?.delivery_person?.name} is on the way!
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#3B82F6' }}>
                    📞 {dispatchInfo.customer_message?.delivery_person?.phone} · {dispatchInfo.customer_message?.delivery_person?.vehicle}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#3B82F6', marginTop: 2 }}>
                    ⏱ ETA: {dispatchInfo.customer_message?.estimated_time}
                  </div>
                  {dispatchInfo.customer_message?.bill_summary && (
                    <pre style={{
                      marginTop: 10, padding: 10, background: 'white', borderRadius: 8,
                      fontSize: '0.68rem', color: '#1E3A8A', whiteSpace: 'pre-wrap', fontFamily: 'ui-monospace, monospace',
                    }}>{dispatchInfo.customer_message.bill_summary}</pre>
                  )}
                </div>
                <div style={{
                  padding: '14px 18px', borderRadius: 'var(--radius-md)',
                  background: 'linear-gradient(135deg, #FEF3C7, #FDE68A)',
                }}>
                  <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#92400E', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>🧾 Sent to Delivery Person</div>
                  <div style={{ fontSize: '0.82rem', color: '#78350F', fontWeight: 500 }}>
                    📍 {dispatchInfo.delivery_person_message?.customer?.name}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#92400E' }}>
                    {dispatchInfo.delivery_person_message?.customer?.address}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#92400E', marginTop: 2 }}>
                    📞 {dispatchInfo.delivery_person_message?.customer?.phone} · 💰 ₹{dispatchInfo.delivery_person_message?.total} (COD)
                  </div>
                  {dispatchInfo.delivery_person_message?.items?.length > 0 && (
                    <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#78350F' }}>
                      {dispatchInfo.delivery_person_message.items.map((it: any, i: number) => (
                        <div key={i}>{it.quantity}× {it.product_name}</div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}

            <button className="btn btn-primary" onClick={() => { setShowConfirmation(false); setDispatchInfo(null); }}>
              Done
            </button>
          </div>
        </div>
      )}

      {/* Drilldown Modals */}
      {drilldown === 'low-stock' && (
        <DrilldownModal title="Low Stock Items" icon="⚠" onClose={() => setDrilldown(null)}>
          {drilldownLoading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading...</div>
          ) : (
            <div className="drilldown-table">
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Brand</th>
                    <th style={{textAlign:'right'}}>Stock</th>
                    <th style={{textAlign:'right'}}>Threshold</th>
                    <th>Status</th>
                    <th style={{textAlign:'right'}}>Restock</th>
                  </tr>
                </thead>
                <tbody>
                  {(drilldownData as any[] || []).map((p: any) => (
                    <tr key={p.id}>
                      <td style={{ fontWeight: 600 }}>{p.name}</td>
                      <td>{p.brand}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700,
                        color: p.status === 'critical' ? '#DC2626' : p.status === 'out' ? '#9CA3AF' : '#D97706'
                      }}>{p.stock}</td>
                      <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>{p.threshold}</td>
                      <td>
                        <span className={`stock-badge ${p.status === 'critical' ? 'critical' : p.status === 'out' ? 'out-of-stock' : 'low-stock'}`}>
                          {p.status === 'critical' ? 'Critical' : p.status === 'out' ? 'Out' : 'Low'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 500, color: 'var(--brand-600)' }}>+{p.suggested_restock}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(!drilldownData || (drilldownData as any[]).length === 0) && (
                <div className="empty-state" style={{ padding: 24 }}>
                  <p>✅ All products are well stocked!</p>
                </div>
              )}
            </div>
          )}
        </DrilldownModal>
      )}

      {drilldown === 'pending-deliveries' && (
        <DrilldownModal title="Pending Deliveries" icon="🚚" onClose={() => setDrilldown(null)}>
          {drilldownLoading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading...</div>
          ) : (
            <div className="drilldown-list">
              {(drilldownData as any[] || []).map((o: any) => (
                <div key={o.order_id} className="drilldown-card">
                  <div className="dd-card-header">
                    <span className="dd-order-id">{o.display_id}</span>
                    <span className="dd-total">₹{o.total}</span>
                  </div>
                  <div className="dd-card-body">
                    <div className="dd-row">
                      <span className="dd-label">👤 Customer</span>
                      <span>{o.customer_name}</span>
                    </div>
                    <div className="dd-row">
                      <span className="dd-label">📞 Phone</span>
                      <span>{o.customer_phone}</span>
                    </div>
                    <div className="dd-row">
                      <span className="dd-label">📍 Address</span>
                      <span>{o.address || 'Not provided'}</span>
                    </div>
                    <div className="dd-row">
                      <span className="dd-label">📦 Items</span>
                      <span>{o.item_count} items</span>
                    </div>
                  </div>
                </div>
              ))}
              {(!drilldownData || (drilldownData as any[]).length === 0) && (
                <div className="empty-state" style={{ padding: 24 }}>
                  <p>✅ No pending deliveries!</p>
                </div>
              )}
            </div>
          )}
        </DrilldownModal>
      )}

      {drilldown === 'revenue' && (
        <DrilldownModal title="Revenue Breakdown" icon="₹" onClose={() => setDrilldown(null)}>
          {drilldownLoading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading...</div>
          ) : (
            <div className="drilldown-revenue">
              <div className="revenue-total-card">
                <div className="rt-label">Total Revenue Today</div>
                <div className="rt-value">₹{(drilldownData as any)?.total_revenue?.toLocaleString('en-IN') ?? 0}</div>
                <div className="rt-count">{(drilldownData as any)?.order_count ?? 0} orders</div>
              </div>
              <table className="data-table compact">
                <thead>
                  <tr>
                    <th>Order</th>
                    <th>Customer</th>
                    <th style={{textAlign:'right'}}>Subtotal</th>
                    <th style={{textAlign:'right'}}>Delivery</th>
                    <th style={{textAlign:'right'}}>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {((drilldownData as any)?.orders || []).map((o: any) => (
                    <tr key={o.order_id}>
                      <td style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--brand-700)' }}>{o.display_id}</td>
                      <td>{o.customer_name}</td>
                      <td style={{ textAlign: 'right' }}>₹{o.subtotal}</td>
                      <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>₹{o.delivery_fee}</td>
                      <td style={{ textAlign: 'right', fontWeight: 700 }}>₹{o.total}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DrilldownModal>
      )}

      {drilldown === 'orders' && (
        <DrilldownModal title="Today's Orders" icon="📦" onClose={() => setDrilldown(null)}>
          {drilldownLoading ? (
            <div className="loading-overlay"><div className="spinner" /> Loading...</div>
          ) : (
            <div className="drilldown-list">
              {(drilldownData as any[] || []).map((o: any) => (
                <div key={o.id} className="drilldown-card">
                  <div className="dd-card-header">
                    <span className="dd-order-id">KF-{1000 + o.id}</span>
                    <span className={`stock-badge in-stock`} style={{ textTransform: 'capitalize' }}>{o.status}</span>
                  </div>
                  <div className="dd-card-body">
                    <div className="dd-row">
                      <span className="dd-label">👤 Customer</span>
                      <span>{o.customer_name}</span>
                    </div>
                    <div className="dd-row">
                      <span className="dd-label">📦 Items</span>
                      <span>{o.item_count} items</span>
                    </div>
                    <div className="dd-row">
                      <span className="dd-label">💰 Total</span>
                      <span style={{ fontWeight: 700 }}>₹{o.total}</span>
                    </div>
                  </div>
                </div>
              ))}
              {(!drilldownData || (drilldownData as any[]).length === 0) && (
                <div className="empty-state" style={{ padding: 24 }}>
                  <p>No orders yet today. Process a request to get started!</p>
                </div>
              )}
            </div>
          )}
        </DrilldownModal>
      )}
    </div>
  );
}
