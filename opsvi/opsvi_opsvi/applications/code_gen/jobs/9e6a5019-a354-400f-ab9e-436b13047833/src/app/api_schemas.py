"""
Marshmallow schemas for serializing API models.
"""
from marshmallow import Schema, fields


class TagSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class CategorySchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()


class ImageSchema(Schema):
    id = fields.Int()
    url = fields.Str()
    alt_text = fields.Str()


class PostSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    content = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    tags = fields.List(fields.Nested(TagSchema))
    categories = fields.List(fields.Nested(CategorySchema))
    images = fields.List(fields.Nested(ImageSchema))
