from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import random
from datetime import datetime
import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# データベース設定
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./omikuji.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# データベースモデル
class OmikujiHistory(Base):
    __tablename__ = "omikuji_history"

    id = Column(Integer, primary_key=True, index=True)
    fortune = Column(String)
    description = Column(String)
    lucky_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# データベースの作成
Base.metadata.create_all(bind=engine)

app = FastAPI()

# メッセージのデータモデル
class Message(BaseModel):
    id: Optional[int] = None
    content: str

# インメモリデータベース（実際のアプリケーションではデータベースを使用することを推奨）
messages = []
current_id = 1

# おみくじの運勢リスト
fortunes = [
    {"level": "大吉", "description": "とても良い運勢です！", "lucky_number": random.randint(1, 100)},
    {"level": "中吉", "description": "良い運勢です！", "lucky_number": random.randint(1, 100)},
    {"level": "小吉", "description": "まあまあの運勢です。", "lucky_number": random.randint(1, 100)},
    {"level": "吉", "description": "普通の運勢です。", "lucky_number": random.randint(1, 100)},
    {"level": "末吉", "description": "少し注意が必要です。", "lucky_number": random.randint(1, 100)}
]

# データベースセッションの依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "こんにちは"}

@app.get("/omikuji")
async def get_omikuji(db: Session = Depends(get_db)):
    fortune = random.choice(fortunes)
    
    # データベースに履歴を保存
    db_history = OmikujiHistory(
        fortune=fortune["level"],
        description=fortune["description"],
        lucky_number=fortune["lucky_number"]
    )
    db.add(db_history)
    db.commit()
    
    return {
        "運勢": fortune["level"],
        "説明": fortune["description"],
        "ラッキーナンバー": fortune["lucky_number"]
    }

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    history = db.query(OmikujiHistory).order_by(OmikujiHistory.created_at.desc()).limit(10).all()
    return [
        {
            "運勢": h.fortune,
            "説明": h.description,
            "ラッキーナンバー": h.lucky_number,
            "日時": h.created_at
        }
        for h in history
    ]

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