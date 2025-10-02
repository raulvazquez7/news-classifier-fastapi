# 🗺️ ROADMAP - Hacker News API with AI Classification

**Proyecto:** Flanks AI Engineer Technical Test  
**Objetivo:** Crear una API asíncrona que scrapea Hacker News y clasifica contenido con OpenAI  
**Fecha inicio:** 1 de Octubre, 2025

---

## 📚 Índice

1. [Stack Tecnológico](#-stack-tecnológico)
2. [Decisiones Técnicas Clave](#-decisiones-técnicas-clave)
3. [Estructura del Proyecto](#-estructura-del-proyecto)
4. [Fases de Desarrollo](#-fases-de-desarrollo)
5. [Notas Importantes](#-notas-importantes)

---

## 🛠 Stack Tecnológico

### Core
- **Python:** 3.12+ (actualmente 3.13)
- **Framework:** FastAPI (async nativo, Pydantic, OpenAPI docs automática)
- **HTTP Client:** httpx (async, para scraping)
- **Parser HTML:** BeautifulSoup4 + lxml (rápido y robusto)

### AI & Validation
- **OpenAI:** Responses API (`/v1/responses`) con Structured Outputs
- **Validation:** Pydantic v2 (con `Literal`, `Field`, type safety)

### Testing
- **Framework:** pytest + pytest-asyncio
- **Mocking:** pytest-mock, httpx-mock
- **Coverage:** pytest-cov

### DevOps
- **Containerización:** Docker + Docker Compose
- **Variables de entorno:** python-dotenv
- **Logging:** structlog o logging estándar
- **Linting:** ruff o black + isort

---

## 🎯 Decisiones Técnicas Clave

### 1. OpenAI Responses API (No Chat Completions)

**Endpoint:** `POST https://api.openai.com/v1/responses`

**¿Por qué?**
- Structured Outputs nativos (garantía de formato)
- Mejor integración con Pydantic models
- Soporte avanzado para tool calling y workflows
- Production-ready desde el diseño

**Implementación:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class StoryClassification(BaseModel):
    category: Literal["ai-ml", "programming", "security", ...]
    intent: Literal["news", "discussion", "tutorial", ...]
    tags: list[str] = Field(min_length=1, max_length=6)
    confidence: int = Field(ge=0, le=100)
    reason_brief: str = Field(max_length=160)

# En la llamada:
response = client.responses.create(
    model="gpt-4o-mini",
    input=prompt_from_yaml,
    response_format=StoryClassification
)
```

**Referencias:**
- Documentación oficial: https://platform.openai.com/docs/api-reference/responses/create
- Documentación del Lead (proporcionada por usuario)

---

### 2. Sistema de Caché Incremental (CacheManager)

**Requisito:** Caché in-memory, no persistente, incremental

**Implementación:** Clase `CacheManager` con lógica clara y testeable

```python
class CacheManager:
    """
    Gestiona caché incremental de páginas scrapeadas.
    
    Ejemplos:
    - Pedir /1 → scrapea página 1
    - Pedir /2 → solo scrapea página 2 (1 ya está en caché)
    - Pedir /4 → scrapea páginas 3 y 4 (1 y 2 ya en caché)
    """
    def __init__(self):
        self._cache: dict[int, list[Story]] = {}
    
    def get_cached_pages(self) -> set[int]:
        """Devuelve qué páginas ya están en caché"""
        
    def get_missing_pages(self, requested: int) -> list[int]:
        """Calcula qué páginas faltan para llegar a 'requested'"""
        
    def add_page(self, page_num: int, stories: list[Story]):
        """Añade una página al caché"""
        
    def get_stories_up_to(self, page: int) -> list[Story]:
        """Devuelve todas las stories hasta la página N"""
        
    def clear(self):
        """Limpia el caché (útil para testing)"""
```

**Ventajas:**
- ✅ Testeable (cada método hace una cosa)
- ✅ Production-ready (claro, mantenible)
- ✅ No overkill (no usa Redis/Memcached innecesariamente)

---

### 3. Prompts Estructurados en YAML

**Ubicación:** `config/prompts.yaml`

**¿Por qué YAML?**
- Separación de concerns (código vs prompts)
- Fácil de modificar sin tocar código
- Versionable en Git
- Permite experimentar con prompts sin rebuilds

**Estructura ejemplo:**
```yaml
classification:
  system: |
    Eres un experto clasificador de noticias técnicas de Hacker News.
    Tu tarea es analizar el título, URL, points y comments de una noticia
    y clasificarla según categoría, intent, tags relevantes y confianza.
    
  user_template: |
    Clasifica la siguiente noticia de Hacker News:
    
    Título: {title}
    URL: {url}
    Points: {points}
    Comments: {comments}
    
    Devuelve la clasificación siguiendo el schema proporcionado.
```

---

### 4. Testing Strategy

#### Unit Tests (Mock HTML, Mock OpenAI)
- Scrapear HTML estático (fixtures)
- No golpear HN real en cada test
- Mock respuestas de OpenAI (no gastar tokens)

#### Integration Tests
- Endpoints de FastAPI con TestClient
- Cache behavior (incremental logic)
- Error handling (rate limits, timeouts)

#### Manual/E2E Tests
- Contra HN real (ocasionalmente)
- Validar OpenAI real (pre-deployment)

**Comando tests:**
```bash
pytest tests/ -v --cov=src --cov-report=html
```

---

### 5. Exception Handling & Recovery

**Principios:**
- Excepciones custom por módulo
- Retry logic con backoff exponencial
- Graceful degradation (no crashear, devolver errores claros)
- Logging estructurado

**Ejemplos:**
```python
# Excepciones custom
class HNScraperError(Exception):
    """Error base para scraping"""

class HNPageNotFoundError(HNScraperError):
    """Página no encontrada"""

class HNParseError(HNScraperError):
    """Error parseando HTML"""

class AIClassificationError(Exception):
    """Error clasificando con OpenAI"""

# Retry logic
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(httpx.TimeoutException)
)
async def fetch_page(url: str) -> str:
    ...
```

---

## 📁 Estructura del Proyecto

```
HackernewsAPItest/
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point FastAPI
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # Endpoints: /, /{number}, /ai/classify/{pages}
│   │   └── dependencies.py        # Dependency injection (cache, clients)
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── hn_scraper.py          # Lógica de scraping HN
│   │   └── parser.py              # Parseo HTML → Story model
│   ├── cache/
│   │   ├── __init__.py
│   │   └── manager.py             # CacheManager class
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── classifier.py          # OpenAI Responses API integration
│   │   └── prompts.py             # Carga prompts desde YAML
│   ├── models/
│   │   ├── __init__.py
│   │   ├── story.py               # Story Pydantic model
│   │   ├── classification.py     # StoryClassification Pydantic model
│   │   └── responses.py           # API response models
│   └── exceptions.py              # Custom exceptions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures compartidos
│   ├── fixtures/
│   │   └── hn_page_sample.html    # HTML estático para tests
│   ├── unit/
│   │   ├── test_scraper.py
│   │   ├── test_cache.py
│   │   └── test_classifier.py
│   └── integration/
│       └── test_api.py            # Tests de endpoints
├── config/
│   └── prompts.yaml               # Prompts estructurados
├── docker/
│   └── Dockerfile
├── .env.example                   # Template de variables
├── .env                           # Variables reales (no en Git)
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml                 # Config de linting/formatting
├── pytest.ini                     # Config de pytest
├── README.md                      # Documentación final del proyecto
└── ROADMAP.md                     # Este archivo
```

---


---

## 🚀 Fases de Desarrollo

### **FASE 0: Setup Inicial** ⏳

- [ ] Crear estructura de directorios
- [ ] Configurar `.gitignore` (venv, .env, __pycache__, .pytest_cache, htmlcov, etc.)
- [ ] Crear `.env.example` con variables necesarias
- [ ] Crear `requirements.txt` base
- [ ] Configurar `pyproject.toml` (black, isort, ruff)
- [ ] Configurar `pytest.ini`
- [ ] Git: Commit inicial con estructura

**Duración estimada:** 30 min

---

### **FASE 1: Modelos Base (Pydantic)** 🔨

#### Objetivos:
- Definir modelos de datos con Pydantic
- Type safety desde el principio
- Validaciones robustas

#### Tareas:
- [ ] `models/story.py`: Modelo `Story` con campos del README
  ```python
  class Story(BaseModel):
      title: str
      url: str | None  # Ask HN no tiene URL
      points: int
      sent_by: str
      published: str
      comments: int
  ```
- [ ] `models/classification.py`: Modelo `StoryClassification` con Literals
  ```python
  class StoryClassification(BaseModel):
      category: Literal["ai-ml", "programming", ...]
      intent: Literal["news", "discussion", ...]
      tags: list[str] = Field(min_length=1, max_length=6)
      confidence: int = Field(ge=0, le=100)
      reason_brief: str = Field(max_length=160)
  ```
- [ ] `models/responses.py`: Modelos de respuesta de API
  ```python
  class ClassificationResponse(BaseModel):
      model: str
      total: int
      schema_version: str
      items: list[StoryClassification]
  ```
- [ ] Tests unitarios de validación Pydantic
- [ ] Git: Commit "feat: add Pydantic models"

**Duración estimada:** 45 min

---

### **FASE 2: Scraper (Core)** 🕷️

#### Objetivos:
- Scrapear HN de manera robusta
- Manejo de edge cases (Ask HN, stories sin URL, etc.)
- Fully async

#### Tareas:
- [ ] Analizar HTML de HN (identificar estructura, clases CSS)
- [ ] Crear fixture `tests/fixtures/hn_page_sample.html` (guardar HTML real)
- [ ] `scrapers/parser.py`: Parsear HTML → lista de `Story`
  - Manejo de casos: Ask HN, Show HN, stories nuevos sin points/comments
- [ ] Tests unitarios del parser (usando fixture)
- [ ] `scrapers/hn_scraper.py`: 
  - `async def fetch_page(page_num: int) -> str` (httpx)
  - `async def scrape_page(page_num: int) -> list[Story]` (fetch + parse)
- [ ] Tests del scraper (mock httpx responses)
- [ ] Retry logic con `tenacity` para robustez
- [ ] Exception handling custom (`HNScraperError`, etc.)
- [ ] Git: Commit "feat: implement HN scraper with retry logic"

**Duración estimada:** 2 horas

---

### **FASE 3: Cache Manager** 💾

#### Objetivos:
- Caché incremental in-memory
- Lógica clara y testeable
- No persistente (dict en memoria)

#### Tareas:
- [ ] `cache/manager.py`: Implementar clase `CacheManager`
  - `get_cached_pages() -> set[int]`
  - `get_missing_pages(requested: int) -> list[int]`
  - `add_page(page_num: int, stories: list[Story])`
  - `get_stories_up_to(page: int) -> list[Story]`
  - `clear()`
- [ ] Tests unitarios exhaustivos:
  - Caché vacío → pedir página 1
  - Caché con página 1 → pedir página 2 (solo scrapea 2)
  - Caché con páginas 1,2 → pedir página 4 (scrapea 3,4)
  - Edge cases (pedir página menor a la máxima en caché)
- [ ] Git: Commit "feat: implement incremental cache manager"

**Duración estimada:** 1.5 horas

---

### **FASE 4: FastAPI Endpoints (Sin AI)** 🚀

#### Objetivos:
- Endpoints `/` y `/{number}` funcionales
- Integración scraper + cache
- Tests de integración

#### Tareas:
- [ ] `main.py`: Setup FastAPI app
  - CORS si es necesario
  - Exception handlers globales
  - Health check endpoint `/health`
- [ ] `api/dependencies.py`: Dependency injection
  ```python
  def get_cache_manager() -> CacheManager:
      return cache_manager  # Singleton global
  ```
- [ ] `api/routes.py`: Implementar endpoints
  - `GET /` → redirige a `/1`
  - `GET /{number}` → scrapea + cache + retorna lista de Story
- [ ] Tests de integración con `TestClient`
  - Mock scraper para no golpear HN
  - Validar comportamiento del caché
- [ ] Logging estructurado (INFO, ERROR)
- [ ] Git: Commit "feat: implement FastAPI endpoints with caching"

**Testing manual:**
```bash
uvicorn src.main:app --reload
curl localhost:8000/1 | jq
```

**Duración estimada:** 2 horas

---

### **FASE 5: OpenAI Integration** 🤖

#### Objetivos:
- Integrar Responses API de OpenAI
- Structured Outputs con Pydantic
- Prompts desde YAML

#### Tareas:
- [ ] `config/prompts.yaml`: Definir prompts de clasificación
- [ ] `ai/prompts.py`: Cargar prompts desde YAML
  ```python
  def get_classification_prompt(story: Story) -> str:
      template = load_yaml("config/prompts.yaml")["classification"]["user_template"]
      return template.format(title=story.title, url=story.url, ...)
  ```
- [ ] `ai/classifier.py`: Implementar clasificación
  ```python
  async def classify_stories(
      stories: list[Story],
      model: str = "gpt-4o-mini"
  ) -> ClassificationResponse:
      # Tomar solo los primeros 5
      # Llamar a Responses API con Structured Outputs
      # Retornar ClassificationResponse
  ```
- [ ] Tests unitarios (mock respuesta de OpenAI)
- [ ] Manejo de errores:
  - Rate limits → retry con backoff
  - API errors → retornar error claro
  - Timeout → configurar timeout apropiado
- [ ] Git: Commit "feat: integrate OpenAI Responses API"

**Duración estimada:** 2.5 horas

---

### **FASE 6: Endpoint AI Classification** 🧠

#### Objetivos:
- Endpoint `/ai/classify/{pages}` funcional
- Integración completa: scraper + cache + OpenAI

#### Tareas:
- [ ] `api/routes.py`: Implementar endpoint `/ai/classify/{pages}`
  - Usar cache para obtener stories (no re-scrapear si ya está)
  - Clasificar primeros 5 items
  - Retornar `ClassificationResponse`
- [ ] Tests de integración
  - Mock OpenAI responses
  - Validar que usa caché correctamente
- [ ] Documentación OpenAPI (docstrings en endpoint)
- [ ] Git: Commit "feat: implement AI classification endpoint"

**Testing manual:**
```bash
curl localhost:8000/ai/classify/1 | jq
```

**Duración estimada:** 1.5 horas

---

### **FASE 7: Docker & Docker Compose** 🐳

#### Objetivos:
- Aplicación dockerizada
- Runnable con `docker compose up -d`
- Puerto 3000 (según README)

#### Tareas:
- [ ] `docker/Dockerfile`:
  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt
  COPY src/ src/
  COPY config/ config/
  CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3000"]
  ```
- [ ] `docker-compose.yml`:
  ```yaml
  version: "3.8"
  services:
    api:
      build:
        context: .
        dockerfile: docker/Dockerfile
      ports:
        - "3000:3000"
      env_file:
        - .env
      restart: unless-stopped
  ```
- [ ] `.dockerignore` (excluir venv, __pycache__, etc.)
- [ ] Probar build y run
- [ ] Git: Commit "feat: add Docker and Docker Compose"

**Testing:**
```bash
docker compose up -d
curl -s localhost:3000 | jq
curl -s localhost:3000/2 | jq | wc -l  # ~60
curl -s localhost:3000/ai/classify/1 | jq
```

**Duración estimada:** 1 hora

---

### **FASE 8: Testing Completo** ✅

#### Objetivos:
- Cobertura de tests >80%
- Tests unit + integration robustos
- CI/CD ready

#### Tareas:
- [ ] Revisar cobertura actual: `pytest --cov=src --cov-report=html`
- [ ] Añadir tests faltantes (edge cases, error handling)
- [ ] Tests de integración E2E (opcional, contra HN real)
- [ ] Documentar cómo correr tests en README
- [ ] Git: Commit "test: improve test coverage"

**Duración estimada:** 2 horas

---

### **FASE 9: Documentation & Polish** 📝

#### Objetivos:
- README completo y profesional
- Código limpio y comentado
- Git history limpio

#### Tareas:
- [ ] Actualizar `README.md`:
  - Descripción del proyecto
  - Arquitectura (diagrama simple)
  - Cómo correr localmente
  - Cómo correr con Docker
  - Cómo correr tests
  - Variables de entorno necesarias
  - Endpoints disponibles
  - Decisiones técnicas clave
- [ ] Revisar código:
  - Comentarios donde sea necesario
  - Docstrings en funciones públicas
  - Type hints consistentes
- [ ] Revisar commits:
  - Mensajes claros y estructurados
  - Squash si es necesario
- [ ] Linting final: `ruff check . --fix`
- [ ] Formatting final: `black .`
- [ ] Git: Commit "docs: complete README and code documentation"

**Duración estimada:** 1.5 horas

---

### **FASE 10: Final Review & Delivery** 🎉

#### Objetivos:
- Revisión completa pre-entrega
- Todo funciona según specs
- Repo listo para compartir

#### Checklist Final:
- [ ] ✅ API funciona localmente (`uvicorn`)
- [ ] ✅ API funciona con Docker Compose (`docker compose up -d`)
- [ ] ✅ Endpoint `/` retorna 30 stories
- [ ] ✅ Endpoint `/2` retorna 60 stories
- [ ] ✅ Endpoint `/ai/classify/1` retorna 5 clasificaciones
- [ ] ✅ Caché funciona (validar con logs que no re-scrapea)
- [ ] ✅ Tests pasan: `pytest tests/ -v`
- [ ] ✅ Cobertura >80%: `pytest --cov=src`
- [ ] ✅ README completo y claro
- [ ] ✅ `.env` no está en Git (solo `.env.example`)
- [ ] ✅ Commits limpios y estructurados
- [ ] ✅ No hay TODOs ni código comentado innecesario
- [ ] ✅ Repo privado configurado
- [ ] ✅ Invitar al Lead de Flanks al repo

**Duración estimada:** 1 hora

---

## 📊 Resumen Temporal

| Fase | Descripción | Duración |
|------|-------------|----------|
| 0 | Setup Inicial | 30 min |
| 1 | Modelos Base | 45 min |
| 2 | Scraper | 2h |
| 3 | Cache Manager | 1.5h |
| 4 | FastAPI Endpoints | 2h |
| 5 | OpenAI Integration | 2.5h |
| 6 | AI Classification Endpoint | 1.5h |
| 7 | Docker & Docker Compose | 1h |
| 8 | Testing Completo | 2h |
| 9 | Documentation & Polish | 1.5h |
| 10 | Final Review | 1h |
| **TOTAL** | | **~16 horas** |

> **Nota:** Tiempos estimados para desarrollo learning-oriented. Si ya dominas el stack, puede reducirse a ~8-10 horas.

---

## 📌 Notas Importantes

### 1. OpenAI Responses API - Recursos

- **Documentación oficial:** https://platform.openai.com/docs/api-reference/responses/create
- **Structured Outputs:** https://platform.openai.com/docs/guides/structured-outputs
- **Librería Python:** Asegurarse de tener `openai>=2.0.0`

**Verificar versión:**
```bash
pip show openai
```

### 2. Rate Limits y Costes

- **gpt-4o-mini:** ~$0.00015/1K tokens (input) + ~$0.0006/1K tokens (output)
- **Estimate por clasificación:** ~100 tokens input + 50 tokens output = ~$0.00006 por story
- **5 stories:** ~$0.0003 por request
- **Rate limit:** Depende del tier de la API key de Flanks

**Implementar:**
- Timeout apropiado (30s)
- Retry logic con backoff exponencial
- Logging de costes (opcional)

### 3. Scraping Best Practices

- **User-Agent:** Usar un User-Agent apropiado
  ```python
  headers = {
      "User-Agent": "HN-API-Test-Bot/1.0 (Educational Purpose)"
  }
  ```
- **Rate limiting:** No hacer más de 1 request/segundo a HN
- **Politeness:** Cachear resultados, no re-scrapear innecesariamente
- **Error handling:** 404, 500, timeouts

### 4. Git Commit Convention

Usar conventional commits:
- `feat:` nueva funcionalidad
- `fix:` bug fix
- `test:` añadir/modificar tests
- `docs:` documentación
- `refactor:` refactorización sin cambio funcional
- `chore:` tareas de mantenimiento

**Ejemplos:**
```bash
git commit -m "feat: implement CacheManager with incremental logic"
git commit -m "test: add unit tests for HN scraper"
git commit -m "docs: update README with Docker instructions"
```

### 5. Variables de Entorno Necesarias

```bash
# .env.example
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
HN_BASE_URL=https://news.ycombinator.com
```

### 6. Edge Cases a Considerar

- **Ask HN:** No tiene URL externa
- **Show HN:** Patrón especial en título
- **Stories nuevos:** Pueden no tener points/comments aún
- **Deleted stories:** Pueden aparecer como [deleted]
- **HN down:** Manejo de timeouts y errores 500

### 7. Testing Strategy Detallada

```python
# tests/conftest.py
@pytest.fixture
def sample_html():
    with open("tests/fixtures/hn_page_sample.html") as f:
        return f.read()

@pytest.fixture
def mock_openai_response():
    return {
        "category": "ai-ml",
        "intent": "news",
        "tags": ["AI", "Machine Learning"],
        "confidence": 85,
        "reason_brief": "Article about AI advancement"
    }

# tests/unit/test_cache.py
def test_cache_incremental_logic():
    cache = CacheManager()
    
    # Pedir página 1
    missing = cache.get_missing_pages(1)
    assert missing == [1]
    
    # Añadir página 1
    cache.add_page(1, [Story(...)])
    
    # Pedir página 2
    missing = cache.get_missing_pages(2)
    assert missing == [2]  # Solo falta la 2
```

---

## 🎯 Criterios de Éxito

Al finalizar, el proyecto debe:

✅ Cumplir 100% de los requisitos del README original  
✅ Código limpio, type-safe, bien estructurado  
✅ Tests con buena cobertura (>80%)  
✅ Dockerizado y fácil de correr  
✅ Documentación clara y completa  
✅ Git history profesional  
✅ Manejo robusto de errores  
✅ Production-ready (logging, retry logic, exception handling)  

**Objetivo:** Que digan "WOW!" 🚀

---

## 📞 Contacto & Dudas

- **Lead AI Flanks:** [pendiente de email]
- **Dudas sobre Responses API:** Preguntar al Lead o consultar docs
- **Deadline:** [pendiente de confirmación]

---

**Última actualización:** 1 de Octubre, 2025  
**Versión:** 1.0  
**Status:** En progreso 🔨