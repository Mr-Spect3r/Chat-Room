import asyncio
import websockets
import os
import base64
import threading
import queue
from colorama import Fore, Style, init
import sys

init(autoreset=True)

msg_queue = queue.Queue()

def input_thread():
    while True:
        try:
            line = input(" > ")
            msg_queue.put(line)
            if line.lower() in {"exit", "quit"}:
                break
        except EOFError:
            break

async def receive(ws):
    while True:
        try:
            msg = await ws.recv()
            if msg.startswith("\U0001F4E5"):  
                parts = msg.split(maxsplit=2)
                if len(parts) == 3:
                    filename, b64data = parts[1], parts[2]
                    try:
                        with open(filename, "wb") as f:
                            f.write(base64.b64decode(b64data))
                        print(f"\n{Fore.GREEN}💾 Downloaded '{filename}' successfully.\n > ", end="", flush=True)
                    except Exception as e:
                        print(f"\n{Fore.RED}❌ Save error: {e}\n > ", end="", flush=True)
            else:
                print(f"\n{Fore.LIGHTWHITE_EX}{msg}\n > ", end="", flush=True)
        except Exception:
            print(f"\n{Fore.RED}❌ Connection lost.\n")
            break

async def send(ws):
    while True:
        msg = await asyncio.get_event_loop().run_in_executor(None, msg_queue.get)
        if msg.lower() in {"exit", "quit"}:
            print("Disconnecting...")
            await ws.close()
            break

        if msg.startswith("/send"):
            parts = msg.split(maxsplit=1)
            if len(parts) != 2:
                print(f"{Fore.YELLOW}❗ Usage: /send path_to_file")
                continue
            filepath = parts[1]
            if os.path.exists(filepath):
                try:
                    with open(filepath, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                    fname = os.path.basename(filepath)
                    await ws.send(f"/send {fname} {b64}")
                except Exception as e:
                    print(f"{Fore.RED}❌ File read error: {e}")
            else:
                print(f"{Fore.RED}❌ File not found.")
        else:
            await ws.send(msg)

async def main():
    ip = input("🌐 Server IP [127.0.0.1]: ") or "127.0.0.1"
    port = input("🔌 Port [9990]: ") or "9990"
    uri = f"ws://{ip}:{port}"

    try:
        async with websockets.connect(uri) as ws:
            print(await ws.recv())  
            pw = input(" > ")
            await ws.send(pw)

            print(await ws.recv())  
            username = input(" > ")
            await ws.send(username)

            if username.strip() == "admin":
                print(await ws.recv())  
                admin_pw = input(" > ")
                await ws.send(admin_pw)

            print(f"🕷️ Connected. Use /pm, /send, /down, /list, /list show, /help or chat normally.\n")

            input_thr = threading.Thread(target=input_thread, daemon=True)
            input_thr.start()

            await asyncio.gather(receive(ws), send(ws))

    except Exception as e:
        print(f"{Fore.RED}❌ Could not connect: {e}")

if __name__ == "__main__":
    asyncio.run(main())