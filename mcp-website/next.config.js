/** @type {import('next').NextConfig} */
const catalog = require('../mcp-backend/functions/config/environment_catalog.json')
const {validatePublicRuntime, publicRuntimeEnvironment} = require('./config/runtime-policy.cjs')
const runtime = validatePublicRuntime(process.env, catalog)
const nextConfig = {
  env: publicRuntimeEnvironment(runtime),
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
