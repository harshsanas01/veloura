# This Dockerfile runs the Vite dev server for local docker-compose usage.
# Production deploys go through Vercel (see docs/deployment.md), not this image.
FROM node:20-slim

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install

COPY apps/web ./

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
