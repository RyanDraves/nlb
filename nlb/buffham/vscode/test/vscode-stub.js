// Minimal in-memory stub of the `vscode` API surface used by extension.js,
// aliased in via vitest.config.js. Tests register workspace files with
// `setWorkspaceFiles({relativePath: contents})` and open them with
// `openDocument(relativePath)`.

class Position {
    constructor(line, character) {
        this.line = line;
        this.character = character;
    }
}

class Range {
    constructor(...args) {
        if (args.length === 4) {
            this.start = new Position(args[0], args[1]);
            this.end = new Position(args[2], args[3]);
        } else {
            this.start = args[0];
            this.end = args[1];
        }
    }
}

class Location {
    constructor(uri, rangeOrPosition) {
        this.uri = uri;
        this.range = rangeOrPosition;
    }
}

class Uri {
    constructor(path) {
        this.path = path;
        this.fsPath = path;
    }

    toString() {
        return `file://${this.path}`;
    }

    static joinPath(base, ...segments) {
        return new Uri([base.path, ...segments].join('/'));
    }
}

class TextLine {
    constructor(text, lineIndex) {
        this.text = text;
        this.range = new Range(lineIndex, 0, lineIndex, text.length);
    }
}

class TextDocument {
    constructor(uri, contents) {
        this.uri = uri;
        this._lines = contents.split('\n');
        this.lineCount = this._lines.length;
    }

    lineAt(line) {
        return new TextLine(this._lines[line], line);
    }

    getText(range) {
        const text = this._lines[range.start.line];
        return text.slice(range.start.character, range.end.character);
    }

    getWordRangeAtPosition(position, regex = /\w+/) {
        const text = this._lines[position.line];
        const global = new RegExp(regex.source, 'g');
        for (const match of text.matchAll(global)) {
            if (
                match.index <= position.character &&
                position.character <= match.index + match[0].length
            ) {
                return new Range(
                    position.line, match.index,
                    position.line, match.index + match[0].length
                );
            }
        }
        return undefined;
    }
}

class DocumentLink {
    constructor(range, target) {
        this.range = range;
        this.target = target;
    }
}

class DocumentSymbol {
    constructor(name, detail, kind, range, selectionRange) {
        this.name = name;
        this.detail = detail;
        this.kind = kind;
        this.range = range;
        this.selectionRange = selectionRange;
        this.children = [];
    }
}

class CompletionItem {
    constructor(label, kind) {
        this.label = label;
        this.kind = kind;
    }
}

class MarkdownString {
    constructor() {
        this.value = '';
    }

    appendCodeblock(code, language) {
        this.value += `\`\`\`${language}\n${code}\n\`\`\``;
    }

    appendMarkdown(markdown) {
        this.value += markdown;
    }
}

class Hover {
    constructor(contents) {
        this.contents = contents;
    }
}

class WorkspaceEdit {
    constructor() {
        this.replacements = [];
    }

    replace(uri, range, newText) {
        this.replacements.push({ uri, range, newText });
    }
}

const SymbolKind = {
    Struct: 'Struct',
    Enum: 'Enum',
    EnumMember: 'EnumMember',
    Field: 'Field',
    Constant: 'Constant',
    Method: 'Method',
    Event: 'Event',
};

const CompletionItemKind = {
    Struct: 'Struct',
    Enum: 'Enum',
    Constant: 'Constant',
    Module: 'Module',
};

// In-memory workspace state
const WORKSPACE_ROOT = new Uri('/workspace');
let workspaceFiles = {};

function setWorkspaceFiles(files) {
    workspaceFiles = files;
}

function openDocument(relativePath) {
    return new TextDocument(
        Uri.joinPath(WORKSPACE_ROOT, relativePath),
        workspaceFiles[relativePath]
    );
}

function relativePathOf(uri) {
    return uri.path.replace(`${WORKSPACE_ROOT.path}/`, '');
}

const workspace = {
    getWorkspaceFolder: () => ({ uri: WORKSPACE_ROOT }),
    asRelativePath: (uri) => relativePathOf(uri),
    openTextDocument: async (uri) => {
        const relativePath = relativePathOf(uri);
        if (!(relativePath in workspaceFiles)) {
            throw new Error(`No such file: ${relativePath}`);
        }
        return new TextDocument(uri, workspaceFiles[relativePath]);
    },
    findFiles: async () =>
        Object.keys(workspaceFiles)
            .filter((path) => path.endsWith('.bh'))
            .map((path) => Uri.joinPath(WORKSPACE_ROOT, path)),
    fs: {
        stat: async (uri) => {
            const relativePath = relativePathOf(uri);
            if (!(relativePath in workspaceFiles)) {
                throw new Error(`No such file: ${relativePath}`);
            }
            return {};
        },
    },
};

const languages = {
    registerDocumentLinkProvider: () => ({ dispose: () => {} }),
    registerDefinitionProvider: () => ({ dispose: () => {} }),
    registerDocumentSymbolProvider: () => ({ dispose: () => {} }),
    registerHoverProvider: () => ({ dispose: () => {} }),
    registerReferenceProvider: () => ({ dispose: () => {} }),
    registerRenameProvider: () => ({ dispose: () => {} }),
    registerCompletionItemProvider: () => ({ dispose: () => {} }),
};

module.exports = {
    Position,
    Range,
    Location,
    Uri,
    DocumentLink,
    DocumentSymbol,
    CompletionItem,
    CompletionItemKind,
    MarkdownString,
    Hover,
    WorkspaceEdit,
    SymbolKind,
    workspace,
    languages,
    // Test helpers (not part of the vscode API)
    setWorkspaceFiles,
    openDocument,
};
