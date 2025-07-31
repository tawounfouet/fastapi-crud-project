"""
Blog App Views - Route handlers and controllers
"""

from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, func, select

from src.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from src.apps.blog.models import BlogPost, Category, Comment, Tag
from src.apps.blog.schemas import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostResponse,
    BlogPostListResponse,
    BlogPostFilter,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    TagCreate,
    TagUpdate,
    TagResponse,
    TagListResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    CommentFilter,
    BlogStats,
)
from src.apps.blog.services import (
    BlogPostService,
    CategoryService,
    TagService,
    CommentService,
    BlogStatsService,
)
from src.apps.shared import Message

router = APIRouter()


# Category endpoints
@router.post("/categories/", response_model=CategoryResponse)
def create_category(
    *,
    session: SessionDep,
    category_in: CategoryCreate,
    current_user: CurrentUser,
) -> Any:
    """Create new category (admin only)"""
    category = CategoryService.create_category(
        session=session, category_in=category_in, created_by_id=current_user.id
    )

    # Add post count
    post_count = (
        session.exec(
            select(func.count(BlogPost.id)).where(BlogPost.category_id == category.id)
        ).first()
        or 0
    )

    category_dict = category.model_dump()
    category_dict["post_count"] = post_count
    return CategoryResponse(**category_dict)


