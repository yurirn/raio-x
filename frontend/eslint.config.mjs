import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const config = defineConfig([
  ...nextVitals,
  ...nextTypeScript,
  {
    rules: {
      "react-hooks/set-state-in-effect": "off",
      "@next/next/no-location-assign-relative-destination": "off",
    },
  },
  globalIgnores([".next/**", "node_modules/**", "next-env.d.ts"]),
]);

export default config;
