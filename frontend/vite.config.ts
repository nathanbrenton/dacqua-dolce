// DD_LOCAL_PREVIEW_TS_TYPING_FIX: scoped node-type workaround
// @ts-ignore -- Offline dev preview; @types/node is not declared in this frontend.
import { createReadStream, existsSync } from "node:fs";
// @ts-ignore -- Offline dev preview; @types/node is not declared in this frontend.
import { homedir } from "node:os";
// @ts-ignore -- Offline dev preview; @types/node is not declared in this frontend.
import { join } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "dacqua-local-product-imagery-preview",
      apply: "serve",
      configureServer(server) {
                        // DD_ORIGIN_PREVIEW_BEGIN — local Vite only, not public production assets.
            server.middlewares.use((req, res, next) => {
                const requestPath = ((req as unknown as { url?: string }).url ?? "").split("?")[0];
                const selected = /^\/__dd_image_preview\/origin\/(DD(?:5RO|6ROAE)-(?:hero|dimensions|filter)|storage-tank|DD6ROAE-alkaline-detail)\.png$/.exec(requestPath);
                if (!selected) return next();
                if (((req as unknown as { method?: string }).method) !== "GET" && ((req as unknown as { method?: string }).method) !== "HEAD") { res.statusCode = 405; res.end(); return; }
                const file = join(homedir(), "Desktop", "dacqua-dolce-imagery-preview", "origin", `${selected[1]}.png`);
                if (!existsSync(file)) { res.statusCode = 404; res.end(); return; }
                res.setHeader("Content-Type", "image/png");
                res.setHeader("Cache-Control", "no-store");
                if (((req as unknown as { method?: string }).method) === "HEAD") { res.statusCode = 200; res.end(); return; }
                const stream = createReadStream(file);
                stream.on("error", () => { if (!res.headersSent) res.statusCode = 500; res.end(); });
                stream.pipe(res);
            });
            // DD_ORIGIN_PREVIEW_END

            // DD_REFINE_PREVIEW_BEGIN — local Vite serve ONLY; intentionally not in public media.
            server.middlewares.use((req, res, next) => {
                const requestPath = ((req as unknown as { url?: string }).url ?? "").split("?")[0];
                const match = /^\/__dd_image_preview\/refine\/(DD(?:15|20)SOFT-(?:bare|jacket|dimensions)|brine-tank|neoprene-jacket-20-folded)\.png$/.exec(requestPath);
                if (!match) return next();
                if (((req as unknown as { method?: string }).method) !== "GET" && ((req as unknown as { method?: string }).method) !== "HEAD") { res.statusCode = 405; res.end(); return; }
                const file = join(homedir(), "Desktop", "dacqua-dolce-imagery-preview", "refine", `${match[1]}.png`);
                if (!existsSync(file)) { res.statusCode = 404; res.end(); return; }
                res.setHeader("Content-Type", "image/png");
                res.setHeader("Cache-Control", "no-store");
                if (((req as unknown as { method?: string }).method) === "HEAD") { res.statusCode = 200; res.end(); return; }
                const stream = createReadStream(file);
                stream.on("error", () => { if (!res.headersSent) res.statusCode = 500; res.end(); });
                stream.pipe(res);
            });
            // DD_REFINE_PREVIEW_END

            // DD_ESSENCE_PREVIEW_BEGIN
            server.middlewares.use((req, res, next) => {
                const requestPath = ((req as unknown as { url?: string }).url ?? "").split("?")[0];
                const match = /^\/__dd_image_preview\/essence\/(DD(?:15|20)CATRV-(?:bare|jacket|dimensions))\.png$/.exec(requestPath);
                if (!match) return next();
                if ((req as unknown as { method?: string }).method !== "GET" && (req as unknown as { method?: string }).method !== "HEAD") {
                    res.statusCode = 405; res.end(); return;
                }
                const file = join(homedir(), "Desktop", "dacqua-dolce-imagery-preview", "essence", `${match[1]}.png`);
                if (!existsSync(file)) { res.statusCode = 404; res.end(); return; }
                res.setHeader("Content-Type", "image/png");
                res.setHeader("Cache-Control", "no-store");
                if ((req as unknown as { method?: string }).method === "HEAD") { res.statusCode = 200; res.end(); return; }
                const stream = createReadStream(file);
                stream.on("error", () => { if (!res.headersSent) res.statusCode = 500; res.end(); });
                stream.pipe(res);
            });
            // DD_ESSENCE_PREVIEW_END

            // PT53: Fittings live in public/__dd_image_preview/clack/; Vite serves them directly.


        const dir = join(homedir(), "Desktop", "dacqua-dolce-imagery-preview", "harmony");
        server.middlewares.use((req, res, next) => {
          const path = ((req as unknown as { url?: string }).url ?? "").split("?")[0];
          const match = /^\/__dd_image_preview\/(DD15CLEAR(?:PTV|PL[123]))(-(hero|frame))?\.png$/.exec(path);
          const shared = /^\/__dd_image_preview\/shared\/(neoprene-jacket-15-(?:folded|installed-harmony))\.png$/.exec(path);
          if (!match && !shared) return next();
          if ((req as unknown as { method?: string }).method !== "GET" && (req as unknown as { method?: string }).method !== "HEAD") {
            res.statusCode = 405;
            res.end();
            return;
          }
          const file = match
            ? join(dir, `${match[1]}${match[2] ?? ""}.png`)
            : join(homedir(), "Desktop", "dacqua-dolce-imagery-preview", "shared", `${shared![1]}.png`);
          if (!existsSync(file)) {
            res.statusCode = 404;
            res.end();
            return;
          }
          res.setHeader("Content-Type", "image/png");
          res.setHeader("Cache-Control", "no-store");
          if ((req as unknown as { method?: string }).method === "HEAD") {
            res.statusCode = 200;
            res.end();
            return;
          }
          const stream = createReadStream(file);
          stream.on("error", () => {
            if (!res.headersSent) res.statusCode = 500;
            res.end();
          });
          stream.pipe(res);
        });
      },
    },
  ],

  server: {
    host: "127.0.0.1",
    port: 15173,

    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false
      },

      "/health": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false
      },

      "/readiness": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false
      }
    }
  }
});
