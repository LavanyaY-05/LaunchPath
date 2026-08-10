import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'LaunchPath — AI Advisor for Early-Stage Entrepreneurship',
  description: 'AI-powered advisory platform for freelancers, startup founders, and small business owners based on strictly grounded domain knowledge.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
