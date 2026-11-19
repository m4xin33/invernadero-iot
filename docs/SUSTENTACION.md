# Guía de sustentación (20 % de la nota)

## Demostración en vivo (guion de 5 minutos)

Antes de empezar: Wokwi corriendo, app abierta, topic base igual en ambos, micrófono permitido.

1. **(30 s) Contexto.** Qué es el invernadero, qué se simula, qué dos ambientes hay.
2. **(60 s) Sensores → app.** Mueve el potenciómetro de suelo hasta quedar por debajo del umbral: en *Monitoreo* aparece el estado en rojo y en modo automático se enciende el LED azul de la bomba.
3. **(60 s) App → Wokwi con botones.** En *Control* apaga la bomba y mueve el slider de la ventana: el servo gira en Wokwi y la app muestra la confirmación.
4. **(60 s) Voz.** Di «abre la ventana al cincuenta por ciento» y «enciende la lámpara». Muestra la transcripción, el JSON enviado y el LED amarillo.
5. **(60 s) Imagen.** Sube una foto de una hoja verde y otra amarilla; muestra el índice de salud y cómo la recomendación cambia según el sensor de suelo.
6. **(30 s) Cierre.** Muestra la bitácora, el repositorio y las pruebas pasando.

**Plan B:** si falla Wokwi o el internet, ejecuta `python tools/simulador_esp32.py --base <tu_id>`: la app se comporta igual.

## Preguntas probables (C2 – dominio técnico)

- **¿Por qué MQTT y no HTTP?** Publicación/suscripción, bajo consumo, mensajes pequeños, comunicación en ambos sentidos sin sondeo.
- **¿Qué hace el Last Will?** Si el ESP32 se desconecta sin avisar, el broker publica `offline` en `/estado`, y la app lo muestra.
- **¿Por qué la histéresis?** Evita que la bomba se encienda y apague continuamente cuando el valor oscila alrededor del umbral.
- **¿Cómo evitas que Streamlit abra un cliente MQTT nuevo en cada interacción?** Con `st.cache_resource`: el cliente vive en un hilo propio y las páginas leen una copia del estado protegida con un lock.
- **¿Cómo se actualiza la pantalla sin recargar?** Con `st.fragment(run_every=2)`, que re-ejecuta solo el panel.
- **¿Cómo funciona la voz?** `st.audio_input` entrega un WAV, el servicio web de SpeechRecognition lo transcribe y `core/comandos.py` lo convierte en JSON.
- **¿Cómo analizas la imagen?** Convierto a HSV, me quedo con píxeles saturados y mido la proporción de verde frente a amarillo/marrón. Es una heurística, no un diagnóstico agronómico.
- **¿Qué pasa si se pierde la conexión?** El cliente reconecta solo, la app muestra «sin conexión» y el ESP32 reconecta en su bucle.
- **¿Qué mejorarías?** Broker propio con TLS y autenticación, base de datos histórica, modelo de visión entrenado, hardware real.
- **¿Qué limitación de seguridad tiene?** El broker público no tiene autenticación: cualquiera que conozca el topic podría publicar comandos.

## Manejo del tiempo (C3)
Ensaya con cronómetro. Reparte 5 min de demo + el resto para preguntas, y no leas diapositivas: apóyate en el guion de arriba.
