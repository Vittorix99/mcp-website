/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // 🔴 Rimuovi "standalone" per funzionare con Firebase Hosting SSR
  // output: "standalone",

  images: {
    unoptimized: true, // utile su Firebase se non usi l’Image Optimization
    domains: ["firebasestorage.googleapis.com"],
  },
};

module.exports = nextConfig;