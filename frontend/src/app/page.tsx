'use client';

import React, { useState } from 'react';
import Navbar from '@/components/Navbar';
import ChatTab from '@/components/ChatTab';
import ExploreTab from '@/components/ExploreTab';

export default function Home() {
  const [activeTab, setActiveTab] = useState<'chat' | 'explore'>('chat');
  const [initialChatPrompt, setInitialChatPrompt] = useState<string>('');

  const handleContinueInChat = (prompt: string) => {
    setInitialChatPrompt(prompt);
    setActiveTab('chat');
  };

  return (
    <>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="app-container">
        {activeTab === 'chat' ? (
          <ChatTab
            initialPrompt={initialChatPrompt}
            onClearInitialPrompt={() => setInitialChatPrompt('')}
          />
        ) : (
          <ExploreTab onContinueInChat={handleContinueInChat} />
        )}
      </main>
    </>
  );
}
