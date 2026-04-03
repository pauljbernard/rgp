import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: ["@rgp/domain", "@rgp/ui", "@rgp/api-client"]
};

export default nextConfig;
