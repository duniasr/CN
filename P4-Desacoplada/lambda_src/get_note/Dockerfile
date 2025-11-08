# Usar la imagen base de Lambda
FROM public.ecr.aws/lambda/python:3.11

# Establecer el directorio de trabajo
WORKDIR /var/task

# --- RUTAS CORREGIDAS ---
# Copia el requirements.txt DESDE la subcarpeta create_note
COPY lambda_src/get_note/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el CÓDIGO COMÚN (relativo a lambda_src)
COPY lambda_src/app/db/ /var/task/db
COPY lambda_src/app/models/ /var/task/models

# Copia el main.py DESDE la subcarpeta create_note
COPY lambda_src/get_note/main.py .
# --- FIN DE CORRECCIONES ---

# Apuntar al handler
CMD [ "main.handler" ]