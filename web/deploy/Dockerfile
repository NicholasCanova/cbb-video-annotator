# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Install server dependencies
FROM node:20-alpine AS server-build
WORKDIR /server
COPY server/package.json server/package-lock.json ./
RUN npm ci
COPY server/ .
RUN npx tsc
RUN rm -rf node_modules && npm ci --omit=dev

# Stage 3: Production image — Node serves API + static files
FROM node:20-alpine
WORKDIR /app

# Copy server
COPY --from=server-build /server/dist ./dist
COPY --from=server-build /server/node_modules ./node_modules
COPY --from=server-build /server/users.json ./users.json

# Copy frontend build
COPY --from=frontend-build /app/dist ./public

EXPOSE 8080

ENV PORT=8080
ENV NODE_ENV=production

CMD ["node", "dist/index.js"]
