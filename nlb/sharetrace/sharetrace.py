import datetime
import pathlib
import webbrowser

import jinja2
import pygments
import rich_click as click
from InquirerPy.prompts import confirm as confirm_prompt
from InquirerPy.prompts import list as list_prompt
from pygments import formatters
from pygments import lexers
from pygments import util

from nlb.sharetrace import interface
from nlb.util import console_utils


def _select_exception_file() -> pathlib.Path | None:
    """Prompt user to select an exception file from the cache."""
    cached_files = interface.list_cached_exceptions()

    if not cached_files:
        console_utils.Console().error('No cached exception files found!')
        return None

    # Filter to the 10 most recent files
    cached_files = sorted(cached_files, key=lambda f: f.stat().st_mtime, reverse=True)[
        :10
    ]

    # Create display choices with exception info
    choices = []
    for file_path in cached_files:
        try:
            data = interface.load_exception_data(file_path)
            timestamp = datetime.datetime.fromisoformat(data.timestamp)
            choice_text = f'{timestamp.strftime("%Y-%m-%d %H:%M:%S")} - {data.exception_type}: {data.exception_message[:60]}{"..." if len(data.exception_message) > 60 else ""}'
            choices.append({'name': choice_text, 'value': file_path})
        except Exception as e:
            choices.append(
                {'name': f'{file_path.name} (Error loading: {e})', 'value': file_path}
            )

    selected_file = list_prompt.ListPrompt(
        message='Select exception to visualize:',
        choices=choices,
    ).execute()

    return selected_file


def _get_syntax_highlighted_code(code: str, filename: str) -> str:
    """Get syntax highlighted HTML for code."""
    try:
        # Try to determine lexer from filename
        if filename.endswith('.py'):
            lexer = lexers.get_lexer_by_name('python')
        elif filename.endswith('.js'):
            lexer = lexers.get_lexer_by_name('javascript')
        elif filename.endswith('.ts'):
            lexer = lexers.get_lexer_by_name('typescript')
        elif filename.endswith('.html'):
            lexer = lexers.get_lexer_by_name('html')
        elif filename.endswith('.css'):
            lexer = lexers.get_lexer_by_name('css')
        elif filename.endswith('.json'):
            lexer = lexers.get_lexer_by_name('json')
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            lexer = lexers.get_lexer_by_name('yaml')
        elif filename.endswith('.md'):
            lexer = lexers.get_lexer_by_name('markdown')
        else:
            lexer = lexers.get_lexer_by_name('text')
    except util.ClassNotFound:
        lexer = lexers.get_lexer_by_name('text')

    formatter = formatters.HtmlFormatter(
        style='github-dark',
        linenos=True,
        linenostart=1,
        cssclass='highlight',
        wrapcode=True,
    )

    return pygments.highlight(code, lexer, formatter)


