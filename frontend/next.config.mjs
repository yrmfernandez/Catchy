/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output (own minimal node_modules + server.js) keeps the Docker
  // image small. Vercel produces its own build output and doesn't want this, so
  // it's enabled only for container builds — the Dockerfile sets DOCKER_BUILD=1.
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" } : {}),
};

export default nextConfig;
