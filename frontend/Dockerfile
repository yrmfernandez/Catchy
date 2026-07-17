# syntax=docker/dockerfile:1
# ------------------------------------------------------------------
# PhishGuard AI frontend image (Next.js standalone output).
# Multi-stage: install → build → tiny runtime with a non-root user.
# ------------------------------------------------------------------
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

FROM node:20-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
RUN useradd --uid 1000 --create-home nextjs
USER nextjs

# Standalone output ships its own minimal node_modules + server.js.
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