@router.get("/categories/", response_model=CategoryListResponse)
def get_categories(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_inactive: bool = Query(False),
) -> Any:
    """Get all categories"""
    categories = CategoryService.get_categories(
        session=session, skip=skip, limit=limit, include_inactive=include_inactive
    )

    # Add post counts
    category_responses = []
    for category in categories:
        post_count = (
            session.exec(
                select(func.count(BlogPost.id)).where(
                    BlogPost.category_id == category.id
                )
            ).first()
            or 0
        )
        category_dict = category.model_dump()
        category_dict["post_count"] = post_count
        category_responses.append(CategoryResponse(**category_dict))

    # Get total count
    total = session.exec(select(func.count(Category.id))).first() or 0
    pages = (total + limit - 1) // limit

    return CategoryListResponse(
        items=category_responses, total=total, page=(skip // limit) + 1, pages=pages
    )


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: uuid.UUID, session: SessionDep) -> Any:
    """Get category by ID"""
    category = CategoryService.get_category(session=session, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    post_count = (
        session.exec(
            select(func.count(BlogPost.id)).where(BlogPost.category_id == category.id)
        ).first()
        or 0
    )

    category_dict = category.model_dump()
    category_dict["post_count"] = post_count
    return CategoryResponse(**category_dict)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    *,
    session: SessionDep,
    category_id: uuid.UUID,
    category_in: CategoryUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update category (admin only)"""
    category = CategoryService.get_category(session=session, category_id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    updated_category = CategoryService.update_category(
        session=session, db_category=category, category_in=category_in
    )

    post_count = (
        session.exec(
            select(func.count(BlogPost.id)).where(
                BlogPost.category_id == updated_category.id
            )
        ).first()
        or 0
    )

    category_dict = updated_category.model_dump()
    category_dict["post_count"] = post_count
    return CategoryResponse(**category_dict)


@router.delete("/categories/{category_id}")
def delete_category(
    *,
    session: SessionDep,
    category_id: uuid.UUID,
    current_user: CurrentUser,
) -> Message:
    """Delete category (admin only)"""
    success = CategoryService.delete_category(session=session, category_id=category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return Message(message="Category deleted successfully")


# Tag endpoints
@router.post("/tags/", response_model=TagResponse)
def create_tag(
    *,
    session: SessionDep,
    tag_in: TagCreate,
    current_user: CurrentUser,
) -> Any:
    """Create new tag (admin only)"""
    tag = TagService.create_tag(session=session, tag_in=tag_in)

    # Add post count (new tag will have 0 posts)
    post_count = 0

    tag_dict = tag.model_dump()
    tag_dict["post_count"] = post_count
    return TagResponse(**tag_dict)


@router.get("/tags/", response_model=TagListResponse)
def get_tags(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    include_inactive: bool = Query(False),
) -> Any:
    """Get all tags"""
    tags = TagService.get_tags(
        session=session, skip=skip, limit=limit, include_inactive=include_inactive
    )

    # Add post counts
    tag_responses = []
    for tag in tags:
        # Get post count using helper method
        posts = TagService.get_tag_posts(session=session, tag_id=tag.id)
        post_count = len(posts)
        tag_dict = tag.model_dump()
        tag_dict["post_count"] = post_count
        tag_responses.append(TagResponse(**tag_dict))

    total = session.exec(select(func.count(Tag.id))).first() or 0

    return TagListResponse(items=tag_responses, total=total)


@router.get("/tags/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: uuid.UUID, session: SessionDep) -> Any:
    """Get tag by ID"""
    tag = TagService.get_tag(session=session, tag_id=tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # Get post count using helper method
    posts = TagService.get_tag_posts(session=session, tag_id=tag_id)
    post_count = len(posts)
    tag_dict = tag.model_dump()
    tag_dict["post_count"] = post_count
    return TagResponse(**tag_dict)


# Blog post endpoints
@router.post("/posts/", response_model=BlogPostResponse)
def create_post(
    *, session: SessionDep, post_in: BlogPostCreate, current_user: CurrentUser
) -> Any:
    """Create new blog post"""
    post = BlogPostService.create_post(
        session=session, post_in=post_in, author_id=current_user.id
    )

    # Load relationships for response
    session.refresh(post, ["category", "comments"])

    # Get tags using helper method
    tags = BlogPostService.get_post_tags(session=session, post_id=post.id)

    # Build response
    post_dict = post.model_dump()
    post_dict["category"] = (
        CategoryResponse(**post.category.model_dump()) if post.category else None
    )
    post_dict["tags"] = [TagResponse(**tag.model_dump()) for tag in tags]
    post_dict["comment_count"] = (
        len([c for c in post.comments if c.is_approved()]) if post.comments else 0
    )

    return BlogPostResponse(**post_dict)


@router.get("/posts/", response_model=BlogPostListResponse)
def get_posts(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    tag_id: uuid.UUID | None = Query(None),
    author_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    published_only: bool = Query(False),
) -> Any:
    """Get published blog posts with filtering"""
    # Build filters
    filters = BlogPostFilter(
        status=status,
        category_id=category_id,
        tag_id=tag_id,
        author_id=author_id,
        search=search,
    )

    posts = BlogPostService.get_posts(
        session=session,
        skip=skip,
        limit=limit,
        filters=filters,
        published_only=published_only,
    )

    # Build response with relationships
    post_responses = []
    for post in posts:
        session.refresh(post, ["category", "comments"])

        # Get tags using helper method
        tags = BlogPostService.get_post_tags(session=session, post_id=post.id)

        post_dict = post.model_dump()
        post_dict["category"] = (
            CategoryResponse(**post.category.model_dump()) if post.category else None
        )
        post_dict["tags"] = [TagResponse(**tag.model_dump()) for tag in tags]
        post_dict["comment_count"] = (
            len([c for c in post.comments if c.is_approved()]) if post.comments else 0
        )

        post_responses.append(BlogPostResponse(**post_dict))

    # Get total count with same filters
    total_statement = select(func.count(BlogPost.id)).where(BlogPost.is_active == True)
    if published_only:
        total_statement = total_statement.where(
            BlogPost.status == "published", BlogPost.published_at <= func.now()
        )
    total = session.exec(total_statement).first() or 0
    pages = (total + limit - 1) // limit

    return BlogPostListResponse(
        items=post_responses, total=total, page=(skip // limit) + 1, pages=pages
    )


@router.get("/posts/{post_slug}", response_model=BlogPostResponse)
def get_post_by_slug(
    post_slug: str, session: SessionDep, increment_views: bool = Query(True)
) -> Any:
    """Get blog post by slug"""
    post = BlogPostService.get_post_by_slug(session=session, slug=post_slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Increment view count if requested
    if increment_views:
        BlogPostService.increment_view_count(session=session, post_id=post.id)
        session.refresh(post)

    # Load relationships
    session.refresh(post, ["category", "comments"])

    # Get tags using helper method
    tags = BlogPostService.get_post_tags(session=session, post_id=post.id)

    # Build response
    post_dict = post.model_dump()
    post_dict["category"] = (
        CategoryResponse(**post.category.model_dump()) if post.category else None
    )
    post_dict["tags"] = [TagResponse(**tag.model_dump()) for tag in tags]
    post_dict["comment_count"] = (
        len([c for c in post.comments if c.is_approved()]) if post.comments else 0
    )

    return BlogPostResponse(**post_dict)


@router.put("/posts/{post_id}", response_model=BlogPostResponse)
def update_post(
    *,
    session: SessionDep,
    post_id: uuid.UUID,
    post_in: BlogPostUpdate,
    current_user: CurrentUser,
) -> Any:
    """Update blog post"""
    post = BlogPostService.get_post(session=session, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check permissions - only author or superuser can update
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    updated_post = BlogPostService.update_post(
        session=session, db_post=post, post_in=post_in, updated_by_id=current_user.id
    )

    # Load relationships
    session.refresh(updated_post, ["category", "comments"])

    # Get tags using helper method
    tags = BlogPostService.get_post_tags(session=session, post_id=updated_post.id)

    # Build response
    post_dict = updated_post.model_dump()
    post_dict["category"] = (
        CategoryResponse(**updated_post.category.model_dump())
        if updated_post.category
        else None
    )
    post_dict["tags"] = [TagResponse(**tag.model_dump()) for tag in tags]
    post_dict["comment_count"] = (
        len([c for c in updated_post.comments if c.is_approved()])
        if updated_post.comments
        else 0
    )

    return BlogPostResponse(**post_dict)


@router.delete("/posts/{post_id}")
def delete_post(
    *, session: SessionDep, post_id: uuid.UUID, current_user: CurrentUser
) -> Message:
    """Delete blog post"""
    post = BlogPostService.get_post(session=session, post_id=post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check permissions - only author or superuser can delete
    if post.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )

    success = BlogPostService.delete_post(session=session, post_id=post_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found")

    return Message(message="Post deleted successfully")


# Comment endpoints
@router.post("/comments/", response_model=CommentResponse)
def create_comment(*, session: SessionDep, comment_in: CommentCreate) -> Any:
    """Create new comment (public endpoint)"""
    comment = CommentService.create_comment(session=session, comment_in=comment_in)

    # Load relationships
    session.refresh(comment, ["replies"])

    comment_dict = comment.model_dump()
    comment_dict["replies"] = (
        [CommentResponse(**reply.model_dump()) for reply in comment.replies]
        if comment.replies
        else []
    )

    return CommentResponse(**comment_dict)


@router.get("/comments/", response_model=CommentListResponse)
def get_comments(
    session: SessionDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    post_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    approved_only: bool = Query(True),
    current_user: CurrentUser | None = None,  # Optional auth
) -> Any:
    """Get comments with filtering"""
    # Build filters
    filters = CommentFilter(status=status, post_id=post_id)

    # Only show approved comments for non-admin users
    if not current_user or not current_user.is_superuser:
        approved_only = True

    comments = CommentService.get_comments(
        session=session,
        skip=skip,
        limit=limit,
        filters=filters,
        approved_only=approved_only,
    )

    # Build response with replies
    comment_responses = []
    for comment in comments:
        session.refresh(comment, ["replies"])
        comment_dict = comment.model_dump()
        comment_dict["replies"] = (
            [CommentResponse(**reply.model_dump()) for reply in comment.replies]
            if comment.replies
            else []
        )
        comment_responses.append(CommentResponse(**comment_dict))

    # Get total count
    total_statement = select(func.count(Comment.id)).where(Comment.is_active == True)
    if approved_only:
        total_statement = total_statement.where(Comment.status == "approved")
    total = session.exec(total_statement).first() or 0
    pages = (total + limit - 1) // limit

    return CommentListResponse(
        items=comment_responses, total=total, page=(skip // limit) + 1, pages=pages
    )


@router.put("/comments/{comment_id}/moderate")
def moderate_comment(
    *,
    session: SessionDep,
    comment_id: uuid.UUID,
    status: str,
    current_user: CurrentUser,
) -> CommentResponse:
    """Moderate comment (admin only)"""
    from src.apps.blog.models import CommentStatus

    try:
        comment_status = CommentStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid comment status")

    comment = CommentService.moderate_comment(
        session=session,
        comment_id=comment_id,
        status=comment_status,
        moderated_by_id=current_user.id,
    )

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    session.refresh(comment, ["replies"])
    comment_dict = comment.model_dump()
    comment_dict["replies"] = (
        [CommentResponse(**reply.model_dump()) for reply in comment.replies]
        if comment.replies
        else []
    )

    return CommentResponse(**comment_dict)


@router.delete("/comments/{comment_id}")
def delete_comment(
    *,
    session: SessionDep,
    comment_id: uuid.UUID,
    current_user: CurrentUser,
) -> Message:
    """Delete comment (admin only)"""
    success = CommentService.delete_comment(session=session, comment_id=comment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")

    return Message(message="Comment deleted successfully")


# Statistics endpoint
@router.get("/stats/", response_model=BlogStats)
def get_blog_stats(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get blog statistics (admin only)"""
    return BlogStatsService.get_blog_stats(session=session)
