import { describe, expect, it } from "vitest";

const sourceFiles = import.meta.glob("../src/**/*.{ts,tsx}", {
  eager: true,
  import: "default",
  query: "?raw",
}) as Record<string, string>;

describe("web API boundary", () => {
  it("uses only the versioned API and contains no persistence access", () => {
    const sources = Object.values(sourceFiles);
    const transferClient = Object.entries(sourceFiles).find(([path]) =>
      path.endsWith("/lib/api/transfers.ts"),
    )?.[1];

    expect(transferClient).toContain('fetch("/api/v1/transfers"');
    expect(sources.join("\n")).not.toMatch(/fetch\(\s*["']\/(?!api\/v1)/);
    expect(sources.join("\n")).not.toMatch(/sqlalchemy|psycopg|postgres|DATABASE_URL/i);
  });
});