import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async rewrites() {
    // Demo surfaces served as static pages: /ops (exec dashboard), /shop (mechanic board)
    return [
      { source: '/ops', destination: '/ops.html' },
      { source: '/shop', destination: '/shop.html' },
    ];
  },
};

export default nextConfig;
