from dataclasses import dataclass

from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler


from autogen_core import SingleThreadedAgentRuntime
import asyncio


@dataclass
class Message:
    content: str


class EchoAgent(RoutedAgent):
    def __init__(self) -> None:
        super().__init__("MyAgent")

    @message_handler
    async def handle_my_message_type(
        self, message: Message, ctx: MessageContext
    ) -> None:
        print(f"{self.id.type} received message: {message.content}")


async def main() -> None:
    # Create a local embedded runtime.
    runtime = SingleThreadedAgentRuntime()

    # Register the modifier and checker agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    await EchoAgent.register(
        runtime,
        "echo",
        # Modify the value by subtracting 1
        lambda: EchoAgent(),
    )

    # Start the runtime and send a direct message to the checker.
    runtime.start()
    await runtime.send_message(Message("This is echo!"), AgentId("echo", "default"))
    await runtime.stop_when_idle()


asyncio.run(main())
