"""
Lightweight uAgents-compatible runtime for Python 3.12+.
Provides Agent, Bureau, Context, Model, and AgentStorage with the same
API surface as Fetch.ai uAgents so agent code is easy to migrate.
"""
import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, Optional, Type

from pydantic import BaseModel


class Model(BaseModel):
    pass


class AgentStorage:
    """Persistent key-value store backed by a JSON file."""

    def __init__(self, agent_name: str):
        self._path = f"/tmp/scaena_{agent_name}_storage.json"
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        try:
            with open(self._path) as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            with open(self._path, "w") as f:
                json.dump(self._data, f)
        except Exception:
            pass

    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]


# Global registry: address → Agent
_REGISTRY: Dict[str, "Agent"] = {}


class Context:
    def __init__(self, agent: "Agent"):
        self.address = agent.address
        self.storage = agent.storage
        self.logger = logging.getLogger(f"scaena.{agent.name}")

    async def send(self, address: str, message: "Model"):
        target = _REGISTRY.get(address)
        if not target:
            self.logger.warning(f"No agent at address {address!r}")
            return
        await target._inbox.put(message)


class Agent:
    def __init__(self, name: str, seed: str = "", port: int = 8000, **kwargs):
        self.name = name
        self.seed = seed
        self.port = port
        # Deterministic fake address
        self.address = f"agent1q{name.replace('_', '').replace('-', '')}"
        self.storage = AgentStorage(name)
        self._ctx = Context(self)
        self._startup_handlers: list = []
        self._interval_handlers: list = []
        self._message_handlers: Dict[str, tuple] = {}
        self._inbox: asyncio.Queue = asyncio.Queue()
        _REGISTRY[self.address] = self

    @property
    def wallet(self):
        class _Wallet:
            address = "mock_wallet_address"
        return _Wallet()

    def on_event(self, event_type: str):
        def decorator(func: Callable):
            if event_type == "startup":
                self._startup_handlers.append(func)
            return func
        return decorator

    def on_interval(self, period: float):
        def decorator(func: Callable):
            self._interval_handlers.append((func, period))
            return func
        return decorator

    def on_message(self, model: Type[Model]):
        def decorator(func: Callable):
            self._message_handlers[model.__name__] = (func, model)
            return func
        return decorator

    async def _run_inbox(self):
        while True:
            message = await self._inbox.get()
            msg_type = type(message).__name__
            if msg_type in self._message_handlers:
                func, _ = self._message_handlers[msg_type]
                try:
                    await func(self._ctx, self.address, message)
                except Exception as e:
                    self._ctx.logger.error(f"Handler error for {msg_type}: {e}", exc_info=True)

    async def _run_interval(self, func: Callable, period: float):
        await asyncio.sleep(period)
        while True:
            try:
                await func(self._ctx)
            except Exception as e:
                self._ctx.logger.error(f"Interval error in {func.__name__}: {e}", exc_info=True)
            await asyncio.sleep(period)

    async def run(self):
        for handler in self._startup_handlers:
            try:
                await handler(self._ctx)
            except Exception as e:
                self._ctx.logger.error(f"Startup error: {e}", exc_info=True)

        tasks = [self._run_inbox()]
        for func, period in self._interval_handlers:
            tasks.append(self._run_interval(func, period))

        await asyncio.gather(*tasks)


class Bureau:
    def __init__(self):
        self._agents: list = []

    def add(self, agent: Agent):
        self._agents.append(agent)

    def run(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
        asyncio.run(self._run())

    async def _run(self):
        await asyncio.gather(*[agent.run() for agent in self._agents])
