/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // exceljs è usato solo lato client — escluso dal bundle server
  serverExternalPackages: ["exceljs"],

  // 🔴 Rimuovi "standalone" per funzionare con Firebase Hosting SSR
  // output: "standalone",

  images: {
    unoptimized: true, // utile su Firebase se non usi l’Image Optimization
    domains: ["firebasestorage.googleapis.com"],
  },

  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        stream: false,
      }
    }
    return config
  },
};

module.exports = nextConfig;
