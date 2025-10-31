# The AZ Agent Development Note

## 20251031

In VScode juptyer interactive, when using the following code in one cell: 
```py
async def run_sequential_chats():
    user_inputs = [
        "who are you",
        "what you can do", 
        "tell me a joke"
    ]
    
    for message in user_inputs:
        response = await chat.async_chat(message=message)
        print(f"User: {message}")
        print(f"Assistant: {response}")
        print('---')

asyncio.run(run_sequential_chats())
```

Error message will pop up: `RuntimeError: asyncio.run() cannot be called from a running event loop`. 

To solve this problem, use 
```py
import nest_asyncio
nest_asyncio.apply()
```
before the function call, like this: 
```py
import nest_asyncio
nest_asyncio.apply()

async def run_sequential_chats():
    user_inputs = [
        "who are you",
        "what you can do", 
        "tell me a joke",
        "tell me another one"
    ]
    
    for message in user_inputs:
        response = await chat.async_chat(message=message)
        print(f"User: {message}")
        print(f"Assistant: {response}")
        print('---')

asyncio.run(run_sequential_chats())
```

or simply use this: 
```py
user_inputs = [
    "who are you",
    "what you can do", 
    "tell me a joke"
]

for message in user_inputs:
    response = await chat.async_chat(message=message) # type:ignore
    print(f"User: {message}")
    print(f"Assistant: {response}")
    print('---')
```

The `# type:ignore` will surpress `await` warning. 