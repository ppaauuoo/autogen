from dataclasses import dataclass

from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler


from autogen_core import AgentId, SingleThreadedAgentRuntime

import asyncio


@dataclass
class MyMessageType:
    content: str


class MyAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("MyAgent")

    @message_handler
    async def handle_my_message_type(
        self, message: MyMessageType, ctx: MessageContext
    ) -> None:
        print(f"{self.id.type} received message: {message.content}")


async def main() -> None:
    # Create a local embedded runtime.
    runtime = SingleThreadedAgentRuntime()

    # Register the modifier and checker agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    await MyAgent.register(
        runtime,
        "modifier",
        # Modify the value by subtracting 1
        lambda: Modifier(modify_val=lambda x: x - 1),
    )

    # Start the runtime and send a direct message to the checker.
    runtime.start()
    await runtime.send_message(Message(10), AgentId("agent", "default"))
    await runtime.stop_when_idle()


asyncio.run(main())
