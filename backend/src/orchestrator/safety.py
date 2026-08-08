"""Content safety and professional guardrails agent."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SafetyAgent:
    """Agent responsible for content safety and professional guardrails.

    Validates topics before generation starts.
    """

    def __init__(self, api_key: str, provider: str = "huggingface", model: Optional[str] = None) -> None:
        from aphra_blogger.llm.factory import create_llm_provider

        self.llm = create_llm_provider(provider=provider, api_key=api_key, model=model)

    def validate_topic(self, topic: str) -> Dict[str, Any]:
        """Validates a topic against professional and safety standards.

        Returns a dict with 'safe': bool and 'reason': str.
        """
        prompt = f"""
        Actúa como un Moderador de Contenido Profesional para un blog de tecnología y estilo de vida.
        Tu tarea es evaluar si el siguiente TEMA es apropiado para ser publicado.
        
        TEMA: "{topic}"
        
        CRITERIOS DE RECHAZO (Responde 'FALSE' si cumple alguno):
        1. Contenido obsceno, sexualmente explícito o pornográfico.
        2. Discurso de odio, discriminación o violencia.
        3. Promoción de actividades ilegales.
        4. Spam, estafas o contenido malicioso.
        5. Temas que darían una imagen poco profesional o dañina para el proyecto (ej. política extrema, insultos).
        
        Responde ÚNICAMENTE en formato JSON:
        {{
          "safe": boolean,
          "reason": "breve explicación en español si es inseguro, de lo contrario 'OK'"
        }}
        """

        try:
            response = self.llm.generate(prompt)
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return data

            if "true" in response.lower() and "false" not in response.lower():
                return {"safe": True, "reason": "OK"}
            return {"safe": False, "reason": "No se pudo validar la seguridad del tema."}

        except Exception as e:
            logger.error("Error in SafetyAgent: %s", e)
            return {"safe": False, "reason": f"Error técnico en validación: {str(e)}"}
