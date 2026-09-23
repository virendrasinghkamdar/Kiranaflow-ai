// KiranaFlow AI - Inventory Page with Fuzzy Search
// Innovation: Client-side fuzzy matching + visual search indicators

import { useState, useEffect, useMemo } from 'react';
import { getProducts, getProductCategories } from '../services/api';
import type { Product } from '../types';

// Fuzzy matching function - handles misspelled product names
function fuzzyMatch(query: string, text: string): { match: boolean; score: number } {
  const q = query.toLowerCase().trim();
  const t = text.toLowerCase();
  
  if (!q) return { match: true, score: 1 };
  if (t.includes(q)) return { match: true, score: 1 };
  
  // Levenshtein distance for similarity
  const distance = levenshtein(q, t.substring(0, Math.max(q.length + 2, t.length)));
  const maxLen = Math.max(q.length, t.length);
  const similarity = 1 - (distance / maxLen);
  
  // Check individual words
  const queryWords = q.split(/\s+/);
  const textWords = t.split(/\s+/);
  let wordMatchScore = 0;
  
  for (const qw of queryWords) {
    let bestWordScore = 0;
    for (const tw of textWords) {
      if (tw.includes(qw) || qw.includes(tw)) {
        bestWordScore = Math.max(bestWordScore, 0.9);
      } else {
        const d = levenshtein(qw, tw);
        const s = 1 - (d / Math.max(qw.length, tw.length));
        bestWordScore = Math.max(bestWordScore, s);
      }
    }
    wordMatchScore += bestWordScore;
  }
  wordMatchScore = wordMatchScore / queryWords.length;
  
  const finalScore = Math.max(similarity, wordMatchScore);
  return { match: finalScore >= 0.45, score: finalScore };
}

function levenshtein(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)
      );
    }
  }
  return dp[m][n];
}

export default function Inventory() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await getProducts(selectedCategory || undefined) as Product[];
      setProducts(data);
    } catch { /* */ }
    setLoading(false);
  };

  useEffect(() => {
    getProductCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => { fetchProducts(); }, [selectedCategory]);

  // Fuzzy search results
  const filteredProducts = useMemo(() => {
    if (!searchQuery.trim()) return products.map(p => ({ product: p, score: 1, isExact: true }));
    
    return products
      .map(p => {
        // Search across name, brand, category, aliases
        const nameMatch = fuzzyMatch(searchQuery, p.name);
        const brandMatch = fuzzyMatch(searchQuery, p.brand);
        const categoryMatch = fuzzyMatch(searchQuery, p.category);
        const aliasMatches = (p.aliases || []).map(a => fuzzyMatch(searchQuery, a));
        
        const bestAliasScore = aliasMatches.length > 0
          ? Math.max(...aliasMatches.map(m => m.score))
          : 0;
        
        const bestScore = Math.max(nameMatch.score, brandMatch.score, categoryMatch.score, bestAliasScore);
        const isExact = p.name.toLowerCase().includes(searchQuery.toLowerCase());
        
        return { product: p, score: bestScore, isExact };
      })
      .filter(r => r.score >= 0.45)
      .sort((a, b) => b.score - a.score);
  }, [products, searchQuery]);

  const getStockStatus = (p: Product) => {
    if (p.stock === 0) return { label: 'Out of Stock', cls: 'out-of-stock' };
    if (p.stock <= 2) return { label: 'Critical', cls: 'critical' };
    if (p.stock <= p.low_stock_threshold) return { label: 'Low Stock', cls: 'low-stock' };
    return { label: 'In Stock', cls: 'in-stock' };
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <div>
          <h1>Inventory</h1>
          <p className="page-subtitle">
            {products.length} products · CP / SP on every SKU
          </p>
        </div>
      </div>

      <div className="filter-bar">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products (handles misspellings too!)..."
          />
        </div>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <button className="btn btn-secondary btn-sm" onClick={fetchProducts}>
          ↻ Refresh
        </button>
      </div>

      {/* Search Results Info */}
      {searchQuery.trim() && (
        <div style={{
          padding: '10px 16px', marginBottom: '12px',
          background: 'var(--brand-50)', borderRadius: 'var(--radius-sm)',
          fontSize: '0.82rem', color: 'var(--brand-700)',
          display: 'flex', alignItems: 'center', gap: '8px',
        }}>
          🔍 Found <strong>{filteredProducts.length}</strong> results for "{searchQuery}"
          {filteredProducts.some(r => !r.isExact) && (
            <span style={{ fontSize: '0.72rem', color: 'var(--brand-600)' }}>
              (including fuzzy matches)
            </span>
          )}
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="loading-overlay">
            <div className="spinner" /> Loading inventory...
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Brand</th>
                <th>Unit</th>
                <th style={{ textAlign: 'right' }}>CP</th>
                <th style={{ textAlign: 'right' }}>SP</th>
                <th style={{ textAlign: 'right' }}>Margin</th>
                <th style={{ textAlign: 'right' }}>Stock</th>
                <th style={{ textAlign: 'right' }}>Threshold</th>
                <th>Status</th>
                {searchQuery.trim() && <th>Match</th>}
              </tr>
            </thead>
            <tbody>
              {filteredProducts.map(({ product: p, score, isExact }) => {
                const status = getStockStatus(p);
                return (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                      {p.name}
                    </td>
                    <td>{p.category}</td>
                    <td>{p.brand}</td>
                    <td>{p.unit}</td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>₹{p.cost_price ?? 0}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>₹{p.price}</td>
                    <td style={{ textAlign: 'right', color: 'var(--brand-700)', fontWeight: 600 }}>
                      {p.price ? Math.round((((p.price - (p.cost_price || 0)) / p.price) * 100)) : 0}%
                    </td>
                    <td style={{
                      textAlign: 'right', fontWeight: 700,
                      color: status.cls === 'in-stock' ? 'var(--text-primary)' :
                        status.cls === 'low-stock' ? '#B45309' :
                          status.cls === 'critical' ? '#B91C1C' : 'var(--text-tertiary)',
                    }}>
                      {p.stock}
                    </td>
                    <td style={{ textAlign: 'right', color: 'var(--text-tertiary)' }}>
                      {p.low_stock_threshold}
                    </td>
                    <td>
                      <span className={`stock-badge ${status.cls}`}>
                        {status.label}
                      </span>
                    </td>
                    {searchQuery.trim() && (
                      <td>
                        <span className="search-match">
                          {isExact ? '✓ Exact' : `~${Math.round(score * 100)}%`}
                        </span>
                      </td>
                    )}
                  </tr>
                );
              })}
              {filteredProducts.length === 0 && (
                <tr>
                  <td colSpan={searchQuery.trim() ? 11 : 10} style={{ textAlign: 'center', padding: '32px' }}>
                    <div className="empty-state" style={{ padding: '16px' }}>
                      <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🔍</div>
                      <h3>No products found</h3>
                      <p>Try a different spelling or search term.</p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
      {!loading && products.length > 0 && (
        <div className="pnl-foot" style={{ marginTop: 12 }}>
          Stock at cost ₹{products.reduce((s, p) => s + (p.cost_price || 0) * p.stock, 0).toLocaleString('en-IN')}
          <span>·</span>
          Unsold margin ₹{products.reduce((s, p) => s + (p.price - (p.cost_price || 0)) * p.stock, 0).toLocaleString('en-IN')}
        </div>
      )}
    </div>
  );
}
