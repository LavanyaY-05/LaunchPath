/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    // During local development, proxy /api/backend to the local backend server.
    // In production (Vercel), routing is handled by vercel.json and the platform
    // will route /api/backend to the backend service — avoid rewriting to localhost there.
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/backend/:path*',
          destination: 'http://localhost:8000/:path*',
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
