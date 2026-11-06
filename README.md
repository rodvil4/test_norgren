# Norgren

Proyecto Django con la aplicacion `orders`.

En Windows, usando el entorno virtual existente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Abre http://127.0.0.1:8000/ para administrar órdenes, clientes y productos.
La lista de órdenes muestra cada encabezado seguido de sus detalles.
Los detalles se capturan y editan dentro de la orden; se necesita al menos una
línea para guardar. La pantalla numera automáticamente las líneas de cada orden
desde 1 y las renumera al eliminar una. Las migraciones cargan los tres clientes y cuatro productos de
ejemplo. El proyecto usa `db.sqlite3`; la base existente `DatosExamenCopia.db`
permanece separada y no se modifica con las migraciones.

La cantidad admite cuatro decimales y los importes dos. En la pantalla de la
orden, el precio unitario se toma del catálogo de productos; al editar una línea
se conserva el precio histórico si el producto no cambia. Al cambiar de
producto se usa su precio actual. El total de cada línea es cantidad por precio unitario, redondeado a dos
decimales (mitades alejadas de cero); el importe total suma las líneas no
eliminadas. El servidor recalcula ambos importes al guardar. Al eliminar una orden también
se eliminan sus detalles. Los clientes o productos con referencias no se
pueden eliminar. Estos formularios no tienen autenticación y están destinados
al uso local de desarrollo.

La configuracion predeterminada es solo para desarrollo local. Antes de
desplegar, configura `DJANGO_SECRET_KEY` con una clave secreta y revisa la
configuracion de seguridad de Django, incluidos `DEBUG` y `ALLOWED_HOSTS`.

Los archivos locales de datos, bases de datos y documentos de examen no se
incluyen en el repositorio.
