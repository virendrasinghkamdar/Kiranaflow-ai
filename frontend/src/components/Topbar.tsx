// KiranaFlow AI - Top Bar Component

import { useEffect, useState } from 'react';
import { healthCheck } from '../services/api';

interface TopbarProps {
  onToggleSidebar: () => void;
}

export default function Topbar({ onToggleSidebar }: TopbarProps) {
  const [online, setOnline] = useState(false);
  const [aiProvider, setAiProvider] = useState('');

  useEffect(() => {
    healthCheck()
      .then((data: any) => {
        setOnline(data.status === 'online');
        setAiProvider(data.ai_provider || 'mock');
      })
      .catch(() => setOnline(false));
  }, []);

  return (
    <header className="topbar">
      <button className="mobile-toggle" onClick={onToggleSidebar}>☰</button>
      <div style={{ flex: 1 }} />
      <span className={`status-badge ${online ? 'online' : ''}`}>
        <span className="dot" />
        Store {online ? 'Online' : 'Offline'}
      </span>
      <span className={`status-badge ${online ? 'online' : ''}`}>
        <span className="dot" />
        Operator {online ? 'Active' : 'Inactive'}
      </span>
      <div style={{
        width: 32, height: 32, borderRadius: '50%',
        background: 'var(--brand-100)', color: 'var(--brand-700)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '0.8rem', fontWeight: 700,
      }}>
        M
      </div>
    </header>
  );
}
