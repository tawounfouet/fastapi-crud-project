"""
Blog App Services - Business logic layer
Contains the core business rules and operations
"""

from datetime import datetime
from typing import Optional
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select, func, or_, and_, desc

from src.apps.blog.models import (
    BlogPost,
    Category,
    Tag,
    Comment,
    PostStatus,
    CommentStatus,
)
from src.apps.blog.schemas import (
    BlogPostCreate,
    BlogPostUpdate,
    BlogPostFilter,
    CategoryCreate,
    CategoryUpdate,
    TagCreate,
    TagUpdate,
    CommentCreate,
    CommentUpdate,
    CommentFilter,
    BlogStats,
)


class CategoryService:
    """Service for category management"""

    @staticmethod
    def create_category(
        *,
        session: Session,
        category_in: CategoryCreate,
        created_by_id: Optional[uuid.UUID] = None,
    ) -> Category:
        """Create a new category"""
        # Check if slug already exists
        existing = session.exec(
            select(Category).where(
                Category.slug == category_in.slug, Category.is_active == True
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400, detail="Category with this slug already exists"
            )

        # Validate parent category if provided
        if category_in.parent_id:
            parent = session.get(Category, category_in.parent_id)
            if not parent or not parent.is_active:
                raise HTTPException(
                    status_code=400, detail="Parent category not found or inactive"
                )

        db_category = Category.model_validate(category_in)
        session.add(db_category)
        session.commit()
        session.refresh(db_category)
        return db_category

    @staticmethod
    def get_category(*, session: Session, category_id: uuid.UUID) -> Optional[Category]:
        """Get a category by ID"""
        return session.get(Category, category_id)

    @staticmethod
    def get_category_by_slug(*, session: Session, slug: str) -> Optional[Category]:
        """Get a category by slug"""
        return session.exec(
            select(Category).where(Category.slug == slug, Category.is_active == True)
        ).first()

    @staticmethod
    def get_categories(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Category]:
        """Get categories with optional filtering"""
        statement = select(Category)

        if not include_inactive:
            statement = statement.where(Category.is_active == True)

        statement = statement.order_by(Category.name).offset(skip).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def update_category(
        *, session: Session, db_category: Category, category_in: CategoryUpdate
    ) -> Category:
        """Update a category"""
        # Check slug uniqueness if updating
        if category_in.slug and category_in.slug != db_category.slug:
            existing = session.exec(
                select(Category).where(
                    Category.slug == category_in.slug,
                    Category.id != db_category.id,
                    Category.is_active == True,
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400, detail="Category with this slug already exists"
                )

        category_data = category_in.model_dump(exclude_unset=True)
        category_data["updated_at"] = datetime.now()
        db_category.sqlmodel_update(category_data)
        session.add(db_category)
        session.commit()
        session.refresh(db_category)
        return db_category

    @staticmethod
    def delete_category(*, session: Session, category_id: uuid.UUID) -> bool:
        """Soft delete a category"""
        category = session.get(Category, category_id)
        if not category:
            return False

        # Check if category has posts
        posts_count = session.exec(
            select(func.count(BlogPost.id)).where(BlogPost.category_id == category_id)
        ).first()

        if posts_count and posts_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete category with existing posts. Move posts to another category first.",
            )

        category.is_active = False
        category.updated_at = datetime.now()
        session.add(category)
        session.commit()
        return True


class TagService:
    """Service for tag management"""

    @staticmethod
    def create_tag(*, session: Session, tag_in: TagCreate) -> Tag:
        """Create a new tag"""
        # Check if slug already exists
        existing = session.exec(
            select(Tag).where(Tag.slug == tag_in.slug, Tag.is_active == True)
        ).first()

        if existing:
            raise HTTPException(
                status_code=400, detail="Tag with this slug already exists"
            )

        db_tag = Tag.model_validate(tag_in)
        session.add(db_tag)
        session.commit()
        session.refresh(db_tag)
        return db_tag

    @staticmethod
    def get_tag(*, session: Session, tag_id: uuid.UUID) -> Optional[Tag]:
        """Get a tag by ID"""
        return session.get(Tag, tag_id)

    @staticmethod
    def get_tag_by_slug(*, session: Session, slug: str) -> Optional[Tag]:
        """Get a tag by slug"""
        return session.exec(
            select(Tag).where(Tag.slug == slug, Tag.is_active == True)
        ).first()

    @staticmethod
    def get_tags(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> list[Tag]:
        """Get tags with optional filtering"""
        statement = select(Tag)

        if not include_inactive:
            statement = statement.where(Tag.is_active == True)

        statement = statement.order_by(Tag.name).offset(skip).limit(limit)
        return list(session.exec(statement).all())

    @staticmethod
    def get_tag_posts(*, session: Session, tag_id: uuid.UUID) -> list[BlogPost]:
        """Get all posts associated with a tag"""
        from src.apps.blog.models import PostTag

        result = session.exec(
            select(BlogPost)
            .join(PostTag, PostTag.post_id == BlogPost.id)
            .where(
                PostTag.tag_id == tag_id,
                BlogPost.is_active == True,
                BlogPost.status == PostStatus.PUBLISHED,
            )
        ).all()

        return list(result)


class BlogPostService:
    """Service for blog post management"""

    @staticmethod
    def create_post(
        *, session: Session, post_in: BlogPostCreate, author_id: uuid.UUID
    ) -> BlogPost:
        """Create a new blog post"""
        # Check if slug already exists
        existing = session.exec(
            select(BlogPost).where(
                BlogPost.slug == post_in.slug, BlogPost.is_active == True
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400, detail="Post with this slug already exists"
            )

        # Validate category if provided
        if post_in.category_id:
            category = session.get(Category, post_in.category_id)
            if not category or not category.is_active:
                raise HTTPException(
                    status_code=400, detail="Category not found or inactive"
                )

        # Set published_at if status is published and no date provided
        if post_in.status == PostStatus.PUBLISHED and not post_in.published_at:
            post_in.published_at = datetime.now()

        # Create post
        post_data = post_in.model_dump(exclude={"tag_ids"})
        post_data.update(
            {
                "author_id": author_id,
                "created_by_id": author_id,
                "updated_by_id": author_id,
            }
        )

        db_post = BlogPost(**post_data)
        session.add(db_post)
        session.flush()  # Get the post ID

        # Handle tags (many-to-many relationship)
        if post_in.tag_ids:
            # Get existing tags
            tags = session.exec(select(Tag).where(Tag.id.in_(post_in.tag_ids))).all()

            if len(tags) != len(post_in.tag_ids):
                raise HTTPException(
                    status_code=400, detail="One or more tags not found"
                )

            # Create associations via PostTag table
            from src.apps.blog.models import PostTag

            for tag_id in post_in.tag_ids:
                association = PostTag(post_id=db_post.id, tag_id=tag_id)
                session.add(association)

        session.commit()
        session.refresh(db_post)
        return db_post

    @staticmethod
    def get_post(*, session: Session, post_id: uuid.UUID) -> Optional[BlogPost]:
        """Get a post by ID"""
        return session.get(BlogPost, post_id)

    @staticmethod
    def get_post_by_slug(*, session: Session, slug: str) -> Optional[BlogPost]:
        """Get a post by slug"""
        return session.exec(
            select(BlogPost).where(BlogPost.slug == slug, BlogPost.is_active == True)
        ).first()

    @staticmethod
    def get_posts(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[BlogPostFilter] = None,
        published_only: bool = False,
    ) -> list[BlogPost]:
        """Get posts with filtering"""
        statement = select(BlogPost)

        # Base filters
        if published_only:
            statement = statement.where(
                BlogPost.status == PostStatus.PUBLISHED,
                BlogPost.is_active == True,
                BlogPost.published_at <= datetime.now(),
            )
        else:
            statement = statement.where(BlogPost.is_active == True)

        # Apply additional filters
        if filters:
            if filters.status:
                statement = statement.where(BlogPost.status == filters.status)
            if filters.category_id:
                statement = statement.where(BlogPost.category_id == filters.category_id)
            if filters.author_id:
                statement = statement.where(BlogPost.author_id == filters.author_id)
            if filters.search:
                search_term = f"%{filters.search}%"
                statement = statement.where(
                    or_(
                        BlogPost.title.ilike(search_term),
                        BlogPost.content.ilike(search_term),
                        BlogPost.excerpt.ilike(search_term),
                    )
                )
            if filters.from_date:
                statement = statement.where(BlogPost.created_at >= filters.from_date)
            if filters.to_date:
                statement = statement.where(BlogPost.created_at <= filters.to_date)

        statement = (
            statement.order_by(desc(BlogPost.created_at)).offset(skip).limit(limit)
        )
        return list(session.exec(statement).all())

    @staticmethod
    def update_post(
        *,
        session: Session,
        db_post: BlogPost,
        post_in: BlogPostUpdate,
        updated_by_id: uuid.UUID,
    ) -> BlogPost:
        """Update a blog post"""
        # Check slug uniqueness if updating
        if post_in.slug and post_in.slug != db_post.slug:
            existing = session.exec(
                select(BlogPost).where(
                    BlogPost.slug == post_in.slug,
                    BlogPost.id != db_post.id,
                    BlogPost.is_active == True,
                )
            ).first()

            if existing:
                raise HTTPException(
                    status_code=400, detail="Post with this slug already exists"
                )

        # Handle status change to published
        if (
            post_in.status == PostStatus.PUBLISHED
            and db_post.status != PostStatus.PUBLISHED
        ):
            if not post_in.published_at:
                post_in.published_at = datetime.now()

        # Update post data
        post_data = post_in.model_dump(exclude_unset=True, exclude={"tag_ids"})
        post_data.update({"updated_at": datetime.now(), "updated_by_id": updated_by_id})
        db_post.sqlmodel_update(post_data)

        # Handle tag updates (many-to-many relationship)
        if post_in.tag_ids is not None:
            # Import PostTag locally to avoid circular import
            from src.apps.blog.models import PostTag

            # Remove existing associations
            existing_associations = session.exec(
                select(PostTag).where(PostTag.post_id == db_post.id)
            ).all()
            for assoc in existing_associations:
                session.delete(assoc)

            # Add new associations if tags provided
            if post_in.tag_ids:
                tags = session.exec(
                    select(Tag).where(Tag.id.in_(post_in.tag_ids))
                ).all()

                if len(tags) != len(post_in.tag_ids):
                    raise HTTPException(
                        status_code=400, detail="One or more tags not found"
                    )

                # Create new associations
                for tag_id in post_in.tag_ids:
                    association = PostTag(post_id=db_post.id, tag_id=tag_id)
                    session.add(association)

        session.add(db_post)
        session.commit()
        session.refresh(db_post)
        return db_post

    @staticmethod
    def increment_view_count(*, session: Session, post_id: uuid.UUID) -> bool:
        """Increment view count for a post"""
        post = session.get(BlogPost, post_id)
        if post:
            post.view_count += 1
            session.add(post)
            session.commit()
            return True
        return False

    @staticmethod
    def delete_post(*, session: Session, post_id: uuid.UUID) -> bool:
        """Soft delete a post"""
        post = session.get(BlogPost, post_id)
        if not post:
            return False

        post.is_active = False
        post.updated_at = datetime.now()
        session.add(post)
        session.commit()
        return True

    @staticmethod
    def get_post_tags(*, session: Session, post_id: uuid.UUID) -> list[Tag]:
        """Get all tags associated with a post"""
        from src.apps.blog.models import PostTag

        result = session.exec(
            select(Tag)
            .join(PostTag, PostTag.tag_id == Tag.id)
            .where(PostTag.post_id == post_id, Tag.is_active == True)
        ).all()

        return list(result)


class CommentService:
    """Service for comment management"""

    @staticmethod
    def create_comment(*, session: Session, comment_in: CommentCreate) -> Comment:
        """Create a new comment"""
        # Validate post exists and allows comments
        post = session.get(BlogPost, comment_in.post_id)
        if not post or not post.can_be_commented():
            raise HTTPException(
                status_code=400, detail="Post not found or comments not allowed"
            )

        # Validate parent comment if provided
        if comment_in.parent_id:
            parent = session.get(Comment, comment_in.parent_id)
            if not parent or parent.post_id != comment_in.post_id:
                raise HTTPException(status_code=400, detail="Invalid parent comment")

        db_comment = Comment.model_validate(comment_in)
        session.add(db_comment)
        session.commit()
        session.refresh(db_comment)
        return db_comment

    @staticmethod
    def get_comment(*, session: Session, comment_id: uuid.UUID) -> Optional[Comment]:
        """Get a comment by ID"""
        return session.get(Comment, comment_id)

    @staticmethod
    def get_comments(
        *,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[CommentFilter] = None,
        approved_only: bool = False,
    ) -> list[Comment]:
        """Get comments with filtering"""
        statement = select(Comment)

        # Base filters
        if approved_only:
            statement = statement.where(
                Comment.status == CommentStatus.APPROVED, Comment.is_active == True
            )
        else:
            statement = statement.where(Comment.is_active == True)

        # Apply additional filters
        if filters:
            if filters.status:
                statement = statement.where(Comment.status == filters.status)
            if filters.post_id:
                statement = statement.where(Comment.post_id == filters.post_id)
            if filters.author_email:
                statement = statement.where(
                    Comment.author_email == filters.author_email
                )

        statement = (
            statement.order_by(desc(Comment.created_at)).offset(skip).limit(limit)
        )
        return list(session.exec(statement).all())

    @staticmethod
    def moderate_comment(
        *,
        session: Session,
        comment_id: uuid.UUID,
        status: CommentStatus,
        moderated_by_id: uuid.UUID,
    ) -> Optional[Comment]:
        """Moderate a comment (approve/reject)"""
        comment = session.get(Comment, comment_id)
        if not comment:
            return None

        comment.status = status
        comment.moderated_at = datetime.now()
        comment.moderated_by_id = moderated_by_id
        comment.updated_at = datetime.now()

        session.add(comment)
        session.commit()
        session.refresh(comment)
        return comment

    @staticmethod
    def delete_comment(*, session: Session, comment_id: uuid.UUID) -> bool:
        """Soft delete a comment"""
        comment = session.get(Comment, comment_id)
        if not comment:
            return False

        comment.is_active = False
        comment.updated_at = datetime.now()
        session.add(comment)
        session.commit()
        return True


class BlogStatsService:
    """Service for blog statistics"""

    @staticmethod
    def get_blog_stats(*, session: Session) -> BlogStats:
        """Get comprehensive blog statistics"""
        total_posts = session.exec(select(func.count(BlogPost.id))).first() or 0

        published_posts = (
            session.exec(
                select(func.count(BlogPost.id)).where(
                    BlogPost.status == PostStatus.PUBLISHED, BlogPost.is_active == True
                )
            ).first()
            or 0
        )

        draft_posts = (
            session.exec(
                select(func.count(BlogPost.id)).where(
                    BlogPost.status == PostStatus.DRAFT, BlogPost.is_active == True
                )
            ).first()
            or 0
        )

        total_comments = session.exec(select(func.count(Comment.id))).first() or 0

        pending_comments = (
            session.exec(
                select(func.count(Comment.id)).where(
                    Comment.status == CommentStatus.PENDING, Comment.is_active == True
                )
            ).first()
            or 0
        )

        total_categories = (
            session.exec(
                select(func.count(Category.id)).where(Category.is_active == True)
            ).first()
            or 0
        )

        total_tags = (
            session.exec(
                select(func.count(Tag.id)).where(Tag.is_active == True)
            ).first()
            or 0
        )

        total_views = (
            session.exec(
                select(func.sum(BlogPost.view_count)).where(BlogPost.is_active == True)
            ).first()
            or 0
        )

        return BlogStats(
            total_posts=total_posts,
            published_posts=published_posts,
            draft_posts=draft_posts,
            total_comments=total_comments,
            pending_comments=pending_comments,
            total_categories=total_categories,
            total_tags=total_tags,
            total_views=total_views,
        )
