# ---------- Builder Stage ----------
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# ---------- Production Stage ----------
FROM node:20-alpine
WORKDIR /app

# Copy only build artifacts & node_modules from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/postcss.config.mjs ./postcss.config.mjs

# No need to install again
EXPOSE 3000

CMD ["npm", "start"]
