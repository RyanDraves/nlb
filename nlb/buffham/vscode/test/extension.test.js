import { createRequire } from 'module';

import { beforeEach, describe, expect, it } from 'vitest';

// Load natively (not through vite) so extension.js's `require('vscode')`
// resolves to the same stub instance via NODE_PATH (see vitest.config.mjs)
// Resolve 'vscode' exactly like extension.js does (via NODE_PATH) so both see
// the same stub instance
const nativeRequire = createRequire(import.meta.url);
const vscode = nativeRequire('vscode');
const {
    findDefinition,
    resolveReference,
    findReferences,
    collectDefinitions,
    BuffhamLinkProvider,
    BuffhamDocumentSymbolProvider,
    BuffhamHoverProvider,
    BuffhamRenameProvider,
    BuffhamCompletionProvider,
} = nativeRequire('../extension.js');

// Trimmed-down mirrors of nlb/buffham/testdata/{sample,other}.bh
const SAMPLE = `import nlb.buffham.testdata.other;

constant uint8_t my_constant = 4;

# Comment on Verbosity
enum Verbosity {
    LOW = 0;
    HIGH = 1;
}

# A message comment
message LogMessage {
    string message;
    Verbosity verbosity;
}

message NestedMessage {
    optional bool flag;
    LogMessage message;
    list[LogMessage] messages;
    nlb.buffham.testdata.other.Pong other_pong;
}

transaction ping[nlb.buffham.testdata.other.Pong, LogMessage];
publish log_message[LogMessage];
svr_method tick;
`;

const OTHER = `constant uint16_t other_constant = 2;

message Pong {
    uint8_t pong;
}

# An unrelated message that shares a name with sample.bh's
message LogMessage {
    string text;
}
`;

beforeEach(() => {
    vscode.setWorkspaceFiles({
        'nlb/buffham/testdata/sample.bh': SAMPLE,
        'nlb/buffham/testdata/other.bh': OTHER,
    });
});

const openSample = () => vscode.openDocument('nlb/buffham/testdata/sample.bh');

// Position of `text` within `document`, with an offset into the match
function positionOf(document, text, offset = 0) {
    for (let i = 0; i < document.lineCount; i++) {
        const index = document.lineAt(i).text.indexOf(text);
        if (index !== -1) {
            return new vscode.Position(i, index + offset);
        }
    }
    throw new Error(`Not found in document: ${text}`);
}

describe('findDefinition', () => {
    it('finds message, enum, constant, and enum value definitions', () => {
        const document = openSample();
        expect(findDefinition(document, 'LogMessage').line).toBe(
            positionOf(document, 'message LogMessage {').line
        );
        expect(findDefinition(document, 'Verbosity').line).toBe(
            positionOf(document, 'enum Verbosity {').line
        );
        expect(findDefinition(document, 'my_constant').line).toBe(
            positionOf(document, 'constant uint8_t my_constant').line
        );
        expect(findDefinition(document, 'HIGH').line).toBe(
            positionOf(document, 'HIGH = 1;').line
        );
    });

    it('returns null for undefined symbols', () => {
        expect(findDefinition(openSample(), 'Nonexistent')).toBeNull();
    });
});

describe('resolveReference', () => {
    it('resolves local references within the file', async () => {
        const document = openSample();
        const usage = positionOf(document, 'LogMessage message;', 2);
        const resolved = await resolveReference(document, usage);
        expect(resolved.symbol).toBe('LogMessage');
        expect(resolved.document.uri.toString()).toBe(document.uri.toString());
        expect(resolved.position.line).toBe(
            positionOf(document, 'message LogMessage {').line
        );
    });

    it('resolves namespaced references to the defining file', async () => {
        const document = openSample();
        const usage = positionOf(
            document, 'nlb.buffham.testdata.other.Pong other_pong', 2
        );
        const resolved = await resolveReference(document, usage);
        expect(resolved.symbol).toBe('Pong');
        expect(resolved.document.uri.path).toContain('other.bh');
        expect(resolved.position.line).toBe(2); // `message Pong {` in OTHER
    });

    it('falls back to the file start for import namespaces', async () => {
        const document = openSample();
        const usage = positionOf(document, 'nlb.buffham.testdata.other;', 2);
        const resolved = await resolveReference(document, usage);
        expect(resolved.document.uri.path).toContain('other.bh');
        expect(resolved.position.line).toBe(0);
        expect(resolved.symbol).toBeNull();
    });
});

describe('BuffhamLinkProvider', () => {
    it('links imports that resolve to workspace files', async () => {
        const links = await new BuffhamLinkProvider().provideDocumentLinks(
            openSample()
        );
        expect(links).toHaveLength(1);
        expect(links[0].target.path).toContain('nlb/buffham/testdata/other.bh');
        expect(links[0].range.start.line).toBe(0);
    });

    it('does not link imports that do not resolve', async () => {
        vscode.setWorkspaceFiles({
            'a.bh': 'import does.not.exist;\n',
        });
        const links = await new BuffhamLinkProvider().provideDocumentLinks(
            vscode.openDocument('a.bh')
        );
        expect(links).toHaveLength(0);
    });
});

