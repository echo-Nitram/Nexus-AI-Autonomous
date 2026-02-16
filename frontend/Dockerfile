FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (--legacy-peer-deps avoids strict peer dep errors)
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the Next.js app
ENV NEXT_TELEMETRY_DISABLED=1
ENV BACKEND_URL=http://backend:8000
RUN npm run build

# Expose port and run
EXPOSE 3000
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "start"]
