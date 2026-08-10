'use client';

import React, { useState } from 'react';
import {
  Briefcase,
  Award,
  TrendingUp,
  Store,
  AlertTriangle,
  MapPin,
  FileSpreadsheet,
  ArrowLeft,
  MessageSquare,
  Loader2
} from 'lucide-react';

interface ExploreDomainCard {
  id: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}

interface ExploreTabProps {
  onContinueInChat: (prompt: string) => void;
}

export default function ExploreTab({ onContinueInChat }: ExploreTabProps) {
  const [selectedDomain, setSelectedDomain] = useState<ExploreDomainCard | null>(null);
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState<string>('');
  const [sources, setSources] = useState<string[]>([]);
  const [followUps, setFollowUps] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const cards: ExploreDomainCard[] = [
    {
      id: 'freelancing',
      title: 'Freelancing',
      desc: 'Client acquisition, hourly/project pricing, portfolio optimization & GenAI developer workflows.',
      icon: <Briefcase size={24} />
    },
    {
      id: 'schemes',
      title: 'Startup Schemes',
      desc: 'Government grants, Startup India Seed Fund, DPIIT recognition, SAMRIDH MeitY & Udyam MSME.',
      icon: <Award size={24} />
    },
    {
      id: 'investors',
      title: 'Investors & Funding',
      desc: 'Angel outreach norms, pitch deck standards, VC expectations & private funding alternatives.',
      icon: <TrendingUp size={24} />
    },
    {
      id: 'local_business',
      title: 'Local Business',
      desc: 'Offline & online local marketing, customer retention tactics, bakery & logistics operations.',
      icon: <Store size={24} />
    },
    {
      id: 'failures',
      title: 'Failures & Lessons',
      desc: 'Real postmortems (Laundry startup, Starsky Robotics), smart waste tech & anti-patterns to avoid.',
      icon: <AlertTriangle size={24} />
    },
    {
      id: 'roadmap',
      title: 'Roadmap & Skills',
      desc: 'Structured skill progression for freelance developers, UI designers & GenAI engineers.',
      icon: <MapPin size={24} />
    },
    {
      id: 'pitch_deck',
      title: 'Pitch Deck Essentials',
      desc: 'Core 10-15 slide layout, traction signals, concrete funding ask & investor review norms.',
      icon: <FileSpreadsheet size={24} />
    }
  ];

  const handleCardClick = async (card: ExploreDomainCard) => {
    setSelectedDomain(card);
    setLoading(true);
    setError(null);
    setContent('');

    try {
      const res = await fetch(`${API_BASE}/explore/${card.id}`);
      if (!res.ok) throw new Error("Failed to load domain guide");

      const data = await res.json();
      setContent(data.answer || "No guide available.");
      setSources(data.sources || []);
      setFollowUps(data.follow_ups || []);
    } catch (err: any) {
      setError(err.message || "Failed to fetch domain exploration content.");
    } finally {
      setLoading(false);
    }
  };

  if (selectedDomain) {
    return (
      <div className="explore-detail-container">
        <div className="explore-nav-bar">
          <button className="back-btn" onClick={() => setSelectedDomain(null)}>
            <ArrowLeft size={16} />
            <span>← Back to Explore</span>
          </button>

          <button
            className="continue-chat-btn"
            onClick={() => {
              const prompt = followUps.length > 0 ? followUps[0] : `Tell me more about ${selectedDomain.title}`;
              onContinueInChat(prompt);
            }}
          >
            <MessageSquare size={16} style={{ display: 'inline', marginRight: '6px' }} />
            Continue in Chat
          </button>
        </div>

        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>
          {selectedDomain.title} Guide
        </h1>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
          {selectedDomain.desc}
        </p>

        {sources.length > 0 && (
          <div className="sources-row" style={{ marginBottom: '1.5rem' }}>
            <span className="sources-label">Validated Sources:</span>
            {sources.map((src, idx) => (
              <span key={idx} className="source-badge">{src}</span>
            ))}
          </div>
        )}

        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '3rem 0', color: 'var(--text-secondary)' }}>
            <Loader2 className="animate-spin" size={24} style={{ color: 'var(--accent-blue)' }} />
            <span>Generating structured domain exploration guide...</span>
          </div>
        ) : error ? (
          <div style={{ color: '#ef4444', padding: '2rem 0' }}>{error}</div>
        ) : (
          <div className="explore-content">
            <p style={{ whiteSpace: 'pre-wrap' }}>{content}</p>

            {followUps.length > 0 && (
              <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--border-color)' }}>
                <h3 style={{ fontSize: '1rem', color: 'var(--accent-cyan)', marginBottom: '0.75rem' }}>
                  Recommended Next Questions:
                </h3>
                <div className="prompt-chips-container" style={{ justifyContent: 'flex-start' }}>
                  {followUps.map((chip, idx) => (
                    <button
                      key={idx}
                      className="prompt-chip"
                      onClick={() => onContinueInChat(chip)}
                    >
                      {chip} →
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: '700', marginBottom: '0.35rem' }}>Explore Topic Guides</h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Browse curated, grounded guidance across key entrepreneurial domains.
        </p>
      </div>

      <div className="explore-grid">
        {cards.map((card) => (
          <div key={card.id} className="explore-card" onClick={() => handleCardClick(card)}>
            <div>
              <div className="explore-icon">{card.icon}</div>
              <h3 className="explore-title">{card.title}</h3>
              <p className="explore-desc">{card.desc}</p>
            </div>
            <span style={{ fontSize: '0.825rem', color: 'var(--accent-blue)', marginTop: '1rem', fontWeight: '600', display: 'block' }}>
              View Structured Guide →
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
