// KiranaFlow AI - Sidebar Navigation Component

import { useLocation, useNavigate } from 'react-router-dom';

const navItems = [
  { path: '/', label: 'Overview', icon: '📊' },
  { path: '/orders', label: 'Orders', icon: '📦' },
  { path: '/inventory', label: 'Inventory', icon: '🏪' },
  { path: '/customers', label: 'Customers', icon: '👥' },
  { path: '/activity', label: 'Agent Activity', icon: '🤖' },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <>
      {isOpen && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)',
            zIndex: 99, display: 'none',
          }}
          className="mobile-overlay"
          onClick={onClose}
        />
      )}
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <h1>
            <span className="brand-icon">K</span>
            KiranaFlow AI
          </h1>
          <div className="tagline">Boliye kya chahiye, baaki KiranaFlow sambhale.</div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <button
              key={item.path}
              className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => { navigate(item.path); onClose(); }}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: '0.68rem', color: 'var(--text-tertiary)', marginTop: '2px' }}>
            KiranaFlow v1.0
          </div>
        </div>
      </aside>
    </>
  );
}
