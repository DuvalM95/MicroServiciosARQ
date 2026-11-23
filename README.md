# Sistema de monitorización de residencias

Prototipo Python basado en los diagramas compartidos. Implementa el microservicio de monitorización con arquitectura hexagonal y dominio `SesionMonitoreo`, `LecturaMetrica`, `UmbralSeguridad` y `AnomaliaDetectadaEvent`. El servicio de alertas recibe eventos mediante HTTP.

## Requisitos

Python 3.11 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Ejecutar

### Interfaz gráfica sencilla (recomendado para probar)

Instala los requisitos una vez y ejecuta:

```powershell
python interfaz.py
```

Se abre una ventana para iniciar una sesión, registrar una lectura manual (por ejemplo, frecuencia cardiaca `125`) o simular el sensor. Las anomalías aparecen en la tabla de alertas. Esta demostración funciona en un solo proceso, usa el dominio y caso de uso del microservicio y mantiene los datos en memoria mientras la ventana está abierta. No necesitas iniciar los servicios HTTP para usar la ventana.

### APIs HTTP

En dos terminales, desde esta carpeta:

```powershell
python -m alertas
```

```powershell
python -m monitorizacion
```

La API de monitorización queda en http://localhost:8000 y la de alertas en http://localhost:8001. La documentación interactiva está en `/docs` en cada servicio. Configure `ALERTS_SERVICE_URL` si alertas se ejecuta en otra dirección.

## Flujo rápido

1. `POST /sessions` con `residente_id` y `dispositivo_id` UUID.
2. `POST /sessions/{session_id}/readings` con `{"metrica":"frecuencia_cardiaca","valor":125,"unidad_medida":"lpm"}`.
3. Si la lectura excede el umbral, monitorización publica un evento y alertas lo registra. Consulte `GET http://localhost:8001/alerts`.
4. `POST /sessions/{session_id}/close` cierra la sesión.

También puede usar `POST /sessions/{session_id}/simulate?metrica=frecuencia_cardiaca` para generar una lectura de prueba. Umbrales iniciales demostrativos: frecuencia cardiaca 50–110 lpm, temperatura corporal 35.5–38 °C, humedad 30–70 % y temperatura ambiente 20–28 °C.

## Alcance del prototipo

Repositorios y alertas están en memoria: los datos se pierden al reiniciar. El simulador reemplaza la integración con hardware; publisher HTTP sustituye un bus duradero. Los umbrales son ilustrativos, no criterios clínicos: deben configurarse y validarse con personal responsable antes de cualquier uso real. Se transportan UUID en vez de nombres u otros datos personales.
