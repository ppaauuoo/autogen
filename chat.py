from dataclasses import dataclass

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from autogen_core import SingleThreadedAgentRuntime
import asyncio


@dataclass
class Message:
    content: str


class MyAssistant(RoutedAgent):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gemini-2.5-flash")
        self._delegate = AssistantAgent(name, model_client=model_client)

    @message_handler
    async def handle_message(self, message: Message, ctx: MessageContext) -> None:
        print(f"{self.id.type} received message: {message.content}")
        response = await self._delegate.on_messages(
            [TextMessage(content=message.content, source="user")],
            ctx.cancellation_token,
        )
        print(f"{self.id.type}")
        print(f"responded: {response.chat_message}")


async def main() -> None:
    # Create a local embedded runtime.
    runtime = SingleThreadedAgentRuntime()

    # Register the modifier and checker agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    await MyAssistant.register(
        runtime,
        "chat",
        # Modify the value by subtracting 1
        lambda: MyAssistant(name="John"),
    )

    # Start the runtime and send a direct message to the checker.
    runtime.start()
    await runtime.send_message(Message("Hello"), AgentId("chat", "default"))
    await runtime.stop_when_idle()


asyncio.run(main())
