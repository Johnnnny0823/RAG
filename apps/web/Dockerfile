FROM node:22-bookworm-slim AS source
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

FROM source AS build
RUN npm run build

FROM nginx:1.30-alpine AS deploy
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

FROM source AS development
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--strictPort"]
