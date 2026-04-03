declare module "next/headers" {
  export function cookies(): Promise<{
    get(name: string): { value: string } | undefined;
  }>;
}
