import asyncio
from telegram import Bot
from datetime import datetime, timezone

class MediaBot:
    def __init__(self, token: str, group_id: str):
        self.token = token
        self.group_id = group_id
        self.bot = Bot(token=self.token)

    async def send_alert(self, data):
        """Processes alert messages and sends message(s) asynchronously."""
        try:
            if not isinstance(data, list):
                data = [data]  # Convert single dict to a list

            alert_messages = []  # Store formatted messages
            ok_messages = []

            for item in data:
                balance = item['balance']
                # print(f"Balance: {balance}, Threshold_low: {item['threshold_low']}, Threshold_high: {item['threshold_high']}, Status: {item['balance'] < float(item['threshold_high'])}")
                if isinstance(balance, str):
                    balance = float(balance.replace(',', ''))

                item['balance'] = balance
                item['time'] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

                if item['balance'] == 0:
                    item['status'] = "Critical Alert 🚨"
                elif item['balance'] < float(item['threshold_low']):
                    item['status'] = "High Alert ⚠️"
                # elif item['balance'] < float(item['threshold_high']):
                #     item['status'] = "Alert ⚠️"
                # else:
                #     item['status'] = "OK ✅"

                if item['balance'] < float(item['threshold_low']):
                    alert_messages.append(self.format_message(item))
                # else:
                #     ok_messages.append(self.format_message(item))

            # Send alerts in chunks
            if alert_messages:
                await self.send_chunked_messages(alert_messages)
                print("Sent alert message(s).")

            # Optionally also send OK messages
            # if ok_messages:
            #     await self.send_chunked_messages(ok_messages)
            #     print("Sent OK message(s).")

        except Exception as e:
            print(f"Error sending alert: {e}")

    async def send_chunked_messages(self, messages, max_length=4000):
        """Send list of messages split into Telegram-acceptable chunks."""
        chunk = ""
        for msg in messages:
            if len(chunk) + len(msg) > max_length:
                await self.send_message(chunk)
                chunk = msg
            else:
                chunk += "\n\n" + msg

        if chunk:
            await self.send_message(chunk)

    async def send_message(self, message: str):
        """Sends a message asynchronously (single message assumed <4096 chars)."""
        try:
            await self.bot.send_message(chat_id=self.group_id, text=message)
        except Exception as e:
            print(f"Failed to send message: {e}")

    def format_message(self, data: dict) -> str:
        """Formats a single alert entry."""
        return (
            f"🚨 **{data['status']}** 🚨\n"
            f"- Brand: {data.get('brand', 'N/A')}\n"
            f"- Currency: {data.get('currency', 'N/A')}\n"
            f"- Publisher: {data.get('platform', 'N/A')}\n"
            f"- Balance: ${data.get('balance', 'N/A')}\n"
            f"- Time: {data.get('time', 'N/A')}\n"
            f"----------------------------------------\n"
        )
