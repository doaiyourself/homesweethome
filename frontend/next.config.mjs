/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "**.naver.net" },
      { protocol: "https", hostname: "**.naver.com" },
      { protocol: "https", hostname: "**.pstatic.net" },
    ],
  },
};

export default nextConfig;
