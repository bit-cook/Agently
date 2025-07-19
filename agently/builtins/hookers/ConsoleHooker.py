# Copyright 2023-2025 AgentEra(Agently.Tech)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from agently.utils import LazyImport

LazyImport.import_package("rich")

import json
import threading
from collections import deque
from datetime import datetime
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.text import Text
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich.text import Text
from rich.live import Live

from agently.types.plugins import EventHooker

if TYPE_CHECKING:
    from agently.types.data.event import EventMessage, EventStatus


class ConsoleManager:
    def __init__(self):
        self._table_data = {}
        self._console = Console()
        self._running = False
        self._console_thread: threading.Thread | None = None
        self._update_event = threading.Event()
        self._lock = threading.Lock()
        self._log_messages = deque(maxlen=20)

    def update_table(self, table_name: str, row_id: str | int, update_dict: dict[str, Any]):
        if table_name not in self._table_data:
            self._table_data.update({table_name: {}})
        if row_id not in self._table_data[table_name]:
            self._table_data[table_name].update({row_id: {}})
        target_row = self._table_data[table_name][row_id]
        for key, value in update_dict.items():
            if value:
                if key[0] == "$":
                    delta_key = key[1:]
                    if delta_key not in target_row:
                        target_row[delta_key] = ""
                    target_row[delta_key] += str(value)
                elif key == "Request Data" and isinstance(value, dict):
                    simplify_request_data_keys = [
                        "data",
                        "request_options",
                        "request_url",
                    ]
                    simplified_request_data = []
                    for k, v in value.items():
                        if k in simplify_request_data_keys:
                            simplified_request_data.append(f"{k}: {json.dumps(v, indent=2, ensure_ascii=False)}")
                    target_row[key] = "\n".join(simplified_request_data)
                else:
                    target_row[key] = value
        self._update_event.set()

    def append_log(self, message: str):

        timestamp = datetime.now().strftime("%H:%M:%S")
        self._log_messages.append(Text(f"[{timestamp}] {message}"))
        self._update_event.set()

    def render(self):

        layout = Layout()

        layout.split_column(
            Layout(name="tables"),
            Layout(name="logs", size=10),
            Layout(name="footer", size=1),
        )

        table_panels: list[Panel] = []

        for table_name, rows in reversed(list(self._table_data.items())):
            if not rows:
                continue
            headers = ["ID"] + list(next(iter(rows.values())).keys())
            table = Table(title=table_name, show_lines=True)
            for header in headers:
                table.add_column(header, style="bold")

            for row_id, data in rows.items():
                row_id = str(row_id)
                row = [row_id[:7] + "..." if len(row_id) > 6 else row_id] + [
                    str(data.get(column_name, "")) for column_name in headers[1:]
                ]
                table.add_row(*row)

            table_panels.append(table)  # type:ignore

        tables_renderable = Group(*table_panels) if table_panels else Text("Nothing to display.")
        layout["tables"].update(Panel(tables_renderable, title="Runtime Dashboard", border_style="green"))

        layout["logs"].update(Panel(Group(*self._log_messages), title="Logs", border_style="dim"))

        layout["footer"].update(Text("Press Ctrl+C to quit", style="bold green", justify="center"))

        return layout

    def _live(self):
        with Live(self.render(), console=self._console, refresh_per_second=4.0) as live:
            while self._running:
                self._update_event.wait()
                self._update_event.clear()
                with self._lock:
                    live.update(self.render())

    def watch(self):
        if self._running:
            return
        self._running = True
        self._console_thread = threading.Thread(target=self._live, daemon=False)
        self._console_thread.start()

    def stop(self):
        self._running = False
        self._update_event.set()
        if self._console_thread:
            self._console_thread.join()


class ConsoleHooker(EventHooker):
    name = "ConsoleHooker"
    events = ["console", "message", "log"]
    console_manager = ConsoleManager()

    _status_mapping: dict["EventStatus", str] = {
        "": "",
        "INIT": "▶️",
        "DOING": "🔨",
        "PENDING": "🕘",
        "SUCCESS": "✅",
        "FAILED": "❌",
        "UNKNOWN": "😶",
    }

    @staticmethod
    def _on_register():
        ConsoleHooker.console_manager.watch()

    @staticmethod
    def _on_unregister():
        ConsoleHooker.console_manager.stop()

    @staticmethod
    async def handler(message: "EventMessage"):
        if message.event == "console":
            ConsoleHooker.console_manager.update_table(
                message.meta["table_name"],
                message.meta["row_id"],
                message.content,
            )
        else:
            ConsoleHooker.console_manager.append_log(
                f"{ ConsoleHooker._status_mapping.get(message.status, message.status) + ' ' }"
                f"[{ message.module_name }] "
                f"{ message.content}"
            )
