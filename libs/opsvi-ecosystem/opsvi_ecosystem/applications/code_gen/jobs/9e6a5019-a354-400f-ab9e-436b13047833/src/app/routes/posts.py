"""
Routes for blog post CRUD, image upload, AI-assist, editor UI.
"""
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.forms import ImageUploadForm, PostForm
from app.models import Category, Image, Post, Tag, db
from app.tasks import ai_generate_post_content, generate_alt_text
from app.uploads import images

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


@posts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    form = PostForm()
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    if form.validate_on_submit():
        content = form.content.data
        # AI Generation
        if form.ai_generate.data:
            ai_result = ai_generate_post_content.delay(
                form.title.data, form.content.data
            )
            flash("AI is generating the post content. Check back later.", "info")
            content = "<p><em>AI is generating your content. Refresh soon.</em></p>"
        post = Post(title=form.title.data, content=content, user_id=current_user.id)
        # Categories and tags
        post.categories = Category.query.filter(
            Category.id.in_(form.categories.data)
        ).all()
        post.tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
        db.session.add(post)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"DB Error: {str(e)}", "danger")
            return redirect(url_for("posts.create_post"))
        flash("Post created. You may now add images.", "success")
        return redirect(url_for("posts.edit_post", post_id=post.id))
    return render_template("posts/edit.html", form=form, editor=True, new_post=True)


@posts_bp.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id and not current_user.is_admin:
        abort(403)
    form = PostForm(obj=post)
    form.categories.choices = [(c.id, c.name) for c in Category.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    # Pre-fill selections
    if request.method == "GET":
        form.categories.data = [cat.id for cat in post.categories]
        form.tags.data = [tag.id for tag in post.tags]
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.categories = Category.query.filter(
            Category.id.in_(form.categories.data)
        ).all()
        post.tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("posts.edit_post", post_id=post.id))
    images = post.images
    image_form = ImageUploadForm()
    return render_template(
        "posts/edit.html",
        form=form,
        post=post,
        images=images,
        image_form=image_form,
        editor=True,
        new_post=False,
    )


@posts_bp.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id and not current_user.is_admin:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("main.homepage"))


@posts_bp.route("/upload_image/<int:post_id>", methods=["POST"])
@login_required
def upload_image(post_id: int):
    post = Post.query.get_or_404(post_id)
    if post.author.id != current_user.id and not current_user.is_admin:
        abort(403)
    form = ImageUploadForm()
    if form.validate_on_submit():
        filename = images.save(form.image.data, folder=str(post_id))
        url = images.url(filename)
        image = Image(filename=filename, post_id=post.id, url=url)
        db.session.add(image)
        db.session.commit()
        # Trigger background task to generate alt text
        generate_alt_text.delay(image.id, url)
        flash("Image uploaded. Alt-text generation in progress.", "success")
    else:
        flash("Image upload failed.", "danger")
    return redirect(url_for("posts.edit_post", post_id=post_id))
