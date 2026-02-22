# 🏎️ ORIÓN - Sim Racing Race Control

**ORIÓN** es un sistema de gestión de tiempos y telemetría en vivo diseñado para competencias de sim racing (específicamente calibrado para **Assetto Corsa**). Este software permite registrar vueltas automáticamente, gestionar una tabla de posiciones (Leaderboard) y visualizar un cronómetro profesional en tiempo real.

Este proyecto fue desarrollado para gestionar eventos de sim racing en la unidad residencial **Orion** en La Estrella, Antioquia.

## 🚀 Características principales

* **Telemetría en Vivo:** Cronómetro en tiempo real conectado directamente a la memoria de Assetto Corsa.
* **Registro Automático:** Captura los tiempos de vuelta al cruzar la meta sin intervención manual.
* **Leaderboard Dinámico:** Clasificación automática basada en el mejor tiempo de cada piloto.
* **Podio Visual:** Visualización destacada de los 3 mejores tiempos de la sesión.
* **Buscador de Pilotos:** Autocompletado para gestionar rápidamente quién está al volante.
* **Diseño Racing:** Interfaz optimizada con fuentes monoespaciadas para evitar el "baile" de números y mejorar la legibilidad.

## 🛠️ Requisitos del Sistema

1.  **Simulador:** Assetto Corsa (PC).
2.  **Lenguaje:** [Python 3.x](https://www.python.org/) instalado.
3.  **Librerías Python:** `websockets`.
    ```bash
    pip install websockets
    ```

## 📂 Estructura del Proyecto

* `index.html`: Interfaz de usuario (Dashboard) construida con HTML5, CSS3 y JS Vanilla.
* `bridge.py`: Script de Python que actúa como puente entre la memoria del juego (Shared Memory) y la interfaz web mediante WebSockets.

## 🏁 Instrucciones de Uso

1.  **Iniciar el Simulador:** Abre Assetto Corsa y entra en pista.
2.  **Ejecutar el Bridge:**
    ```bash
    python bridge.py
    ```
3.  **Abrir la Interfaz:** Abre el archivo `index.html` en tu navegador (preferiblemente Chrome o Edge).
4.  **Configurar Piloto:** Selecciona o agrega un piloto en el panel lateral.
5.  **¡A correr!:** Los tiempos empezarán a reflejarse automáticamente en el cronómetro verde y se guardarán al completar cada vuelta.

## 🔧 Detalles Técnicos (QA)

* **Offsets de Memoria:** El sistema utiliza los offsets `132` (vueltas), `140` (tiempo actual) y `144` (último tiempo) de la memoria compartida `acpmf_graphics`.
* **Comunicación:** Protocolo WebSocket en el puerto `8765`.
* **Estabilidad Visual:** Implementación de `font-variant-numeric: tabular-nums` para garantizar que los caracteres del cronómetro mantengan un ancho fijo durante la ejecución.

## 📋 Pendientes
- [ ] Eliminar registros de BD


---
Desarrollado por **Juanes** - *Sim Racer & QA Engineer*
