from marshmallow import Schema, fields, validate, ValidationError

class VisitItemSchema(Schema):
    id = fields.Str(required=True)
    user_id = fields.Str(required=True, validate=validate.Regexp(r'^uuid-[^-]+-[^-]+-[^-]+-[^-]+$'))
    visitTime = fields.Decimal(required=True)
    domain = fields.Str(required=True)
    favourite = fields.Bool(required=True, default=False)
    hidden = fields.Bool(required=True, default=False)
    url = fields.Url(required=True)
    category = fields.Str()
    category_description = fields.Str()
    category_group = fields.Str()
    isLocal = fields.Bool()
    lastVisitTime = fields.Decimal()
    title = fields.Str()
    transition = fields.Str()
    typedCount = fields.Int()
    visitCount = fields.Int()
    visitId = fields.Str()

# Test with the provided data
# data = {
#     "user_id": "uuid-uuid-uuid-uuid",
#     "visitTime": 1687511286634.651,
#     "category": "Web-based Applications",
#     "category_description": "Sites that mimic desktop applications such as word processing, spreadsheets, and slide-show presentations.",
#     "category_group": "General Interest - Business",
#     "domain": "docs.google.com",
#     "favourite": true,
#     "hidden": false,
#     "id": "216841",
#     "isLocal": true,
#     "lastVisitTime": 1687511292617.1628,
#     "referringVisitId": "0",
#     "title": "KPIs for kleo network - Google Docs",
#     "transition": "auto_toplevel",
#     "typedCount": 0,
#     "url": "https://docs.google.com/document/d/1lefVLSa8nrIr5LCQOBrC3MaKDYxhfEiv_4wKhSAuEk8/edit?usp=drivesdk",
#     "visitCount": 2,
#     "visitId": "680548"
# }

# schema = VisitItemSchema()
# validated_data = schema.load(data)

# print(validated_data)
