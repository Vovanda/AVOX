from enum import Enum as PyEnum

class AuthProvider(PyEnum):
    INTERNAL = 'internal'
    VK = 'vk'
    YANDEX = 'yandex'
    GOOGLE = 'google'

class UserType(PyEnum):  # Тип пользователя (внешний/внутренний)
    UNKNOWN = 'unknown'
    INTERNAL = 'internal'  # Сотрудник
    EXTERNAL = 'external'  # Клиент
    SYSTEM = 'system'      # Технический аккаунт

class UserRole(PyEnum):
    BASE = 'base'             # Базовые права
    MANAGER = 'manager'       # Управление контентом
    MODERATOR = 'moderator'   # Одобрение PUBLIC контента
    ADMIN = 'admin'           # Полные права
    API = 'api'               # Доступ только к API

class DocAccessRole(PyEnum):  # Уровни доступа
    UNKNOWN = 'unknown'
    READER = 'reader'           # Чтение документа
    CONTRIBUTOR = 'contributor' # Может предлагать правки
    EDITOR = 'editor'           # Редактирование

class SourceType(PyEnum):
    URI = 'URI'
    CONFLUENCE = 'Confluence'
    FILE = 'file'
    TEXT_INPUT = 'text_input'
    WEB_SCRAPING = 'web_scraping'

class DocumentStatus(PyEnum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    DELETED = 'deleted'

class DocAccessLevel(PyEnum):
    RESTRICTED = 'restricted'   # Персональный доступ (через AccessGrant)
    INTERNAL = 'internal'       # Только для сотрудников компании
    PUBLIC = 'public'           # Виден всем (но создавать могут только админы/доверенные редакторы)

class EmbeddingStatus(PyEnum):
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SCHEDULED = 'scheduled'