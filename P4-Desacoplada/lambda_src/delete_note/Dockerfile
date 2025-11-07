# Usar la imagen base de Lambda
FROM public.ecr.aws/lambda/python:3.11

# Establecer el directorio de trabajo
WORKDIR ${LAMBDA_TASK_ROOT}

# --- RUTAS CORREGIDAS ---
# Copia el requirements.txt DESDE la subcarpeta create_note
COPY lambda_src/delete_note/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el CÓDIGO COMÚN (relativo a lambda_src)
COPY lambda_src/common/ ./common/

# Copia el main.py DESDE la subcarpeta create_note
COPY lambda_src/create_note/main.py .
# --- FIN DE CORRECCIONES ---

# Apuntar al handler
CMD [ "main.handler" ]