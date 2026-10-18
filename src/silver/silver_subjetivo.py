# Databricks notebook source
# Silver subjetivo: CSV anchos (fecha x jugadora) pasados a formato largo.
# Antes hay que extraer subjective.zip a {base}/extraido/subjective/ (solo .csv y .json).
import pandas as pd, glob, os

base = "/Volumes/soccermonetl/tfm/bronce_vol"
rutas = glob.glob(f"{base}/extraido/subjective/**/*.csv", recursive=True)
print(len(rutas), "csv encontrados")

largos, saltados = [], []
for r in rutas:
    p = pd.read_csv(r)
    if p.columns[0] == "player_name":   # formato largo: se trata aparte
        saltados.append(os.path.basename(r))
        continue
    medida = os.path.basename(r).replace(".csv", "")
    l = p.melt(id_vars=p.columns[0], var_name="jugadora", value_name="valor")
    l["fecha"] = pd.to_datetime(l.iloc[:, 0], format="%d.%m.%Y")
    l["medida"] = medida
    largos.append(l[["jugadora", "fecha", "medida", "valor"]])

sub = pd.concat(largos).dropna(subset=["valor"])
spark.createDataFrame(sub).write.format("delta").mode("overwrite").save(f"{base}/silver/subjetivo_ancho")
print("saltados (formato largo):", saltados)
print(sub.groupby("medida").size())
