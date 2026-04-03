import path from "path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: {
    jsx: "automatic"
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, ".")
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["app/**/*.test.ts", "app/**/*.test.tsx", "components/**/*.test.ts", "components/**/*.test.tsx"],
    exclude: ["e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text-summary", "json-summary"],
      reportsDirectory: "../../coverage/web",
      include: ["app/**/page.tsx", "components/**/*.ts", "components/**/*.tsx"],
      exclude: ["app/**/*.test.ts", "app/**/*.test.tsx", "components/**/*.test.ts", "components/**/*.test.tsx", "e2e/**"]
    }
  }
});
