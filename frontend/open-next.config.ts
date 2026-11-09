// OpenNext adapter config for Cloudflare Workers.
// The app is a single static page that talks to the API from the browser, so no
// incremental cache (R2/KV) is needed.
import { defineCloudflareConfig } from "@opennextjs/cloudflare";

export default defineCloudflareConfig({});
