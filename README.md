# 🛡️ Hybrid Synthetic Monitoring & Visual Alerting System

[![Synthetic Monitor CI](https://github.com)](https://github.com)

Sistema automatizado de monitoreo sintético híbrido (**API + UI**) y observabilidad continua diseñado bajo estándares de producción. Valida la disponibilidad del backend, mide los tiempos de respuesta (SLA) por cada paso crítico del negocio y captura evidencia ante fallos o degradaciones de rendimiento.

---

## 🏗️ Arquitectura del Sistema

El flujo de monitoreo aísla las fallas de infraestructura antes de consumir recursos de renderizado en navegador:

```text
[Cron / CI Trigger]
        │
        ▼
┌───────────────────┐     Fallo / SLA > Umbral
│ 1. API Health     │ ──────────────────────────┐
│    Check (HTTP)   │                           │
└─────────┬─────────┘                           │
          │ OK (200 + SLA cumplido)             ▼
          ▼                           ┌───────────────────┐
┌───────────────────┐     Fallo / SLA │  Observabilidad   │
│ 2. UI Critical    │ ───────────────►│  • Screenshot PNG │
│    Journey (POM)  │                 │  • Playwright Trace│
└─────────┬─────────┘                 │  • Telegram/Slack │
          │ OK                        └───────────────────┘
          ▼
   [Monitor PASSED]
```

### Stack Tecnológico
* **Lenguaje & Testing:** Python 3.12+, Pytest, Pydantic Settings.
* **Automatización & Telemetría:** Playwright (APIRequestContext + Chromium Headless), `time.perf_counter()`.
* **Contenerización:** Docker (imagen oficial `://microsoft.com` con viewport fijo `1920x1080`).
* **CI/CD & Scheduling:** GitHub Actions (`cron: '0 * * * *'`) con retención de **Artifacts**.

---

## ✨ Características Clave

* **Aislamiento de Capas (API vs. UI):** Verifica el endpoint de salud antes de instanciar el navegador para distinguir rápidamente caídas de servidor de errores de frontend.
* **Control Estricto de SLA:** Mide el tiempo puro de ejecución de cada paso (excluyendo el arranque en frío del navegador) y falla automáticamente si supera el umbral configurado (`SLA_THRESHOLD_SECONDS`).
* **Cero Flakiness:** Implementa el patrón **Page Object Model (POM)** utilizando exclusivamente auto-waiting y aserciones web-first de Playwright (`expect()`), sin pausas fijas (`time.sleep`).
* **Evidencia Automática:** Ante cualquier error funcional o incumplimiento de SLA, genera capturas de pantalla de página completa y trazas interactivas (`trace.zip`) inspeccionables en [Playwright Trace Viewer](https://playwright.dev).

---

## 🚀 Ejecución Local

### 1. Clonar y configurar entorno
```bash
git clone https://github.com
cd synthetic-monitor
cp .env.example .env
```

### 2. Ejecutar con Python
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
pytest
```

### 3. Ejecutar con Docker (Entorno idéntico a CI)
```bash
docker build -t synthetic-monitor .
docker run --rm --env-file .env -v "\${PWD}/artifacts:/app/artifacts" synthetic-monitor
```

---

## ⚙️ Variables de Entorno

| Variable | Descripción | Valor por defecto |
| :--- | :--- | :--- |
| `BASE_URL` | URL base de la aplicación web | `https://saucedemo.com` |
| `API_HEALTH_ENDPOINT` | Endpoint de verificación previa | `https://saucedemo.com` |
| `SLA_THRESHOLD_SECONDS` | Tiempo máximo permitido por paso (segundos) | `3.0` |
| `HEADLESS` | Ejecución sin interfaz gráfica | `true` |
| `ALERT_ENABLED` | Activa notificaciones vía webhook | `false` |
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram (opcional) | - |
| `TELEGRAM_CHAT_ID` | ID del chat destino (opcional) | - |
