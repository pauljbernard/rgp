import path from "path";
import { defineConfig } from "vitest/config";

const jsonReportPath = process.env.VITEST_JSON_REPORT;

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
    reporters: jsonReportPath ? ["default", "json"] : ["default"],
    outputFile: jsonReportPath ? { json: jsonReportPath } : undefined,
    include: ["app/**/*.test.ts", "app/**/*.test.tsx", "components/**/*.test.ts", "components/**/*.test.tsx", "lib/**/*.test.ts"],
    exclude: ["e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text-summary", "json-summary"],
      reportsDirectory: "../../coverage/web",
      include: ["app/**/page.tsx", "components/**/*.ts", "components/**/*.tsx", "lib/**/*.ts"],
      exclude: ["app/**/*.test.ts", "app/**/*.test.tsx", "components/**/*.test.ts", "components/**/*.test.tsx", "lib/**/*.test.ts", "e2e/**"]
    }
  }
});
