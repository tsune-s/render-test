from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI()

# メッセージのデータモデル
class Message(BaseModel):
    id: Optional[int] = None
    content: str

# インメモリデータベース（実際のアプリケーションではデータベースを使用することを推奨）
messages = []
current_id = 1

@app.get("/")
async def root():
    return {"message": "こんにちは"}

# メッセージの作成
@app.post("/messages/", response_model=Message)
async def create_message(message: Message):
    global current_id
    message.id = current_id
    current_id += 1
    messages.append(message)
    return message

# 全メッセージの取得
@app.get("/messages/", response_model=List[Message])
async def get_messages():
    return messages

# 特定のメッセージの取得
@app.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: int):
    for message in messages:
        if message.id == message_id:
            return message
    raise HTTPException(status_code=404, detail="Message not found")

# メッセージの削除
@app.delete("/messages/{message_id}")
async def delete_message(message_id: int):
    for i, message in enumerate(messages):
        if message.id == message_id:
            messages.pop(i)
            return {"message": "Message deleted successfully"}
    raise HTTPException(status_code=404, detail="Message not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 