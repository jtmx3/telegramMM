# Telegram Channel Manager — repaired build

This project was reconstructed from the supplied corrupted archive. The original archive had source files stored under incorrect filenames and several `.py` files containing Python 3.13 bytecode.

## Run on Windows

```powershell
cd C:\path\to\Telegram_Channel_Manager_FIXED
C:\Users\abdul\AppData\Local\Programs\Python\Python314\python.exe -m pip install -r requirements.txt
C:\Users\abdul\AppData\Local\Programs\Python\Python314\python.exe bot.py
```

The `.env` file from the supplied project is preserved. Required keys are `API_ID`, `API_HASH`, `BOT_TOKEN`, and `OWNER_ID`.

`TgCrypto` is intentionally not required. Pyrogram can run without it; omitting it avoids native-extension compatibility problems on newer Python versions.

## Python 3.14 compatibility
This build creates the asyncio event loop before importing Pyrogram 2.0.x. This fixes:
`RuntimeError: There is no current event loop in thread 'MainThread'.`

The `TgCrypto is missing` message is only a performance warning. TgCrypto is not required to run the bot and is intentionally not listed as a mandatory dependency for Python 3.14.


## Channel verification fix
The Add Channel flow now verifies the actual bot membership status with Telegram instead of treating every get_chat error as "bot is not admin". It accepts a numeric -100... ID, a public @username, or a message forwarded directly from the channel. Telegram RPC errors are shown in the bot response for troubleshooting.
