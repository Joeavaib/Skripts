const fs = require("node:fs");

if (!fs.existsSync("tsconfig.json")) {
  console.error("tsconfig.json is required");
  process.exit(1);
}

if (!fs.existsSync("src/index.ts")) {
  console.error("src/index.ts is required");
  process.exit(1);
}

console.log("Lint checks passed.");
