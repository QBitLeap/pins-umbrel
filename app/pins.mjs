import { readFileSync } from "node:fs";

const [command] = process.argv.slice(2);
if (!command || command === "--help") {
  console.log("Usage: pins keygen|address|assign|plan|sign|preflight|broadcast|price [options]");
  process.exit(0);
}

const chain = process.env.QBIT_CHAIN;
if (chain !== "main" && chain !== "testnet4") {
  throw new Error("Open the PINS terminal for Mainnet or Testnet4.");
}
process.argv.push("--network", chain === "main" ? "mainnet" : chain);
if (command === "preflight" || command === "broadcast") {
  const cookie = readFileSync("/auth/.cookie", "utf8").trim();
  const separator = cookie.indexOf(":");
  if (separator <= 0 || separator === cookie.length - 1) throw new Error("Invalid Core RPC cookie.");
  process.argv.push("--rpc", "http://127.0.0.1:18443/",
                    "--rpc-user", cookie.slice(0, separator), "--rpc-password", cookie.slice(separator + 1));
}
await import("/opt/protocol/packages/inscriber/cli.ts");
