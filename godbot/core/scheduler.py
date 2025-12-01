# GodBot core scheduler module
import asyncio
import time
from typing import Callable, Dict, Any

class ScheduledTask:
    def __init__(self, name: str, interval: int, func: Callable, enabled=True):
        self.name = name
        self.interval = interval  # seconds
        self.func = func
        self.enabled = enabled
        self.last_run = 0

class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False

    def add(self, name: str, interval_sec: int, func: Callable):
        self.tasks[name] = ScheduledTask(name, interval_sec, func)
        print(f"[Scheduler] Added task: {name} every {interval_sec}s")

    def enable(self, name: str):
        if name in self.tasks:
            self.tasks[name].enabled = True

    def disable(self, name: str):
        if name in self.tasks:
            self.tasks[name].enabled = False

    async def start(self):
        if self.running:
            return

        self.running = True
        print("[Scheduler] Started")

        while True:
            now = time.time()

            for name, task in self.tasks.items():
                if not task.enabled:
                    continue

                if now - task.last_run >= task.interval:
                    try:
                        asyncio.create_task(task.func(self.bot))
                        task.last_run = now
                    except Exception as e:
                        print(f"[Scheduler] Error in task {name}: {e}")

            await asyncio.sleep(1)