def _generate_html_report(
    exception_data: interface.ExceptionData, output_path: pathlib.Path
) -> None:
    """Generate an HTML report for the exception data."""
    # Get CSS for syntax highlighting
    formatter = formatters.HtmlFormatter(style='github-dark', cssclass='highlight')
    highlight_css = formatter.get_style_defs('.highlight')

    # HTML template
    template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Exception Report: {{ exception_data.exception_type }}</title>
    <style>
        {{ highlight_css }}

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #e6e6e6;
            background-color: #0d1117;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background-color: #21262d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #f85149;
        }

        .exception-title {
            font-size: 2em;
            margin: 0 0 10px 0;
            color: #f85149;
        }

        .exception-message {
            font-size: 1.2em;
            margin: 0;
            color: #ffa657;
        }

        .section {
            background-color: #161b22;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #30363d;
        }

        .section-title {
            font-size: 1.3em;
            margin: 0 0 15px 0;
            color: #58a6ff;
            border-bottom: 2px solid #58a6ff;
            padding-bottom: 5px;
        }

        .stack-frame {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-bottom: 15px;
            overflow: hidden;
        }

        .frame-header {
            background-color: #21262d;
            padding: 10px 15px;
            font-weight: bold;
            color: #f0f6fc;
        }

        .frame-location {
            color: #58a6ff;
        }

        .frame-function {
            color: #79c0ff;
        }

        .code-context {
            padding: 0;
        }

        .highlight {
            margin: 0;
            font-size: 0.9em;
        }

        .highlight pre {
            margin: 0;
            padding: 15px;
            overflow-x: auto;
        }

        .error-line {
            background-color: #490202 !important;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .info-item {
            background-color: #21262d;
            padding: 15px;
            border-radius: 6px;
        }

        .info-label {
            font-weight: bold;
            color: #79c0ff;
            margin-bottom: 5px;
        }

        .info-value {
            color: #e6e6e6;
            word-break: break-all;
        }

        .locals-section {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            margin-top: 10px;
        }

        .locals-header {
            background-color: #21262d;
            padding: 10px 15px;
            font-weight: bold;
            color: #f0f6fc;
            border-bottom: 1px solid #30363d;
        }

        .locals-content {
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }

        .local-var {
            margin-bottom: 8px;
        }

        .var-name {
            color: #79c0ff;
            font-weight: bold;
        }

        .var-value {
            color: #a5a5a5;
            margin-left: 10px;
        }

        .traceback-text {
            background-color: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 15px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            white-space: pre-wrap;
            overflow-x: auto;
            color: #e6e6e6;
        }

        .timestamp {
            color: #7d8590;
            font-size: 0.9em;
        }

        .git-info {
            background-color: #21262d;
            padding: 10px 15px;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 0.9em;
        }

        .git-label {
            color: #79c0ff;
            font-weight: bold;
        }

        .git-value {
            color: #e6e6e6;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="exception-title">{{ exception_data.exception_type }}</h1>
            <p class="exception-message">{{ exception_data.exception_message }}</p>
            <p class="timestamp">Generated on {{ timestamp }} | Exception ID: {{ exception_data.id }}</p>
        </div>

        {% if exception_data.git_info %}
        <div class="section">
            <h2 class="section-title">Repository Information</h2>
            <div class="info-grid">
                {% if exception_data.git_info.repository %}
                <div class="info-item">
                    <div class="info-label">Repository</div>
                    <div class="info-value">{{ exception_data.git_info.repository }}</div>
                </div>
                {% endif %}
                {% if exception_data.git_info.branch %}
                <div class="info-item">
                    <div class="info-label">Branch</div>
                    <div class="info-value">{{ exception_data.git_info.branch }}</div>
                </div>
                {% endif %}
                {% if exception_data.git_info.commit %}
                <div class="info-item">
                    <div class="info-label">Commit</div>
                    <div class="info-value">{{ exception_data.git_info.commit }}</div>
                </div>
                {% endif %}
            </div>
        </div>
        {% endif %}

        <div class="section">
            <h2 class="section-title">Stack Trace</h2>
            {% for frame in exception_data.stack_frames %}
            <div class="stack-frame">
                <div class="frame-header">
                    <span class="frame-location">{{ frame.filename }}:{{ frame.line_number }}</span>
                    in <span class="frame-function">{{ frame.function_name }}()</span>
                </div>

                {% if frame.code_context.lines %}
                <div class="code-context">
                    {% set code_lines = [] %}
                    {% for line in frame.code_context.lines %}
                        {% set _ = code_lines.append(line.content) %}
                    {% endfor %}
                    {{ get_syntax_highlighted_code(code_lines|join('\n'), frame.filename) | safe }}
                </div>
                {% endif %}

                {% if frame.locals %}
                <div class="locals-section">
                    <div class="locals-header">Local Variables</div>
                    <div class="locals-content">
                        {% for var_name, var_value in frame.locals.items() %}
                        <div class="local-var">
                            <span class="var-name">{{ var_name }}:</span>
                            <span class="var-value">{{ var_value }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                {% endif %}
            </div>
            {% endfor %}
        </div>

        <div class="section">
            <h2 class="section-title">System Information</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Platform</div>
                    <div class="info-value">{{ exception_data.system_info.platform }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Python Version</div>
                    <div class="info-value">{{ exception_data.system_info.python_version }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Python Implementation</div>
                    <div class="info-value">{{ exception_data.system_info.python_implementation }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Architecture</div>
                    <div class="info-value">{{ exception_data.system_info.architecture }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Machine</div>
                    <div class="info-value">{{ exception_data.system_info.machine }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">System</div>
                    <div class="info-value">{{ exception_data.system_info.system }}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Full Traceback</h2>
            <div class="traceback-text">{{ exception_data.traceback_text }}</div>
        </div>
    </div>
</body>
</html>
    """

    template = jinja2.Template(template_str)

    # Helper function for the template
    def get_syntax_highlighted_code(code: str, filename: str) -> str:
        return _get_syntax_highlighted_code(code, filename)

    # Generate HTML
    html_content = template.render(
        exception_data=exception_data,
        highlight_css=highlight_css,
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        get_syntax_highlighted_code=get_syntax_highlighted_code,
    )

    # Write to file
    output_path.write_text(html_content, encoding='utf-8')


def _get_output_filename(exception_data: interface.ExceptionData) -> str:
    """Generate a suitable output filename for the exception report."""
    timestamp = datetime.datetime.fromisoformat(exception_data.timestamp)
    # Clean up exception type for use in filename
    safe_exception_type = (
        exception_data.exception_type.replace(':', '_')
        .replace('/', '_')
        .replace(' ', '_')
        .replace('<', '_')
        .replace('>', '_')
    )
    return f'sharetrace_{timestamp.strftime("%Y%m%d_%H%M%S")}_{exception_data.id[:8]}_{safe_exception_type}.html'


@click.command()
@click.option(
    '--open-browser',
    is_flag=True,
    default=False,
    help='Open the generated report in the default browser',
)
def main(open_browser: bool) -> None:
    """Generate shareable HTML reports from cached exception data."""
    console = console_utils.Console()

    # Select exception file
    selected_file = _select_exception_file()
    if not selected_file:
        return

    try:
        # Load exception data
        console.info(f'Loading exception data from {selected_file.name}...')
        exception_data = interface.load_exception_data(selected_file)

        # Get output filename
        output_filename = _get_output_filename(exception_data)
        output_path = interface.TRACE_OUTPUT_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate report
        console.info('Generating HTML report...')
        _generate_html_report(exception_data, output_path)

        console.success(f'Shareable HTML report generated: {output_path}')

        # Open in browser if requested
        if open_browser:
            console.info('Opening report in browser...')
            file_url = output_path.absolute().as_uri()
            webbrowser.open(file_url)
        else:
            # Ask if user wants to open in browser
            should_open = confirm_prompt.ConfirmPrompt(
                message='Open the report in your browser?',
                default=True,
            ).execute()

            if should_open:
                file_url = output_path.absolute().as_uri()
                console.info(f'Opening: {file_url}')
                webbrowser.open(file_url)

    except Exception as e:
        console.error(f'Error generating report: {e}')
        raise click.Abort()


if __name__ == '__main__':
    main(prog_name='sharetrace')
