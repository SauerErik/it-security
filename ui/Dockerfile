# ---------- Build stage ----------
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files first (better caching)
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build static assets
RUN npm run build


# ---------- Production stage ----------
FROM nginx:alpine

# Remove default nginx files
RUN rm -rf /usr/share/nginx/html/*

# Copy build output
COPY --from=build /app/dist /usr/share/nginx/html

# Expose nginx port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
