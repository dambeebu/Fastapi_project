# posts.py (recommended; copy/paste)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db import get_db
from models import Post
from datetime import datetime

# import get_current_user from auth — if circular imports occur, move this import inside endpoints
from auth import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])

class PostIn(BaseModel):
    title: str
    content: str

class PostOut(BaseModel):
    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

@router.post("/", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(post_in: PostIn, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    # current_user is a models.User SQLAlchemy object
    new_post = Post(
        title=post_in.title,
        content=post_in.content,
        user_id=current_user.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post

@router.get("/", response_model=List[PostOut])
async def list_posts(user_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    q = select(Post)
    if user_id:
        q = q.where(Post.user_id == user_id)
    result = await db.execute(q)
    return result.scalars().all()

@router.get("/{post_id}", response_model=PostOut)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/{post_id}", response_model=PostOut)
async def update_post(post_id: int, post_in: PostIn, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")

    post.title = post_in.title
    post.content = post_in.content
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post

@router.delete("/{post_id}")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")

    await db.delete(post)
    await db.commit()
    return {"message": f"Post {post.id} deleted"}
