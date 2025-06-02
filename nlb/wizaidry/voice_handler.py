import asyncio
import base64
import json
import traceback
from typing import Any, Callable, cast

import openai
import sounddevice as sd
from openai.resources.beta.realtime import realtime
from openai.types.beta.realtime import response_function_call_arguments_done_event
from openai.types.beta.realtime import session
from pynput import keyboard
from rich import align
from rich import box
from rich import layout
from rich import live
from rich import panel

from nlb.util import console_utils
from nlb.wizaidry import audio_util
from nlb.mcp import tool_manager
from nlb.wizaidry import util


class VoiceHandler:
    """Tool-rich oice-to-voice interaction via the Realtime API.

    Derived from the push-to-talk example in the OpenAI Python SDK:
    https://github.com/openai/openai-python/blob/f66d2e6fdc51c4528c99bb25a8fbca6f9b9b872d/examples/realtime/push_to_talk_app.py

    NOTE: This requires an X-based backend to run. Using Wayland requires an env var
    to change the `pynput` backend and to run as root. For recent Ubuntu versions,
    a convenient X-based backend is the VsCode integrated terminal; just run it from there.
    """

    def __init__(
        self,
        *tool_managers: tool_manager.ToolManager,
        system_prompt: str | None = None,
        model: str | None = None,
    ):
        self._system_prompt = system_prompt or 'You are a helpful assistant'
        self._model = model or 'gpt-4o-realtime-preview'

        #
        # "TUI" management
        #
        self._console_panel = console_utils.ConsolePanel()

        self._layout = layout.Layout()
        self._layout.split_column(
            layout.Layout(name='instructions', size=3),
            layout.Layout(name='bottom', ratio=1),
        )

        self._layout['bottom'].split_row(
            layout.Layout(name='response', ratio=2),
            layout.Layout(self._console_panel, name='logs', ratio=1),
        )

        self._instructions_panel = panel.Panel(
            align.Align.center(
                'Press "k" to record.',
                vertical='middle',
            ),
            box=box.ROUNDED,
            title='[b blue]Instructions',
            border_style='bright_blue',
        )
        self._log_panel = panel.Panel(
            '',
            box=box.ROUNDED,
            padding=(1, 2),
            title='[b green]Logs',
            border_style='bright_blue',
        )

        self._layout['instructions'].update(self._instructions_panel)
        self._layout['response'].update(self._log_panel)

        #
        # Tool handling
        #
        self._tool_managers = tool_managers

        self._tool_map: dict[str, Callable[..., str]] = {
            func.__name__: func
            for tool in self._tool_managers
            for func in tool.tool_functions
        }

        #
        # IO and synchronization
        #
        self._listen_thread = None
        self._recording = False
        self._loop = asyncio.new_event_loop()
        self._connection: realtime.AsyncRealtimeConnection | None = None
        self._session: session.Session | None = None
        self._client = openai.AsyncOpenAI()
        self._audio_player = audio_util.AudioPlayerAsync()
        self._last_audio_item_id: str | None = None
        self._should_send_audio = asyncio.Event()
        self._connected = asyncio.Event()
        self._stopped = asyncio.Event()

    def update_user_instructions(self, text: str) -> None:
        """Update user-facing instructions in the TUI."""
        self._instructions_panel.renderable = align.Align.center(
            text,
            vertical='middle',
        )

    def update_agent_response(self, text: str) -> None:
        """Update the agent's response in the TUI."""
        self._log_panel.renderable = text

    def run(self) -> None:
        """Run the TUI and kick off realtime AI interactions."""
        with live.Live(self._layout, refresh_per_second=10, screen=True):
            with keyboard.Listener(on_press=self.on_press_handler) as listener:
                self._listen_thread = listener

                async def wait_for_end():
                    await self._stopped.wait()

                self._loop.create_task(self._handle_realtime_connection())
                self._loop.create_task(self._send_mic_audio())
                self._loop.run_until_complete(wait_for_end())

    def on_press_handler(self, key: keyboard.KeyCode | keyboard.Key | None) -> None:
        """World's most mediocre async keyboard handler."""
        asyncio.run_coroutine_threadsafe(self.on_press(key), self._loop)

    async def on_press(self, key: keyboard.KeyCode | keyboard.Key | None) -> None:
        if key is None:
            return

        if isinstance(key, keyboard.Key):
            # Special character like a function key
            pass
        else:
            if key.char == 'q':
                self.quit()
            elif key.char == 'k':
                if self._recording:
                    self._should_send_audio.clear()
                    self._recording = False

                    if self._session and self._session.turn_detection is None:
                        # The default in the API is that the model will automatically detect when the user has
                        # stopped talking and then start responding itself.
                        #
                        # However if we're in manual `turn_detection` mode then we need to
                        # manually tell the model to commit the audio buffer and start responding.
                        conn = await self._get_connection()
                        await conn.input_audio_buffer.commit()
                        await conn.response.create()

                    self.update_user_instructions("Press 'k' to record.")
                else:
                    self._should_send_audio.set()
                    self._recording = True

                    self.update_user_instructions("Press 'k' to stop recording.")

    def quit(self):
        if self._listen_thread:
            self._listen_thread.stop()
        self._stopped.set()

    async def _handle_realtime_connection(self) -> None:
        """AI -> User (or tool) audio and text stream."""
        try:
            async with self._client.beta.realtime.connect(model=self._model) as conn:
                self._connection = conn
                self._connected.set()

                await conn.session.update(
                    session={
                        'instructions': self._system_prompt,
                        'voice': 'shimmer',
                        'turn_detection': {'type': 'server_vad'},
                        'tools': [
                            util.get_realtime_tool_schema(tool_func)
                            for tool in self._tool_managers
                            for tool_func in tool.tool_functions
                        ],
                    }
                )

                acc_items: dict[str, Any] = {}

                async for event in conn:
                    match event.type:
                        case 'session.created':
                            self._session = event.session
                            continue
                        case 'session.updated':
                            self._session = event.session
                            continue
                        case 'response.audio.delta':
                            if event.item_id != self._last_audio_item_id:
                                self._audio_player.reset_frame_count()
                                self._last_audio_item_id = event.item_id

                            bytes_data = base64.b64decode(event.delta)
                            self._audio_player.add_data(bytes_data)
                            continue
                        case 'response.audio_transcript.delta':
                            try:
                                text = acc_items[event.item_id]
                            except KeyError:
                                acc_items[event.item_id] = event.delta
                            else:
                                acc_items[event.item_id] = text + event.delta

                            self.update_agent_response(acc_items[event.item_id])
                            continue
                        case 'response.function_call_arguments.done':
                            await self._on_tool_call(event)
                            continue
                        case _:
                            continue
        except Exception as e:
            # The TUI hides stuff, so this gross except block tries to print any errors
            traceback.print_exc()
            self.update_agent_response(f'Error: {e}')

    async def _get_connection(self) -> realtime.AsyncRealtimeConnection:
        await self._connected.wait()
        assert self._connection is not None
        return self._connection

    async def _send_mic_audio(self) -> None:
        """User -> AI audio stream."""
        device_info = sd.query_devices()
        print(device_info)

        read_size = int(audio_util.SAMPLE_RATE * 0.02)

        stream = sd.InputStream(
            channels=audio_util.CHANNELS,
            samplerate=audio_util.SAMPLE_RATE,
            dtype='int16',
        )
        stream.start()

        try:
            sent_audio = False
            while True:
                if stream.read_available < read_size:
                    await asyncio.sleep(0)
                    continue

                await self._should_send_audio.wait()
                self._recording = True

                data, _ = stream.read(read_size)

                connection = await self._get_connection()
                if not sent_audio:
                    self._loop.create_task(connection.send({'type': 'response.cancel'}))
                    sent_audio = True

                await connection.input_audio_buffer.append(
                    audio=base64.b64encode(cast(Any, data)).decode('utf-8')
                )

                await asyncio.sleep(0)
        except KeyboardInterrupt:
            pass
        finally:
            stream.stop()
            stream.close()

    async def _on_tool_call(
        self,
        event: response_function_call_arguments_done_event.ResponseFunctionCallArgumentsDoneEvent,  # Rolls right off the tongue
    ) -> None:
        """Handle a tool call from the AI assistant."""
        connection = await self._get_connection()

        # Missing from the type hinting in the SDK
        func_name = event.name  # type: ignore

        async def send_item_and_ask_for_response(
            client_event,  # Really annoying to type hint
        ):
            await connection.send(client_event)
            await connection.send(
                {
                    'type': 'response.create',
                }
            )

        if func_name not in self._tool_map:
            self._loop.create_task(
                send_item_and_ask_for_response(
                    {
                        'type': 'conversation.item.create',
                        'item': {
                            'type': 'function_call_output',
                            'call_id': event.call_id,
                            'output': f'Tool {func_name} not found in tools.',
                        },
                    }
                )
            )
            return

        # Trust that we get good kwargs back; no issues thus far
        kwargs = json.loads(event.arguments)

        self._console_panel.print(
            f'Calling tool {func_name} with args: {event.arguments}'
        )

        # Invoke the tool
        output = self._tool_map[func_name](**kwargs)

        self._console_panel.info(f'Tool output: {output}')

        self._loop.create_task(
            send_item_and_ask_for_response(
                {
                    'type': 'conversation.item.create',
                    'item': {
                        'type': 'function_call_output',
                        'call_id': event.call_id,
                        'output': output,
                    },
                }
            )
        )
