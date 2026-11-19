# Esqueleto del informe (20 % de la nota)

Sigue exactamente los ítems de la rúbrica como secciones. Debajo de cada uno: qué poner y qué parte del proyecto lo respalda.

## D1 · Portada y resumen (1 %)
Título, nombre, curso, fecha. Resumen de 120–150 palabras: problema, solución (ESP32 en Wokwi + MQTT + Streamlit), modalidades usadas y resultado principal.

## D2 · Introducción, problema y objetivos (2 %)
- **Problema:** el riego, la ventilación y la iluminación de un invernadero suelen hacerse sin datos en tiempo real, con pérdidas de agua y de cultivo.
- **Objetivo general:** desarrollar una aplicación multimodal que monitoree y controle un invernadero simulado.
- **Objetivos específicos:** simular el hardware en Wokwi; comunicar Wokwi y Streamlit por MQTT en ambos sentidos; ofrecer dos ambientes con al menos tres modalidades; validar con pruebas.

## D3 · Marco teórico (2 %)
IoT y MQTT (publicación/suscripción, QoS, retención, Last Will); ESP32 y sensores (DHT22, humedad de suelo, LDR); interfaces multimodales; control con histéresis; Streamlit; análisis de color en espacio HSV. Cita fuentes reales (documentación de MQTT.org, Espressif, Streamlit, Wokwi).

## D4 · Requerimientos y casos de uso (2 %)
Tabla de requerimientos funcionales (RF1 monitorear sensores, RF2 controlar actuadores, RF3 comandos de voz/texto, RF4 umbrales, RF5 diagnóstico por imagen) y no funcionales (latencia < 3 s, indicador de conexión, pruebas automáticas). Casos de uso: *Operador enciende riego por voz*, *Agrónomo ajusta umbrales*, *Agrónomo diagnostica una planta*.

## D5 · Arquitectura del sistema (3 %)
Diagrama de la arquitectura (el del README), tabla de topics y formato JSON, diagrama de secuencia de un comando (voz → intérprete → MQTT → ESP32 → confirmación). Justifica MQTT frente a HTTP.

## D6 · Hardware simulado en Wokwi (3 %)
Captura del circuito, tabla de pines (DHT22→15, suelo→34, LDR→35, bomba→26, lámpara→27, servo→13), descripción del firmware: lectura, lógica automática con histéresis, corte de seguridad, callback de comandos.

## D7 · Aplicación Streamlit (3 %)
Capturas de cada página, explicación del puente MQTT con hilo propio y `st.cache_resource`, actualización con `st.fragment(run_every=2)`, intérprete de comandos, análisis de imagen.

## D8 · Pruebas y resultados (2 %)
Resultado de `pytest` (35 pruebas), pruebas manuales con Wokwi (tabla: acción → resultado esperado → resultado obtenido), latencia observada, limitaciones encontradas.

## D9 · Conclusiones y trabajo futuro (1 %)
Qué se logró y qué aprendiste. Futuro: hardware real, broker propio con TLS y autenticación, base de datos histórica, modelo de visión entrenado.

## D10 · Referencias, anexos y redacción (1 %)
Referencias en un formato consistente (APA), anexos con código clave y enlace al repositorio. Revisa ortografía.
