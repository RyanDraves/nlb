import { defineConfig } from 'vitest/config';

// extension.js requires the `vscode` module that only exists inside VSCode.
// The tests load extension.js natively (createRequire) with NODE_PATH set to
// test/modules (see BUILD), where a stub `vscode` module lives.
export default defineConfig({
    test: {
        include: ['test/**/*.test.js'],
    },
});
