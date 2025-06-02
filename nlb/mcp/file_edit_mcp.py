import fastmcp
import rich_click as click

from nlb.mcp import file_edit


@click.command()
def main():
    mcp = fastmcp.FastMCP(
        'File Edit Server',
    )

    file_edit_tools = file_edit.FileEditTool()
    for tool in file_edit_tools.tool_functions:
        mcp.add_tool(tool)

    mcp.run(transport='streamable-http', host='127.0.0.1', port=9101)


if __name__ == '__main__':
    main(prog_name='file_edit_mcp')
