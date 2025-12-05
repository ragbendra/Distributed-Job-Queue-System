FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY ./dashboard/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY ./dashboard .

# Build app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config
COPY ./dashboard/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
