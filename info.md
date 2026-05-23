10:59:23.978	Initializing build environment...
10:59:25.775	Success: Finished initializing build environment
10:59:26.363	Cloning repository...
10:59:27.613	Restoring from dependencies cache
10:59:27.616	Restoring from build output cache
10:59:29.204	Detected the following tools from environment: nodejs@22.12.0, npm@10.9.2
10:59:29.205	Installing nodejs 22.12.0
10:59:33.525	Installing project dependencies: npm clean-install --progress=false
10:59:45.035	
10:59:45.035	added 289 packages, and audited 290 packages in 11s
10:59:45.036	
10:59:45.036	143 packages are looking for funding
10:59:45.036	  run `npm fund` for details
10:59:45.036	
10:59:45.037	found 0 vulnerabilities
10:59:45.209	Executing user build command: npm run build
10:59:45.475	
10:59:45.475	> intel-daily-astro@0.0.1 build
10:59:45.475	> astro build
10:59:45.475	
10:59:47.817	(node:1360) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
10:59:47.817	(Use `node --trace-deprecation ...` to show where the warning was created)
10:59:47.878	02:59:47 [@astrojs/cloudflare] Enabling image processing with Cloudflare Images for production with the "IMAGES" Images binding.
10:59:47.882	02:59:47 [@astrojs/cloudflare] Enabling sessions with Cloudflare KV with the "SESSION" KV binding.
10:59:52.916	02:59:52 [vite]   ➜  Tunnel closed
10:59:52.933	02:59:52 [types] Generated 5.02s
10:59:52.934	02:59:52 [build] output: "static"
10:59:52.934	02:59:52 [build] mode: "server"
10:59:52.934	02:59:52 [build] directory: /opt/buildhome/repo/dist/
10:59:52.934	02:59:52 [build] adapter: @astrojs/cloudflare
10:59:52.934	02:59:52 [build] Collecting build info...
10:59:52.934	02:59:52 [build] ✓ Completed in 5.06s.
10:59:52.935	02:59:52 [build] Building server entrypoints...
10:59:54.968	02:59:54 [vite]   ➜  Tunnel closed
10:59:55.112	02:59:55 [WARN] [vite] Unexpected Node.js imports for environment "prerender". Do you need to enable the "nodejs_compat" compatibility flag? Refer to https://developers.cloudflare.com/workers/runtime-apis/nodejs/ for more details.
10:59:55.113	 - "fs" imported from "src/pages/stats.astro"
10:59:55.113	 - "fs" imported from "src/pages/en/stats.astro"
10:59:55.113	 - "fs" imported from "src/utils/data.ts"
10:59:55.113	 - "path" imported from "src/pages/stats.astro"
10:59:55.114	 - "path" imported from "src/pages/en/stats.astro"
10:59:55.114	 - "path" imported from "src/utils/data.ts"
10:59:55.114	
10:59:55.212	02:59:55 [vite] ✓ built in 2.23s
10:59:56.611	02:59:56 [vite]   ➜  Tunnel closed
10:59:56.753	02:59:56 [vite] ✓ built in 1.54s
10:59:56.775	02:59:56 [vite]   ➜  Tunnel closed
10:59:56.785	02:59:56 [vite] ✓ built in 33ms
10:59:56.807	Default inspector port 9229 not available, using 9230 instead
10:59:56.807	
10:59:56.823	
10:59:56.823	 prerendering static routes 
10:59:57.118	02:59:57 [vite]   ➜  Tunnel closed
10:59:57.327	Failed to get static paths from the Cloudflare prerender server (500: Internal Server Error).
10:59:57.327	Error: No such module "dist/server/.prerender/chunks/fs".
10:59:57.327	  imported from "dist/server/.prerender/chunks/data_Cd7pagTw.mjs"
10:59:57.328	    at async Object.fetch (file:///opt/buildhome/repo/node_modules/miniflare/dist/src/workers/core/entry.worker.js:4672:22)
10:59:57.328	  Location:
10:59:57.330	    /opt/buildhome/repo/node_modules/miniflare/dist/src/workers/core/entry.worker.js:4672:22
10:59:57.330	  Stack trace:
10:59:57.330	    at async Object.fetch (file:///opt/buildhome/repo/node_modules/miniflare/dist/src/workers/core/entry.worker.js:4672:22)
10:59:57.330	    at process.processTicksAndRejections (node:internal/process/task_queues:105:5)
10:59:57.330	    at async BasicMinimalPluginContext.handler (file:///opt/buildhome/repo/node_modules/astro/dist/core/build/static-build.js:121:11)
10:59:57.330	    at async buildEnvironments (file:///opt/buildhome/repo/node_modules/astro/dist/core/build/static-build.js:194:3)
10:59:57.330	    at async AstroBuilder.build (file:///opt/buildhome/repo/node_modules/astro/dist/core/build/index.js:157:5)
10:59:57.330	    at async build (file:///opt/buildhome/repo/node_modules/astro/dist/core/build/index.js:48:3)
10:59:57.331	02:59:57 [vite]   ➜  Tunnel closed
10:59:57.896	Failed: error occurred while running build command