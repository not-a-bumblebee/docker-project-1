# Stage 1: Build / Dependencies
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Runtime Image
FROM node:22-alpine AS runner
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# Run as a non-root system user for security
USER node
EXPOSE 3000
CMD ["node", "server.js"]