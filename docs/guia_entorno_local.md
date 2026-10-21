# Guía: poner el proyecto a correr en tu computador (Windows)

Pasos para clonar el repo y correr dbt con DuckDB. Todo es local y gratuito. Está escrita a partir de lo que hicimos en la práctica, incluidos los errores que aparecieron.

## 1. Programas necesarios

- **Git**: https://git-scm.com/download/win (opciones por defecto). Comprueba con `git --version`.
- **Python 3.12**: https://www.python.org/downloads/ (instalador de Windows de 64 bits, versión 3.12.x). En la primera pantalla marca **Add python.exe to PATH**.
  - No uses una versión recién salida (por ejemplo 3.15). Librerías como `pyyaml` y `duckdb` aún no tienen paquetes listos para ella, pip intenta compilarlas y pide Visual C++.

Después de instalar, cierra por completo VS Code y la terminal y ábrelos de nuevo. Una terminal abierta no ve los programas instalados después.

Si `python` no se reconoce, prueba `py --version`. Si abre la Microsoft Store, desactiva los alias en Configuración > Aplicaciones > Configuración avanzada de aplicaciones > Alias de ejecución de aplicaciones.

## 2. Clonar el repo

```powershell
cd $HOME\Documents
git clone https://github.com/luisahernandez01/TFM.git
cd TFM
git config --global user.name "Tu nombre"
git config --global user.email "tu-correo"
```

Al clonar se abre el navegador para iniciar sesión en GitHub. No escribas la contraseña en la terminal. Para traer cambios nuevos: `git pull origin main`.

## 3. Entorno virtual e instalación de dbt

```powershell
cd C:\Users\<tu usuario>\Documents\TFM
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip install dbt-duckdb
.\.venv\Scripts\python.exe -m dbt --version
```

Notas:
- El `.\` al inicio es necesario en PowerShell para ejecutar un programa de una carpeta relativa. Sin él aparece "The module '.venv' could not be loaded".
- Se llama directamente a `.venv\Scripts\python.exe`, así no hace falta activar el entorno.
- Si prefieres activarlo (`.\.venv\Scripts\Activate.ps1`) y da "running scripts is disabled", ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Crea el entorno dentro de la carpeta `TFM`. Si queda en otra carpeta, bórralo con `Remove-Item -Recurse -Force <ruta>\.venv`.

## 4. Los datos

Los parquet de silver se exportan desde Databricks y no están en el repo (carpeta `data/`, ignorada por git).

1. En Databricks: Catalog > `bronce_vol` > `exportar` > `silver_objetivo` y `silver_subjetivo`.
2. Spark escribe **carpetas** con el nombre del archivo. Dentro, el único archivo útil es `part-00000-...parquet`. Los `_committed`, `_started` y `_SUCCESS` se ignoran.
3. Copia cada `part-*.parquet` a `TFM\data\` con el nombre que espera dbt:

```powershell
mkdir data
Copy-Item "$HOME\Downloads\data\silver_objetivo.parquet\part-*.parquet"  "$HOME\Documents\TFM\data\silver_objetivo.parquet"
Copy-Item "$HOME\Downloads\data\silver_subjetivo.parquet\part-*.parquet" "$HOME\Documents\TFM\data\silver_subjetivo.parquet"
dir data
```

`dir` debe mostrar dos archivos (no carpetas).

## 5. Correr dbt

```powershell
cd dbt
..\.venv\Scripts\python.exe -m dbt build --profiles-dir .
```

Debe terminar con todos los modelos creados y las pruebas en PASS. El resultado queda en `data\tfm.duckdb` (tablas `gold_sesiones` y `gold_carga_rolling`).

Para probar sin datos reales:

```powershell
cd ..
.\.venv\Scripts\python.exe scripts\datos_sinteticos.py data_test
cd dbt
..\.venv\Scripts\python.exe -m dbt build --profiles-dir . --vars "{data_dir: ../data_test}"
```

## 6. Subir cambios

```powershell
git add .
git commit -m "descripción corta"
git push origin main
```

No se suben `.venv`, `data`, `.duckdb`, `.parquet` ni `.zip` (ya están en `.gitignore`).

## Errores que ya aparecieron

| Mensaje | Causa | Solución |
|---|---|---|
| `git` / `python` no se reconoce | Programa no instalado o terminal abierta antes de instalarlo | Instalar, cerrar VS Code por completo y reabrir |
| `winget` no se reconoce | No viene en todos los equipos | Instalar a mano desde las páginas oficiales |
| `The module '.venv' could not be loaded` | Falta el `.\` o el entorno no existe en esa carpeta | Usar `.\.venv\...` y comprobar con `dir -Force` |
| `running scripts is disabled` | Política de ejecución de PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `Microsoft Visual C++ 14.0 or greater is required` / `Failed building wheel for pyyaml duckdb` | Python demasiado nuevo (3.15) | Usar Python 3.12 y recrear `.venv` |
