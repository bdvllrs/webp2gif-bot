from io import BytesIO

from maubot import Plugin, MessageEvent
from mautrix.crypto.attachments import decrypt_attachment
from mautrix.types import EventType, MessageType, EncryptedFile
from mautrix.util import magic
from maubot.handlers import event
from PIL import Image


class WebPToGifBot(Plugin):
    async def get_media(self, file: EncryptedFile) -> bytes:
        data = await self.client.download_media(file.url)
        data = decrypt_attachment(
            data, file.key.key, file.hashes.get("sha256"), file.iv
        )
        return data

    @event.on(EventType.ROOM_MESSAGE)
    async def handler(self, evt: MessageEvent):
        if evt.content.msgtype != MessageType.IMAGE:
            return
        mime_type = evt.content.info['mimetype']
        if mime_type in ["image/webp", "image/gif"]:
            data = await self.get_media(evt.content.file)
            mime_type = magic.mimetype(data)
            with Image.open(BytesIO(data)) as img:
                with BytesIO() as data_bytes:
                    loop = img.info.get("loop", 0)
                    duration = img.info.get("duration", 70)
                    img.save(
                        data_bytes,
                        "gif",
                        save_all=True,
                        duration=duration,
                        loop=loop,
                        background=0,
                    )
                    data = data_bytes.getvalue()
            filename = ".".join(evt.content.body.split(".")[:-1]) + ".gif"
            uri = await self.client.upload_media(data, "image/gif", filename)
            info = evt.content.info
            info['mimetype'] = "image/gif"
            await self.client.send_image(evt.room_id, uri, info=info, file_name=filename)
