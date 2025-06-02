import json
from typing import Callable, override

import openai
from InquirerPy.prompts import input as text_input
from openai.types.beta import assistant_stream_event
from openai.types.beta.threads import run
from openai.types.beta.threads import run_submit_tool_outputs_params

from nlb.util import console_utils
from nlb.mcp import tool_manager
from nlb.wizaidry import util


class AssistantEventHandler(openai.AssistantEventHandler):
    def __init__(
        self,
        client: openai.OpenAI,
        console: console_utils.Console,
        *tool_managers: tool_manager.ToolManager,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._client = client
        self._console = console
        self._tool_managers = tool_managers

        self._tool_map: dict[str, Callable[..., str]] = {
            func.__name__: func
            for tool in self._tool_managers
            for func in tool.tool_functions
        }

    @override
    def on_event(self, event: assistant_stream_event.AssistantStreamEvent) -> None:
        # Retrieve events that are denoted with 'requires_action'
        # since these will have our tool_calls
        if event.event == 'thread.run.requires_action':
            run_id = event.data.id  # Retrieve the run ID from the event data
            self.handle_requires_action(event.data, run_id)

    def handle_requires_action(self, data: run.Run, run_id: str) -> None:
        tool_outputs: list[run_submit_tool_outputs_params.ToolOutput] = []

        assert data.required_action is not None
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            if tool.function.name not in self._tool_map:
                tool_outputs.append(
                    {
                        'tool_call_id': tool.id,
                        'output': f'Tool {tool.function.name} not found in tools.',
                    }
                )
                continue

            # Trust that we get good kwargs back; no issues thus far
            kwargs = json.loads(tool.function.arguments)

            self._console.print(
                f'Calling tool {tool.function.name} with args: {tool.function.arguments}'
            )

            # Invoke the tool
            output = self._tool_map[tool.function.name](**kwargs)

            self._console.info(f'Tool output: {output}')

            tool_outputs.append(
                {
                    'tool_call_id': tool.id,
                    'output': output,
                }
            )

        # Submit all tool_outputs at the same time
        self.submit_tool_outputs(tool_outputs, run_id)

    def submit_tool_outputs(
        self,
        tool_outputs: list[run_submit_tool_outputs_params.ToolOutput],
        run_id: str,
    ) -> None:
        assert self.current_run is not None

        # Use the submit_tool_outputs_stream helper
        with self._client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=self.current_run.thread_id,
            run_id=self.current_run.id,
            tool_outputs=tool_outputs,
            # Annoying recursion
            event_handler=AssistantEventHandler(
                self._client, self._console, *self._tool_managers
            ),
        ) as stream:
            for text in stream.text_deltas:
                self._console.success(text, end='')
            self._console.print()


class TextHandler:
    """Tool-rich conversation via text input and the Assistant API."""

    def __init__(
        self,
        *tools: tool_manager.ToolManager,
        system_prompt: str | None = None,
        model: str | None = None,
        initial_prompt: str | None = None,
    ) -> None:
        self._tools = tools
        self._client = openai.OpenAI()
        self._console = console_utils.Console()

        self._system_prompt = system_prompt or 'You are a helpful assistant'
        self._model = model or 'gpt-4o-mini'
        self._initial_prompt = initial_prompt or ''

    def run(self) -> None:
        assistant = self._client.beta.assistants.create(
            instructions=self._system_prompt,
            model=self._model,
            tools=[
                util.get_assistant_tool_schema(tool_func)
                for tool in self._tools
                for tool_func in tool.tool_functions
            ],
        )
        thread = self._client.beta.threads.create()

        user_prompt = text_input.InputPrompt(
            message='Enter a message:',
            default=self._initial_prompt,
        ).execute()

        while True:
            self._client.beta.threads.messages.create(
                thread_id=thread.id,
                role='user',
                content=user_prompt,
            )

            try:
                with self._client.beta.threads.runs.stream(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    event_handler=AssistantEventHandler(
                        self._client, self._console, *self._tools
                    ),
                ) as stream:
                    for text in stream.text_deltas:
                        self._console.success(text, end='')
                    self._console.print()
            except KeyboardInterrupt:
                break

            user_prompt = text_input.InputPrompt(
                message='Enter a message:',
            ).execute()
