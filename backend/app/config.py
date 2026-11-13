from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    proveedor_llm: str = "heroku"
    inference_url: str = ""
    inference_key: str = ""
    inference_model_id: str = ""
    anthropic_api_key: str = ""

    # Prompts y agente
    prompt_version: str = "v1"
    esfuerzo_llm: str = "high"
    max_pasos_agente: int = 20
    timeout_llm_s: int = 120
    max_tokens_por_caso: int = 200_000
    max_tokens_dia: int = 2_000_000
    precio_token_entrada_usd: float = 0.0
    precio_token_salida_usd: float = 0.0

    # Base de datos
    database_url: str = "postgresql://postgres:postgres@db:5432/suscriptor"

    # Sesión
    secret_key: str = "cambiar-en-produccion"

    # Archivos
    tamano_max_archivo_mb: int = 25
    max_archivos_por_carga: int = 20

    # Negocio
    tasa_iva: str = "0.19"
    ruta_tarifario: str = "datos/ejemplo/tarifario.xlsx"

    # Seguridad
    origenes_cors: str = "http://localhost:5173"
    clave_evaluacion: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
