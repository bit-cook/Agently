import asyncio
from agently import Agently

Agently.set_settings(
    "OpenAICompatible",
    {
        "base_url": "https://my-customize-server/v1",
        "model": "my-model",
        "auth": {
            # You can use 'body' key in auth
            "body": {
                "X-User-Token": "<My-Customize-Token>",
            }
        },
        "options": {
            "temperature": 0.7,
            # Or you can use options to pass customize keys
            # "X-User-Token": "<My-Customize-Token>",
        },
    },
)

llm = Agently.create_agent()


async def main():
    instant_mode_response = (
        llm.input("Give me 5 computer-related words and 3 color-related phrases and 1 random sentence.")
        .output(
            {
                "words": [(str,)],
                "phrases": {
                    "<color-name>": (str, "phrase"),
                },
                "sentence": (str,),
            }
        )
        .get_async_generator(content="instant")
    )

    async for event in instant_mode_response:
        print(
            event.path,
            "[DONE]" if event.is_complete else "[>>>>]",
            event.value,
        )


asyncio.run(main())
