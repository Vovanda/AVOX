from enum import Enum as PyEnum

class RoleType(PyEnum):
    EDITOR = 'editor'
    READER = 'reader'
    CLIENT = 'client'

class SourceType(PyEnum):
    URI = 'URI'
    CONFLUENCE = 'Confluence'
    FILE = 'file'
    TEXT_INPUT = 'text_input'
    WEB_SCRAPING = 'web_scraping'

class AccessLevel(PyEnum):
    PRIVATE = 'private'
    PUBLIC = 'public'
    SHARED = 'shared'
    TEAM = 'team'
    RESTRICTED = 'restricted'

class EmbeddingStatus(PyEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SCHEDULED = 'scheduled'

class DocumentStatus(PyEnum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    DELETED = 'deleted'

class ChunkPriority(PyEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
