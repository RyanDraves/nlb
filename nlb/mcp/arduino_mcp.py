import fastmcp
import rich_click as click

from nlb.mcp import arduino


@click.command()
def main():
    mcp = fastmcp.FastMCP(
        'Arduino Server',
    )

    arduino_tools = arduino.ArduinoTool()
    for tool in arduino_tools.tool_functions:
        mcp.add_tool(tool)

    mcp.run(transport='streamable-http', host='127.0.0.1', port=9100)


if __name__ == '__main__':
    main(prog_name='arduino_mcp')
