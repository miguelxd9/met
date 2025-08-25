"""
Modelos de datos para la API de Bitbucket

Estos modelos representan las estructuras de datos que devuelve la API
de Bitbucket y se utilizan para tipado y validación
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class BitbucketUser(BaseModel):
    """Modelo para usuario de Bitbucket"""
    username: str
    display_name: str
    uuid: str
    links: Optional[Dict[str, Any]] = None
    type: str = "user"


class BitbucketWorkspace(BaseModel):
    """Modelo para workspace de Bitbucket"""
    uuid: str
    slug: str
    name: str
    is_private: bool = True
    description: Optional[str] = None
    type: str = "workspace"
    links: Optional[Dict[str, Any]] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None


class BitbucketProject(BaseModel):
    """Modelo para proyecto de Bitbucket"""
    uuid: str
    key: str
    name: str
    description: Optional[str] = None
    is_private: bool = True
    type: str = "project"
    links: Optional[Dict[str, Any]] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None
    owner: Optional[BitbucketUser] = None


class BitbucketRepository(BaseModel):
    """Modelo para repositorio de Bitbucket"""
    uuid: str
    slug: str
    name: str
    description: Optional[str] = None
    is_private: bool = True
    language: Optional[str] = None
    type: str = "repository"
    links: Optional[Dict[str, Any]] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None
    size: Optional[int] = None
    owner: Optional[BitbucketUser] = None
    project: Optional[BitbucketProject] = None
    workspace: Optional[BitbucketWorkspace] = None
    
    # Campos de métricas
    commits_count: Optional[int] = None
    branches_count: Optional[int] = None
    tags_count: Optional[int] = None
    pull_requests_count: Optional[int] = None
    open_pull_requests_count: Optional[int] = None
    closed_pull_requests_count: Optional[int] = None


class BitbucketCommit(BaseModel):
    """Modelo para commit de Bitbucket"""
    hash: str
    id: str
    message: str
    type: str = "commit"
    links: Optional[Dict[str, Any]] = None
    date: str
    author_date: Optional[str] = None
    author: Optional[Dict[str, Any]] = None
    parents: Optional[List[Dict[str, Any]]] = None
    
    # Campos de métricas (si están disponibles)
    additions: Optional[int] = None
    deletions: Optional[int] = None
    total_changes: Optional[int] = None
    is_merge_commit: Optional[bool] = None


class BitbucketPullRequest(BaseModel):
    """Modelo para pull request de Bitbucket"""
    id: str
    title: str
    description: Optional[str] = None
    state: str
    type: str = "pullrequest"
    links: Optional[Dict[str, Any]] = None
    created_on: str
    updated_on: str
    closed_on: Optional[str] = None
    merged_on: Optional[str] = None
    author: Optional[BitbucketUser] = None
    source: Optional[Dict[str, Any]] = None
    destination: Optional[Dict[str, Any]] = None
    
    # Campos de métricas (si están disponibles)
    additions: Optional[int] = None
    deletions: Optional[int] = None
    total_changes: Optional[int] = None


class BitbucketBranch(BaseModel):
    """Modelo para branch de Bitbucket"""
    name: str
    type: str = "branch"
    links: Optional[Dict[str, Any]] = None
    target: Optional[Dict[str, Any]] = None


class BitbucketTag(BaseModel):
    """Modelo para tag de Bitbucket"""
    name: str
    type: str = "tag"
    links: Optional[Dict[str, Any]] = None
    target: Optional[Dict[str, Any]] = None


class BitbucketPipeline(BaseModel):
    """Modelo para pipeline de Bitbucket"""
    uuid: str
    type: str = "pipeline"
    state: str
    build_number: int
    created_on: str
    updated_on: str
    target: Optional[Dict[str, Any]] = None


class BitbucketDeployment(BaseModel):
    """Modelo para deployment de Bitbucket"""
    uuid: str
    type: str = "deployment"
    state: str
    name: str
    created_on: str
    updated_on: str
    environment: Optional[Dict[str, Any]] = None


class BitbucketIssue(BaseModel):
    """Modelo para issue de Bitbucket"""
    id: str
    title: str
    description: Optional[str] = None
    state: str
    type: str = "issue"
    links: Optional[Dict[str, Any]] = None
    created_on: str
    updated_on: str
    reporter: Optional[BitbucketUser] = None
    assignee: Optional[BitbucketUser] = None
    priority: Optional[str] = None
    kind: Optional[str] = None


class BitbucketWiki(BaseModel):
    """Modelo para wiki de Bitbucket"""
    name: str
    type: str = "wiki"
    links: Optional[Dict[str, Any]] = None


class BitbucketSnippet(BaseModel):
    """Modelo para snippet de Bitbucket"""
    uuid: str
    title: str
    description: Optional[str] = None
    type: str = "snippet"
    links: Optional[Dict[str, Any]] = None
    created_on: str
    updated_on: str
    owner: Optional[BitbucketUser] = None
    is_private: bool = True


class BitbucketWebhook(BaseModel):
    """Modelo para webhook de Bitbucket"""
    uuid: str
    description: str
    url: str
    type: str = "webhook"
    active: bool = True
    created_on: str
    updated_on: str
    events: List[str] = []


class BitbucketRepositoryPermission(BaseModel):
    """Modelo para permisos de repositorio"""
    type: str
    user: Optional[BitbucketUser] = None
    repository: Optional[BitbucketRepository] = None
    permission: str


class BitbucketGroup(BaseModel):
    """Modelo para grupo de Bitbucket"""
    uuid: str
    name: str
    slug: str
    type: str = "group"
    links: Optional[Dict[str, Any]] = None
    created_on: Optional[str] = None
    updated_on: Optional[str] = None


class BitbucketRepositoryVariable(BaseModel):
    """Modelo para variable de repositorio"""
    uuid: str
    key: str
    value: str
    secured: bool = False
    type: str = "repository_variable"
    created_on: str
    updated_on: str


class BitbucketRepositoryDeploymentKey(BaseModel):
    """Modelo para clave de deployment de repositorio"""
    uuid: str
    key: str
    label: str
    type: str = "deployment_key"
    created_on: str
    updated_on: str


class BitbucketRepositoryHook(BaseModel):
    """Modelo para hook de repositorio"""
    uuid: str
    name: str
    description: Optional[str] = None
    type: str = "repository_hook"
    active: bool = True
    created_on: str
    updated_on: str


class BitbucketRepositorySettings(BaseModel):
    """Modelo para configuración de repositorio"""
    type: str = "repository_settings"
    fork_policy: Optional[str] = None
    language: Optional[str] = None
    has_issues: Optional[bool] = None
    has_wiki: Optional[bool] = None
    size_limit: Optional[int] = None


class BitbucketRepositoryMetrics(BaseModel):
    """Modelo para métricas de repositorio"""
    type: str = "repository_metrics"
    commits_count: int = 0
    branches_count: int = 0
    tags_count: int = 0
    pull_requests_count: int = 0
    open_pull_requests_count: int = 0
    closed_pull_requests_count: int = 0
    size_bytes: int = 0
    last_activity: Optional[str] = None


class BitbucketWorkspaceMetrics(BaseModel):
    """Modelo para métricas de workspace"""
    type: str = "workspace_metrics"
    total_repositories: int = 0
    total_projects: int = 0
    total_members: int = 0
    total_commits: int = 0
    total_pull_requests: int = 0
    last_activity: Optional[str] = None


class BitbucketProjectMetrics(BaseModel):
    """Modelo para métricas de proyecto"""
    type: str = "project_metrics"
    total_repositories: int = 0
    total_commits: int = 0
    total_pull_requests: int = 0
    last_activity: Optional[str] = None


# Modelos para respuestas paginadas
class BitbucketPaginatedResponse(BaseModel):
    """Modelo para respuestas paginadas de Bitbucket"""
    pagelen: int
    size: int
    page: int
    next: Optional[str] = None
    previous: Optional[str] = None
    values: List[Any] = []


class BitbucketWorkspaceListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de workspaces"""
    values: List[BitbucketWorkspace] = []


class BitbucketProjectListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de proyectos"""
    values: List[BitbucketProject] = []


class BitbucketRepositoryListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de repositorios"""
    values: List[BitbucketRepository] = []


class BitbucketCommitListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de commits"""
    values: List[BitbucketCommit] = []


class BitbucketPullRequestListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de pull requests"""
    values: List[BitbucketPullRequest] = []


class BitbucketBranchListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de branches"""
    values: List[BitbucketBranch] = []


class BitbucketTagListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de tags"""
    values: List[BitbucketTag] = []


class BitbucketPipelineListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de pipelines"""
    values: List[BitbucketPipeline] = []


class BitbucketDeploymentListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de deployments"""
    values: List[BitbucketDeployment] = []


class BitbucketIssueListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de issues"""
    values: List[BitbucketIssue] = []


class BitbucketSnippetListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de snippets"""
    values: List[BitbucketSnippet] = []


class BitbucketWebhookListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de webhooks"""
    values: List[BitbucketWebhook] = []


class BitbucketRepositoryPermissionListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de permisos de repositorio"""
    values: List[BitbucketRepositoryPermission] = []


class BitbucketGroupListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de grupos"""
    values: List[BitbucketGroup] = []


class BitbucketRepositoryVariableListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de variables de repositorio"""
    values: List[BitbucketRepositoryVariable] = []


class BitbucketRepositoryDeploymentKeyListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de claves de deployment"""
    values: List[BitbucketRepositoryDeploymentKey] = []


class BitbucketRepositoryHookListResponse(BitbucketPaginatedResponse):
    """Respuesta paginada para lista de hooks de repositorio"""
    values: List[BitbucketRepositoryHook] = []


# Modelos para errores
class BitbucketError(BaseModel):
    """Modelo para errores de la API de Bitbucket"""
    type: str = "error"
    error: Dict[str, Any]
    message: Optional[str] = None


class BitbucketRateLimitError(BitbucketError):
    """Modelo para errores de rate limiting"""
    type: str = "rate_limit_error"
    retry_after: Optional[int] = None
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_time: Optional[str] = None


class BitbucketAuthenticationError(BitbucketError):
    """Modelo para errores de autenticación"""
    type: str = "authentication_error"


class BitbucketAuthorizationError(BitbucketError):
    """Modelo para errores de autorización"""
    type: str = "authorization_error"


class BitbucketNotFoundError(BitbucketError):
    """Modelo para errores de recurso no encontrado"""
    type: str = "not_found_error"


class BitbucketValidationError(BitbucketError):
    """Modelo para errores de validación"""
    type: str = "validation_error"
    fields: Optional[List[str]] = None


class BitbucketServerError(BitbucketError):
    """Modelo para errores del servidor"""
    type: str = "server_error"
    retry_after: Optional[int] = None
