"""
Utilidades de visión artificial para el control de asistencia.

Se usa:
- Haar Cascade (incluido en OpenCV) para DETECTAR rostros en una imagen.
- LBPH (Local Binary Patterns Histograms, módulo cv2.face) para RECONOCER
  a qué estudiante pertenece un rostro detectado.

No se descarga ningún modelo externo: todo viene incluido en
opencv-contrib-python, por lo que el proyecto funciona sin conexión
a internet una vez instaladas las dependencias.
"""
import base64
import json
import re

import cv2
import numpy as np
from django.conf import settings

MODEL_PATH = settings.FACE_DATA_DIR / "trainer.yml"
LABELS_PATH = settings.FACE_DATA_DIR / "labels.json"
FOTOS_POR_ESTUDIANTE = 15
TAMANO_ROSTRO = (200, 200)

_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Caché simple en memoria para no releer el modelo entrenado en cada request.
_recognizer_cache = {"mtime": None, "recognizer": None, "labels": None}


class ImagenInvalidaError(Exception):
    pass


def decodificar_imagen_base64(data_url, max_bytes=3_000_000):
    """Convierte una cadena 'data:image/jpeg;base64,...' en una imagen OpenCV (BGR)."""
    if not data_url or "," not in data_url:
        raise ImagenInvalidaError("Formato de imagen inválido.")
    header, encoded = data_url.split(",", 1)
    if not re.match(r"^data:image/(jpeg|jpg|png);base64$", header):
        raise ImagenInvalidaError("Tipo de imagen no permitido.")
    if len(encoded) > max_bytes:
        raise ImagenInvalidaError("Imagen demasiado grande.")
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ImagenInvalidaError("No se pudo decodificar la imagen.") from exc
    arr = np.frombuffer(raw, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ImagenInvalidaError("Archivo de imagen corrupto.")
    return img


def detectar_rostros(img_bgr):
    """Devuelve lista de rostros (x, y, w, h) en escala de grises."""
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    rostros = _face_cascade.detectMultiScale(
        gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
    )
    return gray, rostros


def recortar_rostro_principal(img_bgr):
    """Para registro: exige exactamente un rostro visible y lo recorta normalizado."""
    gray, rostros = detectar_rostros(img_bgr)
    if len(rostros) == 0:
        return None, "No se detectó ningún rostro. Acércate a la cámara."
    if len(rostros) > 1:
        return None, "Se detectó más de un rostro. Asegúrate de estar solo frente a la cámara."
    (x, y, w, h) = rostros[0]
    rostro = cv2.resize(gray[y : y + h, x : x + w], TAMANO_ROSTRO)
    return rostro, None


def guardar_muestra_rostro(codigo_estudiante, rostro_gris, indice):
    carpeta = settings.FACE_DATA_DIR / "muestras" / codigo_estudiante
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{indice}.png"
    cv2.imwrite(str(ruta), rostro_gris)
    return len(list(carpeta.glob("*.png")))


def contar_muestras(codigo_estudiante):
    carpeta = settings.FACE_DATA_DIR / "muestras" / codigo_estudiante
    if not carpeta.exists():
        return 0
    return len(list(carpeta.glob("*.png")))


def entrenar_modelo():
    """Reentrena el reconocedor LBPH con TODAS las muestras guardadas."""
    muestras_dir = settings.FACE_DATA_DIR / "muestras"
    imagenes, etiquetas, mapa_labels = [], [], {}

    if not muestras_dir.exists():
        raise ValueError("No hay muestras registradas todavía.")

    siguiente_label = 0
    for carpeta_estudiante in sorted(muestras_dir.iterdir()):
        if not carpeta_estudiante.is_dir():
            continue
        codigo = carpeta_estudiante.name
        fotos = list(carpeta_estudiante.glob("*.png"))
        if not fotos:
            continue
        mapa_labels[str(siguiente_label)] = codigo
        for foto in fotos:
            img = cv2.imread(str(foto), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            imagenes.append(img)
            etiquetas.append(siguiente_label)
        siguiente_label += 1

    if not imagenes:
        raise ValueError("No hay muestras válidas para entrenar.")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(imagenes, np.array(etiquetas))
    recognizer.save(str(MODEL_PATH))
    LABELS_PATH.write_text(json.dumps(mapa_labels), encoding="utf-8")

    # invalidar caché
    _recognizer_cache["mtime"] = None
    return len(mapa_labels), len(imagenes)


def _cargar_recognizer():
    if not MODEL_PATH.exists() or not LABELS_PATH.exists():
        return None, None
    mtime = MODEL_PATH.stat().st_mtime
    if _recognizer_cache["mtime"] == mtime:
        return _recognizer_cache["recognizer"], _recognizer_cache["labels"]

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(MODEL_PATH))
    labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))

    _recognizer_cache.update({"mtime": mtime, "recognizer": recognizer, "labels": labels})
    return recognizer, labels


def reconocer_rostros(img_bgr):
    """
    Detecta todos los rostros en la imagen y trata de reconocer cada uno.
    Devuelve una lista de dicts: {bbox, codigo|None, confianza}
    """
    recognizer, labels = _cargar_recognizer()
    gray, rostros = detectar_rostros(img_bgr)

    resultados = []
    for (x, y, w, h) in rostros:
        info = {"bbox": [int(x), int(y), int(w), int(h)], "cedula": None, "confianza": None}
        if recognizer is not None:
            rostro = cv2.resize(gray[y : y + h, x : x + w], TAMANO_ROSTRO)
            label_id, distancia = recognizer.predict(rostro)
            info["confianza"] = round(float(distancia), 1)
            if distancia <= settings.LBPH_CONFIDENCE_THRESHOLD:
                info["cedula"] = labels.get(str(label_id))
        resultados.append(info)
    return resultados
