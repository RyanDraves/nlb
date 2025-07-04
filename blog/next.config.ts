import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Enable static exports for the App Router.
   *
   * @see https://nextjs.org/docs/app/building-your-application/deploying/static-exports
   */
  output: "export",

  /**
   * Set base path. This is usually the slug of your repository.
   *
   * @see https://nextjs.org/docs/app/api-reference/next-config-js/basePath
   */
  basePath: "/",

  /**
   * Disable server-based image optimization. Next.js does not support
   * dynamic features with static exports.
   *
   * @see https://nextjs.org/docs/pages/api-reference/components/image#unoptimized
   */
  images: {
    unoptimized: true,
  },

  // TODO: don't steamroll through typescript errors
  typescript: {
    ignoreBuildErrors: true,
  },

  webpack(config, { isServer, dev, webpack }) {
    config.experiments = {
      asyncWebAssembly: true,
      layers: true,
    };

    // https://github.com/vercel/next.js/issues/64792#issuecomment-2148766770
    if (!isServer) {
      config.output.environment = { ...config.output.environment, asyncFunction: true };
    }

    // Slapped https://github.com/vercel/next.js/issues/29362#issuecomment-971377869
    // onto https://github.com/vercel/next.js/issues/25852
    if (!dev && isServer) {
      config.output.webassemblyModuleFilename = "chunks/[id].wasm";
      config.plugins.push(new WasmChunksFixPlugin());
    }

    return config;
  },

  pageExtensions: ['jsx', 'js', 'ts', 'tsx', 'md', 'mdx'],

  reactStrictMode: true,

  // TODO: didn't work, was in the examples at
  // https://github.com/bazelbuild/examples
  // swcMinify: true,
};

class WasmChunksFixPlugin {
  apply(compiler) {
    compiler.hooks.thisCompilation.tap("WasmChunksFixPlugin", (compilation) => {
      compilation.hooks.processAssets.tap(
        { name: "WasmChunksFixPlugin" },
        (assets) =>
          Object.entries(assets).forEach(([pathname, source]) => {
            if (!pathname.match(/\.wasm$/)) return;
            compilation.deleteAsset(pathname);

            const name = pathname.split("/")[1];
            const info = compilation.assetsInfo.get(pathname);
            compilation.emitAsset(name, source, info);
          })
      );
    });
  }
}

const withMdx = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
  },
})

export default withMdx(nextConfig);
