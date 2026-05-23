10:39:38.006	Initializing build environment...
10:39:39.671	Success: Finished initializing build environment
10:39:40.225	Cloning repository...
10:39:41.447	Restoring from dependencies cache
10:39:41.450	Restoring from build output cache
10:39:42.341	Detected the following tools from environment: nodejs@22.12.0, npm@10.9.2
10:39:42.342	Installing nodejs 22.12.0
10:39:47.053	Installing project dependencies: npm clean-install --progress=false
10:39:58.085	
10:39:58.086	added 289 packages, and audited 290 packages in 11s
10:39:58.086	
10:39:58.086	143 packages are looking for funding
10:39:58.086	  run `npm fund` for details
10:39:58.087	
10:39:58.087	found 0 vulnerabilities
10:39:58.295	Executing user build command: npm run build
10:39:58.576	
10:39:58.576	> intel-daily-astro@0.0.1 build
10:39:58.576	> astro build
10:39:58.576	
10:40:01.068	(node:1356) [DEP0040] DeprecationWarning: The `punycode` module is deprecated. Please use a userland alternative instead.
10:40:01.069	(Use `node --trace-deprecation ...` to show where the warning was created)
10:40:01.152	02:40:01 [@astrojs/cloudflare] Enabling image processing with Cloudflare Images for production with the "IMAGES" Images binding.
10:40:01.152	02:40:01 [@astrojs/cloudflare] Enabling sessions with Cloudflare KV with the "SESSION" KV binding.
10:40:06.059	02:40:06 [vite]   ➜  Tunnel closed
10:40:06.078	02:40:06 [types] Generated 4.88s
10:40:06.079	02:40:06 [build] output: "static"
10:40:06.079	02:40:06 [build] mode: "server"
10:40:06.079	02:40:06 [build] directory: /opt/buildhome/repo/dist/
10:40:06.080	02:40:06 [build] adapter: @astrojs/cloudflare
10:40:06.080	02:40:06 [build] Collecting build info...
10:40:06.080	02:40:06 [build] ✓ Completed in 4.93s.
10:40:06.080	02:40:06 [build] Building server entrypoints...
10:40:07.682	02:40:07 [vite]   ➜  Tunnel closed
10:40:07.687	02:40:07 [ERROR] [vite] ✗ Build failed in 1.55s
10:40:07.868	src/pages/day/[date].astro (3:27): "TAB_ICONS" is not exported by "src/utils/data.ts", imported by "src/pages/day/[date].astro".
10:40:07.868	file: /opt/buildhome/repo/src/pages/day/[date].astro:3:27
10:40:07.868
10:40:07.868	2: import BaseLayout from '../../layouts/BaseLayout.astro';
10:40:07.868	3: import { TABS, TAB_COLORS, TAB_ICONS, getDayData, getAllDates } from '../../utils/data.ts';
10:40:07.868	                              ^
10:40:07.868	4: 
10:40:07.868	5: export async function getStaticPaths() {
10:40:07.868	
10:40:07.868	  Location:
10:40:07.868	    /opt/buildhome/repo/src/pages/day/[date].astro:3:27
10:40:07.868	  Stack trace:
10:40:07.868	    at getRollupError (file:///opt/buildhome/repo/node_modules/rollup/dist/es/shared/parseAst.js:406:41)
10:40:07.868	    at Module.error (file:///opt/buildhome/repo/node_modules/rollup/dist/es/shared/node-entry.js:17390:16)
10:40:07.868	    at ModuleScope.findVariable (file:///opt/buildhome/repo/node_modules/rollup/dist/es/shared/node-entry.js:15413:39)
10:40:07.869	    at FunctionBodyScope.findVariable (file:///opt/buildhome/repo/node_modules/rollup/dist/es/shared/node-entry.js:5682:38)
10:40:07.869	    at FunctionBodyScope.findVariable (file:///opt/buildhome/repo/node_modules/rollup/dist/es/shared/node-entry.js:5682:38)
10:40:07.869	02:40:07 [vite]   ➜  Tunnel closed
10:40:07.869	02:40:07 [WARN] [vite] Unexpected Node.js imports for environment "prerender". Do you need to enable the "nodejs_compat" compatibility flag? Refer to https://developers.cloudflare.com/workers/runtime-apis/nodejs/ for more details.
10:40:07.869	 - "fs" imported from "src/pages/en/stats.astro"
10:40:07.869	 - "fs" imported from "src/pages/stats.astro"
10:40:07.869	 - "fs" imported from "src/utils/data.ts"
10:40:07.869	 - "path" imported from "src/pages/en/stats.astro"
10:40:07.869	 - "path" imported from "src/utils/data.ts"
10:40:07.869	
10:40:07.930	Failed: error occurred while running build command