describe('BuffhamDocumentSymbolProvider', () => {
    it('lists all top-level definitions with nested fields', () => {
        const symbols = new BuffhamDocumentSymbolProvider()
            .provideDocumentSymbols(openSample());
        const names = symbols.map((symbol) => symbol.name);
        expect(names).toEqual([
            'my_constant', 'Verbosity', 'LogMessage', 'NestedMessage',
            'ping', 'log_message', 'tick',
        ]);

        const verbosity = symbols.find((symbol) => symbol.name === 'Verbosity');
        expect(verbosity.children.map((child) => child.name)).toEqual(
            ['LOW', 'HIGH']
        );
        const nested = symbols.find((symbol) => symbol.name === 'NestedMessage');
        expect(nested.children.map((child) => child.name)).toEqual(
            ['flag', 'message', 'messages', 'other_pong']
        );
    });
});

describe('BuffhamHoverProvider', () => {
    it('shows the definition block and its leading comments', async () => {
        const document = openSample();
        const usage = positionOf(document, 'Verbosity verbosity;', 2);
        const hover = await new BuffhamHoverProvider().provideHover(
            document, usage
        );
        expect(hover.contents.value).toContain('enum Verbosity {');
        expect(hover.contents.value).toContain('HIGH = 1;');
        expect(hover.contents.value).toContain('Comment on Verbosity');
    });
});

describe('findReferences', () => {
    it('scopes references to the defining namespace', async () => {
        const document = openSample();
        const definition = positionOf(document, 'message LogMessage {', 9);
        const references = await findReferences(document, definition, true);

        expect(references.symbol).toBe('LogMessage');
        // All references live in sample.bh; other.bh's same-named message and
        // its usages must not match
        for (const location of references.locations) {
            expect(location.uri.path).toContain('sample.bh');
        }
        // Declaration + 2 fields + transaction + publish
        expect(references.locations).toHaveLength(5);
    });

    it('finds qualified cross-file references', async () => {
        const other = vscode.openDocument('nlb/buffham/testdata/other.bh');
        const definition = positionOf(other, 'message Pong {', 9);
        const references = await findReferences(other, definition, true);

        const paths = references.locations.map((location) => location.uri.path);
        // Declaration in other.bh + field & transaction usages in sample.bh
        expect(paths.filter((path) => path.includes('other.bh'))).toHaveLength(1);
        expect(paths.filter((path) => path.includes('sample.bh'))).toHaveLength(2);
    });

    it('excludes the declaration when asked', async () => {
        const document = openSample();
        const definition = positionOf(document, 'message LogMessage {', 9);
        const references = await findReferences(document, definition, false);
        expect(references.locations).toHaveLength(4);
    });
});

describe('BuffhamRenameProvider', () => {
    it('renames the definition and all usages', async () => {
        const document = openSample();
        const usage = positionOf(document, 'LogMessage message;', 2);
        const edit = await new BuffhamRenameProvider().provideRenameEdits(
            document, usage, 'LogRecord'
        );
        expect(edit.replacements).toHaveLength(5);
        expect(edit.replacements.every(
            (replacement) => replacement.newText === 'LogRecord'
        )).toBe(true);
    });

    it('rejects invalid names', async () => {
        const document = openSample();
        const usage = positionOf(document, 'LogMessage message;', 2);
        await expect(
            new BuffhamRenameProvider().provideRenameEdits(
                document, usage, 'not a name'
            )
        ).rejects.toThrow('Invalid buffham name');
    });
});

describe('collectDefinitions', () => {
    it('separates types from constants', () => {
        const definitions = collectDefinitions(openSample());
        expect(definitions.types.map((type) => type.name)).toEqual(
            ['Verbosity', 'LogMessage', 'NestedMessage']
        );
        expect(definitions.constants.map((constant) => constant.name)).toEqual(
            ['my_constant']
        );
    });
});

describe('BuffhamCompletionProvider', () => {
    const provider = new BuffhamCompletionProvider();

    // Completion position: end of `linePrefix` appended as a new line
    function completionContext(linePrefix) {
        const document = new (openSample().constructor)(
            openSample().uri, SAMPLE + linePrefix
        );
        return {
            document,
            position: new vscode.Position(
                document.lineCount - 1, linePrefix.length
            ),
        };
    }

    it('suggests local and imported types for fields', async () => {
        const { document, position } = completionContext('    Ver');
        const labels = (await provider.provideCompletionItems(document, position))
            .map((item) => item.label);
        expect(labels).toContain('Verbosity');
        expect(labels).toContain('LogMessage');
        expect(labels).toContain('nlb.buffham.testdata.other.Pong');
        expect(labels).not.toContain('my_constant');
    });

    it('suggests types inside transaction brackets', async () => {
        const { document, position } = completionContext('transaction foo[');
        const labels = (await provider.provideCompletionItems(document, position))
            .map((item) => item.label);
        expect(labels).toContain('LogMessage');
        expect(labels).toContain('nlb.buffham.testdata.other.Pong');
    });

    it('suggests constants inside constant references', async () => {
        const { document, position } = completionContext(
            'constant uint8_t two = 1 + {'
        );
        const labels = (await provider.provideCompletionItems(document, position))
            .map((item) => item.label);
        expect(labels).toContain('my_constant');
        expect(labels).toContain('nlb.buffham.testdata.other.other_constant');
        expect(labels).not.toContain('LogMessage');
    });

    it('suggests workspace namespaces for imports', async () => {
        const { document, position } = completionContext('import ');
        const labels = (await provider.provideCompletionItems(document, position))
            .map((item) => item.label);
        expect(labels).toContain('nlb.buffham.testdata.other');
        expect(labels).toContain('nlb.buffham.testdata.sample');
    });
});
