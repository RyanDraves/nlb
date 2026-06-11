// Language features for buffham files: import links, go-to-definition,
// outline symbols, hovers, and find-all-references.
const vscode = require('vscode');

const IMPORT_REGEX = /^import ([\w.]+);/;
const MESSAGE_START_REGEX = /^message (\w+) {/;
const ENUM_START_REGEX = /^enum (\w+) {/;
const ENUM_VALUE_REGEX = /^\s*(\w+)\s*=\s*\d+;/;
const CONSTANT_REGEX = /^constant \w+ (\w+) =/;
const FIELD_REGEX = /^\s*(?:optional\s+)?[\w.[\]]+\s+(\w+);/;
const TRANSACTION_REGEX = /^transaction (\w+)\[/;
const PUBLISH_REGEX = /^publish (\w+)\[/;
const SVR_METHOD_REGEX = /^svr_method (\w+);/;

// Find the position where `symbol` is defined in `document`: a message, enum,
// enum value, or constant.
function findDefinition(document, symbol) {
    const definitionRegexes = [
        new RegExp(`^message (${symbol}) {`),
        new RegExp(`^enum (${symbol}) {`),
        new RegExp(`^constant \\w+ (${symbol}) =`),
        new RegExp(`^\\s*(${symbol})\\s*=\\s*\\d+;`), // Enum value
    ];
    for (let i = 0; i < document.lineCount; i++) {
        const text = document.lineAt(i).text;
        for (const regex of definitionRegexes) {
            const match = regex.exec(text);
            if (match) {
                return new vscode.Position(i, text.indexOf(match[1]));
            }
        }
    }
    return null;
}

// Resolve a (possibly namespaced) reference at `position` to a document and
// definition position. Local references resolve within `document`; namespaced
// references treat all but the last dotted segment as a workspace-root-relative
// file path. Returns {document, position, symbol} or null.
async function resolveReference(document, position) {
    const range = document.getWordRangeAtPosition(position, /[\w.]+/);
    if (!range) {
        return null;
    }
    const reference = document.getText(range);

    if (!reference.includes('.')) {
        const definition = findDefinition(document, reference);
        return definition
            ? { document: document, position: definition, symbol: reference }
            : null;
    }

    const folder = vscode.workspace.getWorkspaceFolder(document.uri);
    if (!folder) {
        return null;
    }
    // Import statements are purely a namespace, so fall back to the file itself
    const segments = reference.split('.');
    const symbol = segments.pop();
    const candidates = [
        { path: segments.join('/') + '.bh', symbol: symbol },
        { path: reference.replaceAll('.', '/') + '.bh', symbol: null },
    ];
    for (const candidate of candidates) {
        const target = vscode.Uri.joinPath(folder.uri, candidate.path);
        let targetDocument;
        try {
            targetDocument = await vscode.workspace.openTextDocument(target);
        } catch {
            continue;
        }
        const definition = candidate.symbol
            ? findDefinition(targetDocument, candidate.symbol)
            : null;
        return {
            document: targetDocument,
            position: definition ?? new vscode.Position(0, 0),
            symbol: candidate.symbol,
        };
    }
    return null;
}

// Document links for buffham imports: Ctrl/Cmd+click an
// `import nlb.buffham.testdata.other;` to open `nlb/buffham/testdata/other.bh`.
class BuffhamLinkProvider {
    async provideDocumentLinks(document) {
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
            return [];
        }

        const links = [];
        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const match = IMPORT_REGEX.exec(line.text);
            if (!match) {
                continue;
            }
            const namespace = match[1];
            const target = vscode.Uri.joinPath(
                folder.uri,
                namespace.replaceAll('.', '/') + '.bh'
            );
            try {
                await vscode.workspace.fs.stat(target);
            } catch {
                continue; // Don't link imports that don't resolve to a file
            }
            const start = line.text.indexOf(namespace);
            const range = new vscode.Range(i, start, i, start + namespace.length);
            const link = new vscode.DocumentLink(range, target);
            link.tooltip = 'Open buffham file';
            links.push(link);
        }
        return links;
    }
}

// Go-to-definition (Ctrl/Cmd+click, F12) for type and constant references
class BuffhamDefinitionProvider {
    async provideDefinition(document, position) {
        const resolved = await resolveReference(document, position);
        return resolved
            ? new vscode.Location(resolved.document.uri, resolved.position)
            : null;
    }
}

// Outline / breadcrumbs / go-to-symbol (Cmd+Shift+O) support
class BuffhamDocumentSymbolProvider {
    provideDocumentSymbols(document) {
        const symbols = [];
        let container = null; // Open message/enum block, if any

        const lineSymbol = (name, kind, lineIndex, text) => {
            const start = text.indexOf(name);
            const range = document.lineAt(lineIndex).range;
            const selection = new vscode.Range(
                lineIndex, start, lineIndex, start + name.length
            );
            return new vscode.DocumentSymbol(name, '', kind, range, selection);
        };

        for (let i = 0; i < document.lineCount; i++) {
            const text = document.lineAt(i).text;
            let match;
            if ((match = MESSAGE_START_REGEX.exec(text))) {
                container = lineSymbol(match[1], vscode.SymbolKind.Struct, i, text);
                symbols.push(container);
            } else if ((match = ENUM_START_REGEX.exec(text))) {
                container = lineSymbol(match[1], vscode.SymbolKind.Enum, i, text);
                symbols.push(container);
            } else if (/^}/.test(text) && container) {
                container.range = new vscode.Range(
                    container.range.start, document.lineAt(i).range.end
                );
                container = null;
            } else if (container && (match = ENUM_VALUE_REGEX.exec(text))) {
                container.children.push(
                    lineSymbol(match[1], vscode.SymbolKind.EnumMember, i, text)
                );
            } else if (container && (match = FIELD_REGEX.exec(text))) {
                container.children.push(
                    lineSymbol(match[1], vscode.SymbolKind.Field, i, text)
                );
            } else if ((match = CONSTANT_REGEX.exec(text))) {
                symbols.push(lineSymbol(match[1], vscode.SymbolKind.Constant, i, text));
            } else if ((match = TRANSACTION_REGEX.exec(text))) {
                symbols.push(lineSymbol(match[1], vscode.SymbolKind.Method, i, text));
            } else if ((match = PUBLISH_REGEX.exec(text))) {
                symbols.push(lineSymbol(match[1], vscode.SymbolKind.Event, i, text));
            } else if ((match = SVR_METHOD_REGEX.exec(text))) {
                symbols.push(lineSymbol(match[1], vscode.SymbolKind.Method, i, text));
            }
        }
        return symbols;
    }
}

// Hover a reference to see its definition and the `#` comments above it
class BuffhamHoverProvider {
    async provideHover(document, position) {
        const resolved = await resolveReference(document, position);
        if (!resolved || !resolved.symbol) {
            return null;
        }
        const target = resolved.document;
        const definitionLine = resolved.position.line;

        // Collect the comment block immediately above the definition
        const comments = [];
        for (let i = definitionLine - 1; i >= 0; i--) {
            const match = /^\s*#\s?(.*)$/.exec(target.lineAt(i).text);
            if (!match) {
                break;
            }
            comments.unshift(match[1]);
        }

        // Show the full block for messages/enums, otherwise the single line
        const definitionText = target.lineAt(definitionLine).text;
        const lines = [definitionText];
        if (/{\s*$/.test(definitionText)) {
            for (let i = definitionLine + 1; i < target.lineCount; i++) {
                lines.push(target.lineAt(i).text);
                if (/^}/.test(target.lineAt(i).text)) {
                    break;
                }
            }
        }

        const markdown = new vscode.MarkdownString();
        markdown.appendCodeblock(lines.join('\n'), 'buffham');
        if (comments.length > 0) {
            markdown.appendMarkdown('\n' + comments.join('\n'));
        }
        return new vscode.Hover(markdown);
    }
}

// Skip Bazel output trees, tool caches, and other non-source directories when
// scanning the workspace
const FIND_FILES_EXCLUDE =
    '{**/bazel-*/**,**/.claude/**,**/node_modules/**,**/.git/**}';

// Find-all-references (Shift+F12) across the workspace's buffham files.
// References are namespace-aware: a symbol is referenced bare within its
// defining file and as `namespace.path.Symbol` from other files.
class BuffhamReferenceProvider {
    async provideReferences(document, position, context) {
        const resolved = await resolveReference(document, position);
        if (!resolved || !resolved.symbol) {
            return [];
        }
        const symbol = resolved.symbol;
        const definingUri = resolved.document.uri;

        // The defining file's namespace, e.g. `nlb.buffham.testdata.sample`
        const namespace = vscode.workspace
            .asRelativePath(definingUri, false)
            .replace(/\.bh$/, '')
            .replaceAll('/', '.');
        const qualified = `${namespace}.${symbol}`.replaceAll('.', '\\.');
        const qualifiedRegex = new RegExp(`(?<![\\w.])${qualified}\\b`, 'g');
        // Bare references are not preceded by a dot (namespaced tail) or word
        const bareRegex = new RegExp(`(?<![\\w.])${symbol}\\b`, 'g');

        const locations = [];
        const files = await vscode.workspace.findFiles('**/*.bh', FIND_FILES_EXCLUDE);
        for (const file of files) {
            let target;
            try {
                target = await vscode.workspace.openTextDocument(file);
            } catch {
                continue;
            }
            const isDefiningFile = file.toString() === definingUri.toString();
            for (let i = 0; i < target.lineCount; i++) {
                const text = target.lineAt(i).text;
                const matches = [...text.matchAll(qualifiedRegex)].map(
                    // Point at the symbol itself, not the namespace prefix
                    (match) => match.index + match[0].length - symbol.length
                );
                if (isDefiningFile) {
                    if (!context.includeDeclaration && i === resolved.position.line) {
                        continue;
                    }
                    matches.push(
                        ...[...text.matchAll(bareRegex)].map((match) => match.index)
                    );
                }
                for (const start of matches) {
                    locations.push(new vscode.Location(
                        file, new vscode.Range(i, start, i, start + symbol.length)
                    ));
                }
            }
        }
        return locations;
    }
}

function activate(context) {
    const selector = { language: 'buffham' };
    context.subscriptions.push(
        vscode.languages.registerDocumentLinkProvider(
            selector, new BuffhamLinkProvider()
        ),
        vscode.languages.registerDefinitionProvider(
            selector, new BuffhamDefinitionProvider()
        ),
        vscode.languages.registerDocumentSymbolProvider(
            selector, new BuffhamDocumentSymbolProvider()
        ),
        vscode.languages.registerHoverProvider(
            selector, new BuffhamHoverProvider()
        ),
        vscode.languages.registerReferenceProvider(
            selector, new BuffhamReferenceProvider()
        )
    );
}

module.exports = { activate };
