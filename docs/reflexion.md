# Reflexión: refactorización asistida por IA

**Nombre:** Hector Ever Alonso Ramirez

Claude Code fue muy útil para entender rápido un código que no conocía: con un solo prompt obtuve el mapa del proyecto, el flujo del menú y una lista de problemas, y con eso armé un plan priorizado por impacto antes de tocar una sola línea.

También aprendí que no se le puede creer todo sin revisar. En dos ocasiones sus propios scripts de comparación estaban mal: uno le daba datos distintos a cada versión, y otro dio un "OK" falso porque ninguna de las dos versiones llegaba a ejecutarse. Además, en una refactorización introdujo una línea demasiado larga que ruff detectó. Sin los tests, el linter y la revisión de los resultados, esos errores habrían pasado.

Lo más valioso fue trabajar con reglas claras en `CLAUDE.md` (no tocar los tests, comportamiento idéntico) y avanzar una refactorización a la vez, validando y haciendo commit en cada paso. Así cada cambio era pequeño y fácil de revisar. También noté que los tests del reto no cubrían el menú, y que validar el comportamiento requirió pruebas adicionales.

Mi conclusión es que la IA acelera mucho el análisis y la ejecución, pero la responsabilidad de validar sigue siendo mía. Me faltó explorar otros modos de Claude Code, como el modo de planificación, y dejé pendientes algunos puntos del plan, como los type hints.
