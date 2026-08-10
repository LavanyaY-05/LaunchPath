'use client';

import React from 'react';
import { Compass, MessageSquare, Rocket } from 'lucide-react';

interface NavbarProps {
  activeTab: 'chat' | 'explore';
  setActiveTab: (tab: 'chat' | 'explore') => void;
}

export default function Navbar({ activeTab, setActiveTab }: NavbarProps) {
  return (
    <header className="navbar">
      <div className="brand">
        <div className="brand-icon">
          <Rocket size={20} />
        </div>
        <span>LaunchPath</span>
      </div>

      <nav className="nav-tabs">
        <button
          className={`nav-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={16} />
          <span>Chat</span>
        </button>

        <button
          className={`nav-tab-btn ${activeTab === 'explore' ? 'active' : ''}`}
          onClick={() => setActiveTab('explore')}
        >
          <Compass size={16} />
          <span>Explore</span>
        </button>
      </nav>
    </header>
  );
}
