FROM node:20-alpine AS deps

WORKDIR /app

COPY package*.json ./
RUN npm ci


FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build Nuxt Nitro output.
RUN npm run build


FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000

# Default to backend exposed by your root docker-compose on host port 8000.
# Override with docker run -e NUXT_PUBLIC_API_BASE_URL=... or compose environment.
ENV NUXT_PUBLIC_API_BASE_URL=http://localhost:8000

COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
