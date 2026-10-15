FROM node:22-slim AS build

WORKDIR /app

COPY package.json package-lock.json .npmrc ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

FROM node:22-slim

WORKDIR /app

COPY --from=build /app/.output ./.output

ENV HOST=0.0.0.0 \
    PORT=3000

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
