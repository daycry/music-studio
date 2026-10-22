FROM node:22.23.2-slim AS base
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /studio
RUN corepack enable

FROM base AS deps
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json
RUN pnpm install --frozen-lockfile --filter web...

FROM base AS build
COPY --from=deps /studio/node_modules /studio/node_modules
COPY --from=deps /studio/apps/web/node_modules /studio/apps/web/node_modules
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web /studio/apps/web
COPY packages/contracts /studio/packages/contracts
RUN pnpm --filter web build

FROM base AS web
ENV NODE_ENV=production
COPY --from=deps /studio/node_modules /studio/node_modules
COPY --from=deps /studio/apps/web/node_modules /studio/apps/web/node_modules
COPY --from=build /studio/apps/web/.next /studio/apps/web/.next
COPY apps/web/package.json /studio/apps/web/package.json
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
EXPOSE 3000
WORKDIR /studio/apps/web
CMD ["pnpm", "start"]
