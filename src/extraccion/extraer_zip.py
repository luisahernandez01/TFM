# Databricks notebook source
# Extrae un mes de un zip de bronze al volumen. Spark no puede leer dentro de un zip,
# por eso se extrae con zipfile y después Spark lee los parquet.
import zipfile, os, shutil

base = "/Volumes/soccermonetl/tfm/bronce_vol"
ZIP = "objective-TeamB-2020.zip"
MES = "2020-06"   # formato AAAA-MM

with zipfile.ZipFile(f"{base}/{ZIP}") as z:
    miembros = [m for m in z.infolist()
                if m.filename.startswith(f"{MES[:4]}/{MES}/") and not m.is_dir()]
    for m in miembros:
        destino = f"{base}/extraido/{m.filename}"
        if os.path.exists(destino) and os.path.getsize(destino) == m.file_size:
            continue
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with z.open(m) as src, open(destino, "wb") as dst:
            shutil.copyfileobj(src, dst, 8 * 1024 * 1024)
print(len(miembros), "archivos del mes", MES)
