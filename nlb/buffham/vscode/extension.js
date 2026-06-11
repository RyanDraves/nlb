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

function activate(context) {
    context.subscriptions.push(
        vscode.languages.registerDocumentLinkProvider(
            { language: 'buffham' },
            new BuffhamLinkProvider()
        )
    );
}

module.exports = { activate };
