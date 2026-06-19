# Optimización de Asignación de Cirugías a Quirófanos

Este proyecto implementa un modelo de programación lineal entera mixta (MIP) para optimizar la asignación y secuenciación de cirugías en los quirófanos del hospital. El sistema busca maximizar el valor de prioridad total de las cirugías realizadas, respetando las restricciones físicas, de recursos humanos y de secuenciación específicas del hospital (como la restricción para cirugías contaminadas).

---

## Modelo de Optimización

El modelo está diseñado para programar un conjunto de cirugías dentro de un horizonte temporal dividido en bloques de tiempo discretos, distribuyéndolas en los quirófanos disponibles.

### 1. Parámetros del Modelo

Los parámetros son los valores de entrada conocidos que configuran el problema:

* **Cirugías**:
  * **Identificador de Cirugía**: Identificador único de cada cirugía a programar.
  * **Nombre**: Nombre descriptivo de la operación.
  * **Bloques de Operación**: Duración en bloques de tiempo que requiere la cirugía en sí.
  * **Bloques de Limpieza**: Tiempo necesario en bloques de tiempo para sanitizar el quirófano inmediatamente después de la cirugía.
  * **Duración Total**: Suma de los bloques de operación y de los bloques de limpieza para cada cirugía.
  * **Es Contaminada**: Indicador binario que señala si el paciente posee una condición infecciosa (como bacterias multirresistentes).
  * **Prioridad**: Valor numérico que califica la urgencia o importancia de realizar la cirugía.
  * **Especialidad Requerida**: Especialidad médica que debe poseer el cirujano asignado a la cirugía.

* **Recursos Humanos y Físicos**:
  * **Quirófanos**: Número total de salas de operaciones disponibles.
  * **Bloques de Tiempo**: Cantidad total de bloques de tiempo en la jornada laboral (por ejemplo, 24 bloques).
  * **Cirujanos**: Lista de cirujanos con sus especialidades correspondientes.
  * **Personal de Soporte**:
    * Anestesistas disponibles en cada bloque de tiempo.
    * Personal circulante disponible en cada bloque de tiempo.
    * Instrumentistas disponibles en cada bloque de tiempo.
  * **Recursos Físicos Adicionales**:
    * Camas de preanestesia disponibles en cada bloque de tiempo.

* **Habilitaciones y Requerimientos**:
  * **Habilitación de Cirujanos**: Matriz que determina si un cirujano tiene la especialidad correcta para realizar una determinada cirugía.
  * **Requerimientos de Soporte**:
    * Cada cirugía requiere 1 anestesista y 1 cama de preanestesia durante su ejecución.
    * Las cirugías contaminadas requieren 2 personas de personal circulante (en lugar de 1) debido a los protocolos de aislamiento.
    * Las cirugías con prioridad alta (mayor o igual a 5) requieren 2 instrumentistas (en lugar de 1).

---

### 2. Variables de Decisión

Las variables representan las decisiones que el solucionador (solver) debe tomar:

* **Asignación de Inicio**: Variable binaria que toma el valor de 1 si una cirugía específica comienza a ejecutarse en un quirófano determinado al inicio de un bloque de tiempo específico, y 0 en caso contrario.
* **Asignación de Cirujano**: Variable binaria que toma el valor de 1 si un cirujano calificado es asignado a una cirugía específica, y 0 en caso contrario.
* **Cirugía Activa en Bloque**: Variable binaria auxiliar que indica si una cirugía está en fase de operación activa durante un bloque de tiempo específico (excluyendo el periodo de limpieza).
* **Orden de Precedencia**: Variable binaria utilizada para decidir el orden secuencial cuando dos cirugías diferentes comparten el mismo cirujano. Evita que las cirugías se solapen en el tiempo al definir cuál se realiza primero.
* **Variables Auxiliares de Tiempo**:
  * **Bloque de Inicio**: El bloque de tiempo en el que comienza la cirugía.
  * **Estado de Programación**: Variable binaria que indica si la cirugía fue finalmente programada en la jornada o si quedó sin asignar.
  * **Bloque de Fin Total**: El bloque de tiempo final que abarca tanto la operación como la limpieza de la cirugía.

---

### 3. Función Objetivo

El objetivo del modelo es:

* **Maximizar la prioridad total de las cirugías programadas**: Se calcula sumando la prioridad de cada cirugía que ha sido efectivamente asignada a un quirófano en un bloque de tiempo. Las cirugías no programadas no aportan al valor de la función objetivo.

---

### 4. Restricciones del Modelo

El modelo de optimización debe satisfacer estrictamente las siguientes reglas para garantizar la viabilidad práctica de la agenda:

* **Unicidad de Programación**: Cada cirugía puede programarse como máximo una vez en la jornada.
* **No Superposición en Quirófanos**: Dos cirugías no pueden ocupar el mismo quirófano al mismo tiempo. El periodo de ocupación de una cirugía abarca tanto el tiempo de operación como su periodo posterior de limpieza. Ninguna cirugía nueva puede iniciar en un quirófano hasta que la cirugía previa y su respectiva limpieza hayan concluido.
* **Secuenciación de Cirugías Contaminadas**: Si una cirugía contaminada y una cirugía no contaminada se programan en el mismo quirófano, la cirugía contaminada debe iniciar estrictamente después de que la cirugía no contaminada y su limpieza hayan finalizado. Esto asegura que los procedimientos contaminados sean siempre los últimos en cada sala de operaciones para prevenir infecciones cruzadas.
* **Asignación de Cirujanos**: Toda cirugía programada debe tener exactamente un cirujano asignado que posea la especialidad médica requerida. Si una cirugía no se programa, no se le asigna ningún cirujano.
* **Disponibilidad de Cirujanos (No Solape)**: Un cirujano no puede realizar dos operaciones de forma simultánea. Si dos cirugías comparten el mismo cirujano, sus intervalos de ejecución no pueden solaparse. La precedencia temporal de estas cirugías es controlada mediante la variable de precedencia.
* **Capacidad de Personal de Soporte y Camas**: Para cada bloque de tiempo de la jornada, la suma de los recursos humanos y físicos (anestesistas, personal circulante, instrumentistas y camas de preanestesia) requeridos por todas las cirugías activas en ese bloque no puede superar la capacidad máxima disponible en el hospital. Cabe destacar que la limpieza no consume estos recursos de soporte directo de la operación, por lo que solo se contabilizan durante los bloques de operación activos.

---

## Cómo Ejecutar la Aplicación

Para probar y visualizar el modelo de optimización mediante la interfaz gráfica interactiva, siga estos pasos:

### Prerrequisitos

Asegúrese de tener instalado Python 3 en su sistema. Se recomienda utilizar el entorno virtual provisto en el repositorio.

### Instrucciones de Ejecución

1. **Abrir una terminal** en el directorio raíz del proyecto:
   ```bash
   cd /home/iaago/Documents/GitHub/ObligatorioIO
   ```

2. **Activar el entorno virtual** de Python:
   ```bash
   source venv/bin/activate
   ```

3. **Iniciar la aplicación de Streamlit**:
   ```bash
   streamlit run app.py
   ```
   O de forma directa utilizando el intérprete de comandos del entorno virtual:
   ```bash
   venv/bin/python -m streamlit run app.py
   ```

4. **Acceder a la interfaz**:
   Una vez que el comando esté en ejecución, se abrirá automáticamente una pestaña en su navegador web. Si no ocurre, puede ingresar manualmente a la dirección que se muestre en la terminal (usualmente `http://localhost:8501`).
