import json
from json import tool

from openai import OpenAI
from colorama import init, Fore
from loguru import logger

from tool_register import get_tools, dispatch_tool
import logging
logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
init(autoreset=True)





def run_conversation(query: str, stream=False, tools=None, max_retry=5):
    params = dict(model="chatglm3", messages=[{"role": "user", "content": query}], stream=stream)
    if tools:
        params["tools"] = tools
    client = OpenAI(
    base_url="http://127.0.0.1:8765/v1",
    api_key = "EMPTY"
    )
    # client = OpenAI(
    #     api_key = ""
    # )
    response = client.chat.completions.create(
        model='chatglm3',
        messages=[{"role": "user", "content": query}],
        stream=stream,
        tools=tools#type: ignore
    )
    # response = client.chat.completions.create(
    #     model='gpt-3.5-turbo-0125',
    #     messages=[{"role": "user", "content": query}],
    #     stream=stream,
    #     tools=tools#type: ignore
    # )
    for _ in range(max_retry):
        if not stream:
            print(response.choices[0].message.tool_calls)
            if response.choices[0].message.function_call:
                function_call = response.choices[0].message.function_call
                logger.info(f"Function Call Response: {function_call.model_dump()}")

                function_args = json.loads(function_call.arguments)
                tool_response = dispatch_tool(function_call.name, function_args)
                logger.info(f"Tool Call Response: {tool_response}")

                params["messages"].append(response.choices[0].message)
                params["messages"].append(
                    {
                        "role": "function",
                        "name": function_call.name,
                        "content": tool_response,  # 调用函数返回结果
                    }
                )
            # elif response.choices[0].finish_reason == "function_call":
            #     print("\n")
            #     function_call = 
            else:
                reply = response.choices[0].message.content
                logger.info(f"Final Reply: \n{reply}")
                return

        else:
            output = ""
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                print(Fore.BLUE + content, end="", flush=True)
                output += content

                if chunk.choices[0].finish_reason == "stop":
                    return

                elif chunk.choices[0].finish_reason == "function_call":
                    print("\n")

                    function_call = chunk.choices[0].delta.function_call
                    logger.info(f"Function Call Response: {function_call.model_dump()}")

                    function_args = json.loads(function_call.arguments)
                    tool_response = dispatch_tool(function_call.name, function_args)
                    logger.info(f"Tool Call Response: {tool_response}")

                    params["messages"].append(
                        {
                            "role": "assistant",
                            "content": output
                        }
                    )
                    params["messages"].append(
                        {
                            "role": "function",
                            "name": function_call.name,
                            "content": tool_response,
                        }
                    )

                    break

        response = client.chat.completions.create(**params)


if __name__ == "__main__":
    from openai import OpenAI
    # client = OpenAI(
    #     api_key = ""
    # )

    tools = [
    {
        "type": "function",
        "function": {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA",
            },
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
        }
    }
    ]
    messages = [{"role": "user", "content": "What's the weather like in Boston today?"}]
    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages,
    tools=tools,
    tool_choice="auto"
    )
    
    query = "你是谁"
    tools = get_tools()
    
    tools = [tools[k] for k in tools.keys() ]
    print(json.dumps(tools,indent=2))
    tools = [
        {
            "type": 'function',
            "function": tool
        }
        for tool in tools
    ]
    run_conversation(query, tools=tools, stream=False)
    # run_conversation(query, tools=[tools[k] for k in tools.keys() ], stream=False)

    # logger.info("\n=========== next conversation ===========")

    query = "帮我查询北京的天气怎么样"
    # print(json.dumps(tools,indent=2))
    run_conversation(query, tools=tools, stream=False)
    # run_conversation(query, tools=[tools[k] for k in tools.keys() ], stream=False)
