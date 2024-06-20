// next.config.mjs
export default {
    restricted:true,
    experimental: {
      appDir: true,
    },
    async rewrites() {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:5000/api/:path*',
        },
      ];
    },
  };
  