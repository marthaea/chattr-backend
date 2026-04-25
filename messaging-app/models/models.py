from sqlalchemy import (
    Column, Integer, String, Text, Boolean,
    ForeignKey, DateTime, func
)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    avatar_url = Column(Text, nullable=True)           # profile picture
    bio = Column(String(200), nullable=True)           # short bio
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participations = relationship("Participant", back_populates="user")
    sent_messages = relationship("Message", back_populates="sender")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    participants = relationship("Participant", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation", order_by="Message.sent_at")


class Participant(Base):
    __tablename__ = "participants"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), primary_key=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="participations")
    conversation = relationship("Conversation", back_populates="participants")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)       # text or Cloudinary URL
    message_type = Column(String(20), default="text")  # text | image | audio | video | file
    file_name = Column(String(255), nullable=True)     # original filename for downloads
    file_size = Column(Integer, nullable=True)         # bytes
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
