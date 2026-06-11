// Document links for buffham imports: Ctrl/Cmd+click an
// `import nlb.buffham.testdata.other;` to open `nlb/buffham/testdata/other.bh`.
// Import namespaces are workspace-root-relative paths with dots as separators.
const vscode = require('vscode');

const IMPORT_REGEX = /^import ([\w.]+);/;

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

// Go-to-definition (Ctrl/Cmd+click, F12) for type and constant references,
// both local (`LogMessage`) and namespaced (`nlb.buffham.testdata.other.Pong`).
class BuffhamDefinitionProvider {
    async provideDefinition(document, position) {
        const range = document.getWordRangeAtPosition(position, /[\w.]+/);
        if (!range) {
            return null;
        }
        const reference = document.getText(range);

        if (!reference.includes('.')) {
            // Local reference; search this file
            const definition = findDefinition(document, reference);
            return definition ? new vscode.Location(document.uri, definition) : null;
        }

        // Namespaced reference: all but the last segment is the file's
        // namespace, the last segment is the symbol. Import statements are
        // purely a namespace, so fall back to the file itself.
        const folder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!folder) {
            return null;
        }
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
            return new vscode.Location(target, definition ?? new vscode.Position(0, 0));
        }
        return null;
    }
}

function activate(context) {
    context.subscriptions.push(
        vscode.languages.registerDocumentLinkProvider(
            { language: 'buffham' },
            new BuffhamLinkProvider()
        ),
        vscode.languages.registerDefinitionProvider(
            { language: 'buffham' },
            new BuffhamDefinitionProvider()
        )
    );
}

module.exports = { activate };
