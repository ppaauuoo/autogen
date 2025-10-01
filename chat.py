from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient


from autogen_core import AgentId, MessageContext, RoutedAgent, message_handler
from autogen_core import SingleThreadedAgentRuntime
import asyncio


from io import BytesIO

import requests
from autogen_core import Image as AGImage
from PIL import Image


class ImageAgent(RoutedAgent):
    @message_handler
    async def on_image_message(
        self, message: MultiModalMessage, ctx: MessageContext
    ) -> TextMessage:
        print(f"{self.id.type} received message")
        return TextMessage(
            content=f"Hello from image agent, {message.source}, you sent me {message}!",
            source="ImageAgent",
        )


class MyAssistant(RoutedAgent):
    def __init__(self, name: str, inner_agent_type: str) -> None:
        super().__init__(name)
        model_client = OpenAIChatCompletionClient(model="gemini-2.5-flash")
        self._delegate = AssistantAgent(name, model_client=model_client)
        self.image_agent_id = AgentId(inner_agent_type, self.id.key)

    @message_handler(match=lambda msg, ctx: msg.source.startswith("user"))
    async def handle_text_message(
        self, message: TextMessage, ctx: MessageContext
    ) -> None:
        print(f"{self.id.type} received message")
        print(f"Hello, {message.source}, you said {message.content}!")
        response = await self._delegate.on_messages(
            [message],
            ctx.cancellation_token,
        )
        print(f"{self.id.type} responded")
        print(f"{response.chat_message}")

    @message_handler(match=lambda msg, ctx: msg.source.startswith("img"))
    async def handle_image_message(
        self, message: TextMessage, ctx: MessageContext
    ) -> None:
        try:
            print(f"{self.id.type} received message")
            response = requests.get(message.content)
            response.raise_for_status()
            pil_image = Image.open(BytesIO(response.content))
            img = AGImage(pil_image)
            multi_modal_message = MultiModalMessage(
                content=[message.content, img], source="user"
            )
            response = await self.send_message(multi_modal_message, self.image_agent_id)
            print(f"Hello from your agent, {message.source}, I got {response.content}!")
        except requests.RequestException as e:
            print(f"Error fetching image: {e}")
        except Exception as e:
            print(f"Error processing image: {e}")

    @message_handler()
    async def handle_multimodal_message(
        self, message: MultiModalMessage, ctx: MessageContext
    ) -> None:
        try:
            print(f"{self.id.type} received message")
            response = await self.send_message(message, self.image_agent_id)
            print(f"Hello from your agent, {message.source}, I got {response.content}!")
        except requests.RequestException as e:
            print(f"Error fetching image: {e}")
        except Exception as e:
            print(f"Error processing image: {e}")


async def main() -> None:
    # Create a local embedded runtime.
    runtime = SingleThreadedAgentRuntime()

    # Register the modifier and checker agents by providing
    # their agent types, the factory functions for creating instance and subscriptions.
    await ImageAgent.register(
        runtime,
        "img",
        # Modify the value by subtracting 1
        lambda: ImageAgent("ImageAgent"),
    )
    await MyAssistant.register(
        runtime,
        "chat",
        # Modify the value by subtracting 1
        lambda: MyAssistant(name="ChatBot", inner_agent_type="img"),
    )

    # Start the runtime and send a direct message to the checker.
    runtime.start()
    await runtime.send_message(
        TextMessage(content="Hello what's your name", source="user"),
        AgentId("chat", "default"),
    )

    await runtime.send_message(
        TextMessage(content="https://picsum.photos/300/200", source="img"),
        AgentId("chat", "default"),
    )

    pil_image = Image.open(
        BytesIO(requests.get("https://picsum.photos/300/200").content)
    )
    img = AGImage(pil_image)

    await runtime.send_message(
        MultiModalMessage(
            content=["What is this image about", img],
            source="user",
        ),
        AgentId("chat", "default"),
    )
    await runtime.stop_when_idle()


asyncio.run(main())
